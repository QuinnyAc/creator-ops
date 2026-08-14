from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content, MetricSnapshot, Platform, PlatformAccount, Publication
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

router = APIRouter(tags=["publishing"])
ACTIVE_PLATFORM_SLUGS = ("xiaohongshu", "bilibili")


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
    account = db.scalar(
        select(PlatformAccount).where(
            PlatformAccount.id == account_id,
            PlatformAccount.user_id == user_id,
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Platform account not found.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/platform-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    account = db.scalar(
        select(PlatformAccount).where(
            PlatformAccount.id == account_id,
            PlatformAccount.user_id == user_id,
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Platform account not found.")
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

    account = db.get(PlatformAccount, publication.platform_account_id)
    platform = db.get(Platform, account.platform_id) if account else None
    if account is None or account.user_id != user_id or platform is None:
        raise HTTPException(status_code=404, detail="发布平台账号不存在。")

    if platform.slug == "bilibili":
        detail = "哔哩哔哩自动同步需要开放平台授权；授权接通前请在数据详情页手动记录当前数据。"
    elif platform.slug == "xiaohongshu":
        detail = "小红书当前没有可直接按普通作品链接读取创作者数据的已配置官方接口；请先在数据详情页手动记录当前数据。"
    else:
        detail = "该平台已停用。"
    raise HTTPException(status_code=422, detail=detail)


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
