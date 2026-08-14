from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import re
import secrets
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BILIBILI_AUTHORIZE_URL = "https://account.bilibili.com/pc/account-pc/auth/oauth"
BILIBILI_TOKEN_URL = "https://api.bilibili.com/x/account-oauth2/v1/token"
BILIBILI_REFRESH_URL = "https://api.bilibili.com/x/account-oauth2/v1/refresh_token"
BILIBILI_API_ORIGIN = "https://member.bilibili.com"
BILIBILI_VIDEO_STAT_PATH = "/arcopen/fn/data/arc/stat"
BVID_RE = re.compile(r"(BV[0-9A-Za-z]{10})", re.IGNORECASE)


class BilibiliApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class BilibiliTokens:
    access_token: str
    refresh_token: str
    expires_at: datetime | None
    scopes: list[str]


@dataclass(frozen=True)
class BilibiliMetrics:
    views: int
    likes: int
    comments: int
    favorites: int
    shares: int
    extra_metrics: dict[str, int | float | str]


def build_authorize_url(client_id: str, callback_url: str, state: str) -> str:
    if not client_id:
        raise BilibiliApiError("B站 API 尚未配置 Client ID。")
    if not callback_url:
        raise BilibiliApiError("B站 API 尚未配置授权回调地址。")
    return f"{BILIBILI_AUTHORIZE_URL}?{urlencode({'client_id': client_id, 'gourl': callback_url, 'state': state})}"


def bilibili_video_id(url: str) -> str | None:
    match = BVID_RE.search(url or "")
    return match.group(1) if match else None


def _request_json(request: Request, *, label: str) -> dict:
    try:
        with urlopen(request, timeout=15) as response:  # noqa: S310 - fixed Bilibili origins
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise BilibiliApiError(f"{label}失败（HTTP {exc.code}）：{detail[:240]}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise BilibiliApiError(f"{label}暂时无法访问：{exc}") from exc

    if int(payload.get("code") or 0) != 0:
        message = payload.get("message") or "未知错误"
        raise BilibiliApiError(f"{label}失败：{message}（code={payload.get('code')}）")
    return payload


def _parse_expiry(value: int | str | None) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None

    now = datetime.now(timezone.utc)
    # Bilibili documents this field as an expiry time, while some OAuth systems
    # return a duration. Accept both forms safely.
    if numeric > int(now.timestamp()) + 3600:
        return datetime.fromtimestamp(numeric, tz=timezone.utc)
    if numeric > 0:
        return now + timedelta(seconds=numeric)
    return None


def _parse_tokens(payload: dict) -> BilibiliTokens:
    data = payload.get("data") or {}
    access_token = str(data.get("access_token") or "")
    if not access_token:
        raise BilibiliApiError("B站授权成功响应中没有 access_token。")
    return BilibiliTokens(
        access_token=access_token,
        refresh_token=str(data.get("refresh_token") or ""),
        expires_at=_parse_expiry(data.get("expires_in")),
        scopes=[str(value) for value in (data.get("scopes") or [])],
    )


def exchange_authorization_code(
    code: str,
    client_id: str,
    client_secret: str,
) -> BilibiliTokens:
    if not client_id or not client_secret:
        raise BilibiliApiError("B站 API 尚未配置 Client ID / App Secret。")
    query = urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": code,
        }
    )
    request = Request(
        f"{BILIBILI_TOKEN_URL}?{query}",
        data=b"",
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Quinny-Workspace/1.0",
        },
    )
    return _parse_tokens(_request_json(request, label="B站 OAuth 授权"))


def refresh_access_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> BilibiliTokens:
    if not refresh_token:
        raise BilibiliApiError("B站 refresh_token 不存在，请重新授权。")
    query = urlencode(
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
    )
    request = Request(
        f"{BILIBILI_REFRESH_URL}?{query}",
        data=b"",
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Quinny-Workspace/1.0",
        },
    )
    return _parse_tokens(_request_json(request, label="B站 Token 刷新"))


def _signed_headers(client_id: str, client_secret: str, access_token: str) -> dict[str, str]:
    if not client_id or not client_secret:
        raise BilibiliApiError("B站 API 尚未配置 Client ID / App Secret。")
    if not access_token:
        raise BilibiliApiError("该B站账号尚未完成授权。")

    signed = {
        "x-bili-accesskeyid": client_id,
        "x-bili-content-md5": hashlib.md5(b"").hexdigest(),  # noqa: S324 - required by Bilibili protocol
        "x-bili-signature-method": "HMAC-SHA256",
        "x-bili-signature-nonce": secrets.token_hex(16),
        "x-bili-signature-version": "2.0",
        "x-bili-timestamp": str(int(time.time())),
    }
    sign_text = "\n".join(f"{key}:{signed[key]}" for key in sorted(signed))
    authorization = hmac.new(
        client_secret.encode("utf-8"),
        sign_text.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Access-Token": access_token,
        "Authorization": authorization,
        "X-Bili-Accesskeyid": signed["x-bili-accesskeyid"],
        "X-Bili-Content-Md5": signed["x-bili-content-md5"],
        "X-Bili-Signature-Method": signed["x-bili-signature-method"],
        "X-Bili-Signature-Nonce": signed["x-bili-signature-nonce"],
        "X-Bili-Signature-Version": signed["x-bili-signature-version"],
        "X-Bili-Timestamp": signed["x-bili-timestamp"],
        "User-Agent": "Quinny-Workspace/1.0",
    }


def fetch_video_metrics(
    url: str,
    *,
    client_id: str,
    client_secret: str,
    access_token: str,
) -> BilibiliMetrics:
    resource_id = bilibili_video_id(url)
    if not resource_id:
        raise BilibiliApiError("无法从作品链接识别 BV 号，请粘贴完整的哔哩哔哩视频链接。")

    query = urlencode({"resource_id": resource_id})
    request = Request(
        f"{BILIBILI_API_ORIGIN}{BILIBILI_VIDEO_STAT_PATH}?{query}",
        method="GET",
        headers=_signed_headers(client_id, client_secret, access_token),
    )
    payload = _request_json(request, label="B站稿件数据同步")
    data = payload.get("data") or {}

    return BilibiliMetrics(
        views=int(data.get("view") or 0),
        likes=int(data.get("like") or 0),
        comments=int(data.get("reply") or 0),
        favorites=int(data.get("favorite") or 0),
        shares=int(data.get("share") or 0),
        extra_metrics={
            "source": "bilibili_open_platform",
            "resource_id": resource_id,
            "title": str(data.get("title") or ""),
            "coin": int(data.get("coin") or 0),
            "danmaku": int(data.get("danmaku") or 0),
            "platform_publish_time": int(data.get("ptime") or 0),
        },
    )
