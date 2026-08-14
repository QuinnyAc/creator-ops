from urllib.parse import parse_qs, urlparse

from app.services.bilibili import bilibili_video_id, build_authorize_url


def test_bilibili_video_id_from_standard_url() -> None:
    assert bilibili_video_id("https://www.bilibili.com/video/BV17B4y1s7R1/") == "BV17B4y1s7R1"


def test_bilibili_video_id_rejects_missing_bvid() -> None:
    assert bilibili_video_id("https://www.bilibili.com/") is None


def test_bilibili_authorize_url_contains_callback_and_state() -> None:
    callback = "https://example.com/api/v1/bilibili/oauth/callback"
    url = build_authorize_url("client123", callback, "signed-state")
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert parsed.netloc == "account.bilibili.com"
    assert params["client_id"] == ["client123"]
    assert params["gourl"] == [callback]
    assert params["state"] == ["signed-state"]
