from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_tag_performance_analytics_uses_latest_publication_snapshot() -> None:
    suffix = uuid4().hex[:8]
    tag_id: str | None = None
    content_id: str | None = None
    account_id: str | None = None
    publication_id: str | None = None

    try:
        tag_response = client.post(
            "/api/v1/tags",
            json={"name": f"tag-analytics-{suffix}"},
        )
        assert tag_response.status_code == 201, tag_response.text
        tag_id = tag_response.json()["id"]

        content_response = client.post(
            "/api/v1/contents",
            json={
                "title": f"Tag analytics content {suffix}",
                "content_type": "video",
                "status": "ready",
            },
        )
        assert content_response.status_code == 201, content_response.text
        content_id = content_response.json()["id"]

        tag_assignment_response = client.put(
            f"/api/v1/contents/{content_id}/tags",
            json={"tag_ids": [tag_id]},
        )
        assert tag_assignment_response.status_code == 200, tag_assignment_response.text

        platforms_response = client.get("/api/v1/platforms")
        assert platforms_response.status_code == 200, platforms_response.text
        bilibili = next(
            platform for platform in platforms_response.json() if platform["slug"] == "bilibili"
        )

        account_response = client.post(
            "/api/v1/platform-accounts",
            json={
                "platform_id": bilibili["id"],
                "name": f"Tag analytics account {suffix}",
                "handle": f"tag-analytics-{suffix}",
            },
        )
        assert account_response.status_code == 201, account_response.text
        account_id = account_response.json()["id"]

        publication_response = client.post(
            "/api/v1/publications",
            json={
                "content_id": content_id,
                "platform_account_id": account_id,
                "title": f"Tag analytics publication {suffix}",
                "status": "published",
                "published_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert publication_response.status_code == 201, publication_response.text
        publication_id = publication_response.json()["id"]

        first_snapshot_response = client.post(
            f"/api/v1/analytics/publications/{publication_id}/metrics",
            json={
                "captured_at": datetime(2026, 8, 14, 1, 0, tzinfo=timezone.utc).isoformat(),
                "views": 500,
                "likes": 30,
                "comments": 10,
                "favorites": 40,
                "shares": 5,
                "followers_gained": 4,
                "extra_metrics": {},
            },
        )
        assert first_snapshot_response.status_code == 201, first_snapshot_response.text

        latest_snapshot_response = client.post(
            f"/api/v1/analytics/publications/{publication_id}/metrics",
            json={
                "captured_at": datetime(2026, 8, 14, 2, 0, tzinfo=timezone.utc).isoformat(),
                "views": 1000,
                "likes": 80,
                "comments": 20,
                "favorites": 120,
                "shares": 30,
                "followers_gained": 10,
                "extra_metrics": {},
            },
        )
        assert latest_snapshot_response.status_code == 201, latest_snapshot_response.text

        analytics_response = client.get("/api/v1/analytics/tags")
        assert analytics_response.status_code == 200, analytics_response.text
        item = next(
            row for row in analytics_response.json() if row["tag_id"] == tag_id
        )

        assert item["tag_name"] == f"tag-analytics-{suffix}"
        assert item["contents"] == 1
        assert item["publications"] == 1
        assert item["views"] == 1000
        assert item["likes"] == 80
        assert item["comments"] == 20
        assert item["favorites"] == 120
        assert item["shares"] == 30
        assert item["followers_gained"] == 10
        assert item["avg_views"] == 1000.0
        assert item["engagement_rate"] == 25.0
        assert item["favorite_rate"] == 12.0
        assert item["follower_conversion_rate"] == 1.0
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
        if tag_id is not None:
            response = client.delete(f"/api/v1/tags/{tag_id}")
            assert response.status_code in {204, 404}, response.text
