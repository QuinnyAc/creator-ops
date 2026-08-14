from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_pillar_trend_compares_recent_and_previous_windows() -> None:
    suffix = uuid4().hex[:8]
    pillar_id: str | None = None
    account_id: str | None = None
    content_ids: list[str] = []
    publication_ids: list[str] = []

    try:
        pillar_response = client.post(
            "/api/v1/content-pillars",
            json={"name": f"Trend Pillar {suffix}", "description": "Trend test"},
        )
        assert pillar_response.status_code == 201, pillar_response.text
        pillar_id = pillar_response.json()["id"]

        platforms_response = client.get("/api/v1/platforms")
        assert platforms_response.status_code == 200, platforms_response.text
        platform = platforms_response.json()[0]

        account_response = client.post(
            "/api/v1/platform-accounts",
            json={
                "platform_id": platform["id"],
                "name": f"Trend account {suffix}",
                "handle": f"trend-{suffix}",
            },
        )
        assert account_response.status_code == 201, account_response.text
        account_id = account_response.json()["id"]

        now = datetime.now(timezone.utc)
        samples = [
            (now - timedelta(days=40), 1000, 50),
            (now - timedelta(days=5), 1500, 120),
        ]

        for index, (published_at, views, favorites) in enumerate(samples):
            content_response = client.post(
                "/api/v1/contents",
                json={
                    "title": f"Trend content {index} {suffix}",
                    "pillar_id": pillar_id,
                    "content_type": "video",
                    "status": "published",
                },
            )
            assert content_response.status_code == 201, content_response.text
            content_id = content_response.json()["id"]
            content_ids.append(content_id)

            publication_response = client.post(
                "/api/v1/publications",
                json={
                    "content_id": content_id,
                    "platform_account_id": account_id,
                    "status": "published",
                    "published_at": published_at.isoformat(),
                },
            )
            assert publication_response.status_code == 201, publication_response.text
            publication_id = publication_response.json()["id"]
            publication_ids.append(publication_id)

            metric_response = client.post(
                f"/api/v1/analytics/publications/{publication_id}/metrics",
                json={
                    "captured_at": (published_at + timedelta(days=1)).isoformat(),
                    "views": views,
                    "likes": 50,
                    "comments": 10,
                    "favorites": favorites,
                    "shares": 5,
                    "followers_gained": 10,
                    "extra_metrics": {},
                },
            )
            assert metric_response.status_code == 201, metric_response.text

        trends_response = client.get("/api/v1/analytics/pillar-trends?window_days=30")
        assert trends_response.status_code == 200, trends_response.text
        trend = next(
            item for item in trends_response.json() if item["pillar_id"] == pillar_id
        )
        assert trend["recent_publications"] == 1
        assert trend["previous_publications"] == 1
        assert trend["recent_avg_views"] == 1500.0
        assert trend["previous_avg_views"] == 1000.0
        assert trend["view_change_percent"] == 50.0
        assert trend["recent_favorite_rate"] == 8.0
        assert trend["previous_favorite_rate"] == 5.0
        assert trend["signal"] == "rising"

    finally:
        for publication_id in publication_ids:
            response = client.delete(f"/api/v1/publications/{publication_id}")
            assert response.status_code in {204, 404}, response.text
        for content_id in content_ids:
            response = client.delete(f"/api/v1/contents/{content_id}")
            assert response.status_code in {204, 404}, response.text
        if account_id is not None:
            response = client.delete(f"/api/v1/platform-accounts/{account_id}")
            assert response.status_code in {204, 404}, response.text
        if pillar_id is not None:
            response = client.delete(f"/api/v1/content-pillars/{pillar_id}")
            assert response.status_code in {204, 404}, response.text
