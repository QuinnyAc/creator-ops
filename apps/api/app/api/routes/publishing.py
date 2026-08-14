from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from jwt import InvalidTokenError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.core.config import settings
from app.db import get_db
from app.models import (
    Content,
    MetricSnapshot,
    Platform,
    PlatformAccount,
    PlatformAccountAuth,
    Publication,
)
from app.schemas import (
    MetricSnapshotRead,
    PlatformAccountCreate,
    PlatformAccountRead,
    PlatformAccountUpdate,
    PlatformRead,
    PublicationCreate,
    PublicationRead,
    PublicationUpdate,
)
from app.services.bilibili import (
    BilibiliApiError,
    build_authorize_url,
    exchange_authorization_code,
    fetch_video_metrics,
    refresh_access_token,
)
from app.services.credential_crypto import (
    CredentialCryptoError,
    decrypt_secret,
    encrypt_secret,
)

router = APIRouter(tags=["publishing"])
ACTIVE_PLATFORM_SLUGS = ("xiaohongshu", "bilibili")
BILIBILI_STATE_TTL_MINUTES = 15
BILIBILI_REFRESH_MARGIN_MINUTES = 5


def _get_owned_platform_account(
    db: Session,
    account_id: UUID,
    user_id: UUID,
) -> PlatformAccount:
    account = db.scalar(
        select(PlatformAccount).where(
            PlatformAccount.id == account_id,
            PlatformAccount.user_id == user_id,
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="平台账号不存在。")
    return account


def _get_account_platform(db: Session, account: PlatformAccount) -> Platform:
    platform = db.get(Platform, account.platform_id)
    if platform is None:
        raise HTTPException(status_code=404, detail="平台不存在。")
    return platform


def _require_bilibili_account(
    db: Session,
    account_id: UUID,
    user_id: UUID,
) -> tuple[PlatformAccount, Platform]:
    account = _get_owned_platform_account(db, account_id, user_id)
    platform = _get_account_platform(db, account)
    if platform.slug != "bilibili":
        raise HTTPException(status_code=400, detail="该账号不是哔哩哔哩账号。")
    return account, platform


def _build_bilibili_state(account_id: UUID, user_id: UUID) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "type": "bilibili_oauth",
            "account_id": str(account_id),
            "user_id": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=BILIBILI_STATE_TTL_MINUTES),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def _decode_bilibili_state(state_token: str) -> tuple[UUID, UUID]:
    try:
        payload = jwt.decode(
            state_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "bilibili_oauth":
            raise InvalidTokenError("Unexpected OAuth state type")
        return UUID(str(payload["account_id"])), UUID(str(payload["user_id"]))
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="B站授权状态无效或已过期，请重新连接。") from exc


def _get_account_auth(db: Session, account_id: UUID) -> PlatformAccountAuth | None:
    return db.scalar(
        select(PlatformAccountAuth).where(
            PlatformAccountAuth.platform_account_id == account_id,
            PlatformAccountAuth.provider == "bilibili",
        )
    )


def _store_bilibili_tokens(
    db: Session,
    account_id: UUID,
    *,
    access_token: str,
    refresh_token: str,
    expires_at: datetime | None,
    scopes: list[str],
) -> PlatformAccountAuth:
    auth = _get_account_auth(db, account_id)
    if auth is None:
        auth = PlatformAccountAuth(
            platform_account_id=account_id,
            provider="bilibili",
            access_token_encrypted=encrypt_secret(access_token),
            refresh_token_encrypted=encrypt_secret(refresh_token) if refresh_token else None,
            token_expires_at=expires_at,
            scopes=scopes,
        )
        db.add(auth)
    else:
        auth.access_token_encrypted = encrypt_secret(access_token)
        if refresh_token:
            auth.refresh_token_encrypted = encrypt_secret(refresh_token)
        auth.token_expires_at = expires_at
        auth.scopes = scopes or auth.scopes
    db.commit()
    db.refresh(auth)
    return auth


def _active_bilibili_access_token(
    db: Session,
    auth: PlatformAccountAuth,
) -> str:
    access_token = decrypt_secret(auth.access_token_encrypted)
    expires_at = auth.token_expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    if expires_at is None or expires_at > now + timedelta(minutes=BILIBILI_REFRESH_MARGIN_MINUTES):
        return access_token

    refresh_token = decrypt_secret(auth.refresh_token_encrypted)
    if not refresh_token:
        raise BilibiliApiError("B站授权已过期且没有可用的 refresh_token，请重新连接账号。")

    tokens = refresh_access_token(
        refresh_token,
        settings.bilibili_client_id,
        settings.bilibili_app_secret,
    )
    _store_bilibili_tokens(
        db,
        auth.platform_account_id,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token or refresh_token,
        expires_at=tokens.expires_at,
        scopes=tokens.scopes or auth.scopes,
    )
    return tokens.access_token


@router.get("/platforms", response_model=list[PlatformRead])
def list_platforms(db: Session = Depends(get_db)) -> list[Platform]:
    return list(
        db.scalars(
            select(Platform)
            .where(Platform.slug.in_(ACTIVE_PLATFORM_SLUGS))
            .order_by(Platform.name)
        )
    )


@router.get("/platform-accounts", response_model=list[PlatformAccountRead])
def list_platform_accounts(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[PlatformAccount]:
    return list(
        db.scalars(
            select(PlatformAccount)
            .join(Platform, Platform.id == PlatformAccount.platform_id)
            .where(
                PlatformAccount.user_id == user_id,
                Platform.slug.in_(ACTIVE_PLATFORM_SLUGS),
            )
            .order_by(PlatformAccount.name)
        )
    )


@router.post(
    "/platform-accounts",
    response_model=PlatformAccountRead,
    status_code=status.HTTP_201_CREATED,
)
def create_platform_account(
    payload: PlatformAccountCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> PlatformAccount:
    platform = db.get(Platform, payload.platform_id)
    if platform is None or platform.slug not in ACTIVE_PLATFORM_SLUGS:
        raise HTTPException(status_code=400, detail="当前仅支持小红书和哔哩哔哩平台。")
    account = PlatformAccount(user_id=user_id, **payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.patch("/platform-accounts/{account_id}", response_model=PlatformAccountRead)
def update_platform_account(
    account_id: UUID,
    payload: PlatformAccountUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> PlatformAccount:
    account = _get_owned_platform_account(db, account_id, user_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


@router.get("/platform-accounts/{account_id}/bilibili/status")
def bilibili_connection_status(
    account_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, object]:
    account, _ = _require_bilibili_account(db, account_id, user_id)
    auth = _get_account_auth(db, account.id)
    return {
        "configured": settings.bilibili_configured,
        "connected": auth is not None,
        "expires_at": auth.token_expires_at.isoformat() if auth and auth.token_expires_at else None,
        "scopes": auth.scopes if auth else [],
        "callback_url": settings.bilibili_callback_url,
    }


@router.get("/platform-accounts/{account_id}/bilibili/authorize-url")
def bilibili_authorize_url(
    account_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> dict[str, str]:
    account, _ = _require_bilibili_account(db, account_id, user_id)
    if not settings.bilibili_configured:
        raise HTTPException(
            status_code=422,
            detail="B站 API 凭据尚未配置。请先配置 BILIBILI_CLIENT_ID 和 BILIBILI_APP_SECRET。",
        )
    state_token = _build_bilibili_state(account.id, user_id)
    try:
        url = build_authorize_url(
            settings.bilibili_client_id,
            settings.bilibili_callback_url,
            state_token,
        )
    except BilibiliApiError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"url": url, "callback_url": settings.bilibili_callback_url}


@router.get("/bilibili/oauth/callback", include_in_schema=False)
def bilibili_oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    try:
        account_id, user_id = _decode_bilibili_state(state)
        account, _ = _require_bilibili_account(db, account_id, user_id)
        if not settings.bilibili_configured:
            raise BilibiliApiError("B站 API 凭据尚未配置。")
        tokens = exchange_authorization_code(
            code,
            settings.bilibili_client_id,
            settings.bilibili_app_secret,
        )
        _store_bilibili_tokens(
            db,
            account.id,
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_at=tokens.expires_at,
            scopes=tokens.scopes,
        )
    except (HTTPException, BilibiliApiError, CredentialCryptoError):
        return RedirectResponse(
            url=f"{settings.normalized_public_web_url}/publishing?bilibili=error",
            status_code=status.HTTP_302_FOUND,
        )

    return RedirectResponse(
        url=f"{settings.normalized_public_web_url}/publishing?bilibili=connected",
        status_code=status.HTTP_302_FOUND,
    )


@router.delete("/platform-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    account = _get_owned_platform_account(db, account_id, user_id)
    publication_count = int(
        db.scalar(
            select(func.count(Publication.id)).where(Publication.platform_account_id == account.id)
        )
        or 0
    )
    if publication_count:
        raise HTTPException(
            status_code=409,
            detail=f"这个账号还有 {publication_count} 条视频记录。请先删除这些视频，再删除账号。",
        )
    db.delete(account)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_owned_publication(
    db: Session,
    publication_id: UUID,
    user_id: UUID,
) -> Publication:
    publication = db.scalar(
        select(Publication)
        .join(Content, Content.id == Publication.content_id)
        .where(
            Publication.id == publication_id,
            Content.user_id == user_id,
        )
    )
    if publication is None:
        raise HTTPException(status_code=404, detail="Publication not found.")
    return publication


@router.get("/publications", response_model=list[PublicationRead])
def list_publications(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[Publication]:
    return list(
        db.scalars(
            select(Publication)
            .join(Content, Content.id == Publication.content_id)
            .where(Content.user_id == user_id)
            .order_by(Publication.scheduled_at.asc().nullslast(), Publication.created_at.desc())
        )
    )


@router.get("/publication-metrics/latest", response_model=list[MetricSnapshotRead])
def list_latest_publication_metrics(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[MetricSnapshot]:
    latest_times = (
        select(
            MetricSnapshot.publication_id,
            func.max(MetricSnapshot.captured_at).label("captured_at"),
        )
        .group_by(MetricSnapshot.publication_id)
        .subquery()
    )
    return list(
        db.scalars(
            select(MetricSnapshot)
            .join(
                latest_times,
                (MetricSnapshot.publication_id == latest_times.c.publication_id)
                & (MetricSnapshot.captured_at == latest_times.c.captured_at),
            )
            .join(Publication, Publication.id == MetricSnapshot.publication_id)
            .join(Content, Content.id == Publication.content_id)
            .where(Content.user_id == user_id)
            .order_by(MetricSnapshot.captured_at.desc())
        )
    )


@router.post(
    "/publications",
    response_model=PublicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_publication(
    payload: PublicationCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Publication:
    content = db.scalar(
        select(Content).where(Content.id == payload.content_id, Content.user_id == user_id)
    )
    account = db.scalar(
        select(PlatformAccount)
        .join(Platform, Platform.id == PlatformAccount.platform_id)
        .where(
            PlatformAccount.id == payload.platform_account_id,
            PlatformAccount.user_id == user_id,
            Platform.slug.in_(ACTIVE_PLATFORM_SLUGS),
        )
    )
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found.")
    if account is None:
        raise HTTPException(status_code=404, detail="仅可使用小红书或哔哩哔哩账号创建发布记录。")
    publication = Publication(**payload.model_dump())
    db.add(publication)
    db.commit()
    db.refresh(publication)
    return publication


@router.get("/publications/{publication_id}", response_model=PublicationRead)
def get_publication(
    publication_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Publication:
    return _get_owned_publication(db, publication_id, user_id)


@router.patch("/publications/{publication_id}", response_model=PublicationRead)
def update_publication(
    publication_id: UUID,
    payload: PublicationUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Publication:
    publication = _get_owned_publication(db, publication_id, user_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(publication, key, value)
    db.commit()
    db.refresh(publication)
    return publication


@router.post(
    "/publications/{publication_id}/sync-metrics",
    response_model=MetricSnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
def sync_publication_metrics(
    publication_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> MetricSnapshot:
    publication = _get_owned_publication(db, publication_id, user_id)
    if not publication.url:
        raise HTTPException(status_code=400, detail="请先填写已发布作品链接。")

    account = _get_owned_platform_account(db, publication.platform_account_id, user_id)
    platform = _get_account_platform(db, account)

    if platform.slug == "bilibili":
        if not settings.bilibili_configured:
            raise HTTPException(status_code=422, detail="B站 API 尚未配置应用凭据。")
        auth = _get_account_auth(db, account.id)
        if auth is None:
            raise HTTPException(status_code=422, detail="请先在发布管理中连接这个B站账号的 API 授权。")
        try:
            access_token = _active_bilibili_access_token(db, auth)
            metrics = fetch_video_metrics(
                publication.url,
                client_id=settings.bilibili_client_id,
                client_secret=settings.bilibili_app_secret,
                access_token=access_token,
            )
        except (BilibiliApiError, CredentialCryptoError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        snapshot = MetricSnapshot(
            publication_id=publication.id,
            captured_at=datetime.now(timezone.utc),
            views=metrics.views,
            likes=metrics.likes,
            comments=metrics.comments,
            favorites=metrics.favorites,
            shares=metrics.shares,
            followers_gained=0,
            extra_metrics=metrics.extra_metrics,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    if platform.slug == "xiaohongshu":
        raise HTTPException(
            status_code=422,
            detail="小红书当前未配置可用于普通创作者笔记数据的官方开放接口，请在数据详情页手动记录当前数据。",
        )

    raise HTTPException(status_code=422, detail="该平台已停用。")


@router.delete("/publications/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_publication(
    publication_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    publication = _get_owned_publication(db, publication_id, user_id)
    db.delete(publication)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
