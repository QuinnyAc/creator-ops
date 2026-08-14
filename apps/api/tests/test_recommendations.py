from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_topic_recommendation_uses_recent_pillar_trend_evidence() -> None:
    suffix = uuid4().hex[:8]
    pillar_id: str | None = None
    account_id: str | None = None
    topic_id: str | None = None
    content_ids: list[str] = []
    publication_ids: list[str] = []

    try:
        pillar_response = client.post(
            "/api/v1/content-pillars",
            json={"name": f"Recommendation Pillar {suffix}"},
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
                "name": f"Recommendation account {suffix}",
                "handle": f"recommendation-{suffix}",
            },
        )
        assert account_response.status_code == 201, account_response.text
        account_id = account_response.json()["id"]

        now = datetime.now(timezone.utc)
        history = [
            (now - timedelta(days=40), 1000, 50),
            (now - timedelta(days=5), 2000, 160),
        ]
        for index, (published_at, views, favorites) in enumerate(history):
            content_response = client.post(
                "/api/v1/contents",
                json={
                    "title": f"Historical recommendation content {index} {suffix}",
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
                    "likes": 80,
                    "comments": 20,
                    "favorites": favorites,
                    "shares": 10,
                    "followers_gained": 15,
                    "extra_metrics": {},
                },
            )
            assert metric_response.status_code == 201, metric_response.text

        topic_response = client.post(
            "/api/v1/topics",
            json={
                "title": f"Next recommended topic {suffix}",
                "pillar_id": pillar_id,
                "status": "approved",
                "goal": "growth",
            },
        )
        assert topic_response.status_code == 201, topic_response.text
        topic_id = topic_response.json()["id"]

        score_response = client.put(
            f"/api/v1/topics/{topic_id}/score",
            json={
                "pain_point": 5,
                "search_demand": 4,
                "trend_heat": 4,
                "differentiation": 5,
                "commercial_value": 4,
                "production_effort": 2,
            },
        )
        assert score_response.status_code == 200, score_response.text
        assert float(score_response.json()["priority_score"]) == 80.1

        recommendations_response = client.get("/api/v1/recommendations/topics?limit=20")
        assert recommendations_response.status_code == 200, recommendations_response.text
        recommendation = next(
            item
            for item in recommendations_response.json()
            if item["topic_id"] == topic_id
        )
        assert recommendation["trend_signal"] == "rising"
        assert recommendation["evidence_publications"] == 2
        assert recommendation["evidence_adjustment"] == 8.0
        assert recommendation["recommended_score"] == 88.1
        assert any("+8" in reason for reason in recommendation["reasons"])

    finally:
        if topic_id is not None:
            response = client.delete(f"/api/v1/topics/{topic_id}")
            assert response.status_code in {204, 404}, response.text
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
