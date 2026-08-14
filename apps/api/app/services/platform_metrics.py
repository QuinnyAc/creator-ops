from dataclasses import dataclass
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


class PlatformMetricsError(RuntimeError):
    pass


@dataclass(frozen=True)
class PlatformMetrics:
    views: int
    likes: int
    comments: int
    favorites: int
    shares: int
    extra_metrics: dict[str, int | float | str]


def youtube_video_id(url: str) -> str | None:
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return None

    host = parsed.netloc.lower().split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]

    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/", 1)[0]
        return video_id or None

    if host not in {"youtube.com", "m.youtube.com", "music.youtube.com"}:
        return None

    if parsed.path == "/watch":
        return parse_qs(parsed.query).get("v", [None])[0]

    for prefix in ("/shorts/", "/embed/", "/live/"):
        if parsed.path.startswith(prefix):
            video_id = parsed.path[len(prefix) :].split("/", 1)[0]
            return video_id or None

    return None


def fetch_youtube_metrics(url: str, api_key: str) -> PlatformMetrics:
    video_id = youtube_video_id(url)
    if not video_id:
        raise PlatformMetricsError("无法从该链接识别 YouTube 视频 ID。")
    if not api_key:
        raise PlatformMetricsError("YouTube 自动同步尚未配置 API Key。")

    query = urlencode(
        {
            "part": "statistics",
            "id": video_id,
            "key": api_key,
        }
    )
    request = Request(
        f"https://www.googleapis.com/youtube/v3/videos?{query}",
        headers={"User-Agent": "Quinny-Creator-Ops/1.0"},
    )

    try:
        with urlopen(request, timeout=12) as response:  # noqa: S310 - fixed Google API origin
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise PlatformMetricsError(f"YouTube API 请求失败（HTTP {exc.code}）：{detail[:240]}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise PlatformMetricsError(f"YouTube API 暂时无法访问：{exc}") from exc

    items = payload.get("items") or []
    if not items:
        raise PlatformMetricsError("YouTube 未返回该视频的数据，请检查链接或视频可见性。")

    statistics = items[0].get("statistics") or {}
    return PlatformMetrics(
        views=int(statistics.get("viewCount") or 0),
        likes=int(statistics.get("likeCount") or 0),
        comments=int(statistics.get("commentCount") or 0),
        # YouTube favoriteCount has been deprecated and is always zero.
        favorites=0,
        shares=0,
        extra_metrics={
            "source": "youtube_data_api",
            "video_id": video_id,
            "favorites_available": "false",
            "shares_available": "false",
        },
    )
