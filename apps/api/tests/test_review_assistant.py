from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_data_assisted_review_handles_empty_and_measured_content() -> None:
    suffix = uuid4().hex[:8]
    content_id: str | None = None
    account_id: str | None = None
    publication_id: str | None = None

    try:
        content_response = client.post(
            "/api/v1/contents",
            json={
                "title": f"提升收藏率的 3 个方法 {suffix}",
                "content_type": "video",
                "status": "review",
            },
        )
        assert content_response.status_code == 201, content_response.text
        content_id = content_response.json()["id"]

        empty_response = client.get(
            f"/api/v1/reviews/content/{content_id}/suggestions"
        )
        assert empty_response.status_code == 200, empty_response.text
        assert empty_response.json()["metrics"]["publications"] == 0
        assert "数据" in empty_response.json()["next_action"]

        platforms_response = client.get("/api/v1/platforms")
        assert platforms_response.status_code == 200, platforms_response.text
        platform = platforms_response.json()[0]

        account_response = client.post(
            "/api/v1/platform-accounts",
            json={
                "platform_id": platform["id"],
                "name": f"Review assistant {suffix}",
                "handle": f"review-assistant-{suffix}",
            },
        )
        assert account_response.status_code == 201, account_response.text
        account_id = account_response.json()["id"]

        publication_response = client.post(
            "/api/v1/publications",
            json={
                "content_id": content_id,
                "platform_account_id": account_id,
                "title": f"提升收藏率的 3 个方法 {suffix}",
                "status": "published",
                "published_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert publication_response.status_code == 201, publication_response.text
        publication_id = publication_response.json()["id"]

        metric_response = client.post(
            f"/api/v1/analytics/publications/{publication_id}/metrics",
            json={
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "views": 2000,
                "likes": 120,
                "comments": 40,
                "favorites": 180,
                "shares": 30,
                "followers_gained": 25,
                "extra_metrics": {},
            },
        )
        assert metric_response.status_code == 201, metric_response.text

        measured_response = client.get(
            f"/api/v1/reviews/content/{content_id}/suggestions"
        )
        assert measured_response.status_code == 200, measured_response.text
        suggestion = measured_response.json()
        assert suggestion["metrics"]["publications"] == 1
        assert suggestion["metrics"]["views"] == 2000
        assert suggestion["metrics"]["favorite_rate"] == 9.0
        assert "数字型" in suggestion["title_patterns"]
        assert "清单型" in suggestion["title_patterns"]
        assert suggestion["learnings"]
        assert suggestion["next_action"]

    finally:
        if publication_id is not None:
            response = client.delete(f"/api/v1/publications/{publication_id}")
            assert response.status_code in {204, 404}, response.text
        if content_id is not None:
            response = client.delete(f"/api/v1/contents/{content_id}")
            assert response.status_code in {204, 404}, response.text
        if account_id is not None:
            response = client.delete(f"/api/v1/platform-accounts/{account_id}")
            assert response.status_code in {204, 404}, response.text
