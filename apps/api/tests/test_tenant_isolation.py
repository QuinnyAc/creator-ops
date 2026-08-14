from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models import User

client = TestClient(app)


def _register(label: str) -> tuple[str, str]:
    suffix = uuid4().hex[:10]
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"tenant-{label}-{suffix}@example.com",
            "display_name": f"Tenant {label}",
            "password": f"tenant-{label}-{suffix}-secure",
            "timezone": "Asia/Shanghai",
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    return payload["user"]["id"], payload["access_token"]


def test_creator_data_is_isolated_between_users() -> None:
    user_a_id: str | None = None
    user_b_id: str | None = None
    unique_marker = f"TENANT-A-{uuid4().hex[:12]}"

    try:
        user_a_id, token_a = _register("a")
        user_b_id, token_b = _register("b")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        platforms_response = client.get("/api/v1/platforms", headers=headers_a)
        assert platforms_response.status_code == 200, platforms_response.text
        platform_id = platforms_response.json()[0]["id"]

        account_a_response = client.post(
            "/api/v1/platform-accounts",
            headers=headers_a,
            json={
                "platform_id": platform_id,
                "name": f"{unique_marker} account",
                "handle": f"tenant-a-{uuid4().hex[:8]}",
            },
        )
        assert account_a_response.status_code == 201, account_a_response.text
        account_a_id = account_a_response.json()["id"]

        account_b_response = client.post(
            "/api/v1/platform-accounts",
            headers=headers_b,
            json={
                "platform_id": platform_id,
                "name": "Tenant B account",
                "handle": f"tenant-b-{uuid4().hex[:8]}",
            },
        )
        assert account_b_response.status_code == 201, account_b_response.text
        account_b_id = account_b_response.json()["id"]

        content_a_response = client.post(
            "/api/v1/contents",
            headers=headers_a,
            json={
                "title": f"{unique_marker} private content",
                "content_type": "video",
                "status": "published",
            },
        )
        assert content_a_response.status_code == 201, content_a_response.text
        content_a_id = content_a_response.json()["id"]

        publication_a_response = client.post(
            "/api/v1/publications",
            headers=headers_a,
            json={
                "content_id": content_a_id,
                "platform_account_id": account_a_id,
                "title": f"{unique_marker} private publication",
                "status": "published",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "platform_tags": ["private-tenant-a"],
            },
        )
        assert publication_a_response.status_code == 201, publication_a_response.text
        publication_a_id = publication_a_response.json()["id"]

        metric_response = client.post(
            f"/api/v1/analytics/publications/{publication_a_id}/metrics",
            headers=headers_a,
            json={
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "views": 1234,
                "likes": 100,
                "comments": 20,
                "favorites": 140,
                "shares": 12,
                "followers_gained": 33,
                "extra_metrics": {},
            },
        )
        assert metric_response.status_code == 201, metric_response.text

        review_response = client.put(
            f"/api/v1/reviews/content/{content_a_id}",
            headers=headers_a,
            json={
                "goal": f"{unique_marker} private goal",
                "learnings": f"{unique_marker} private learning",
                "next_action": "Keep this insight isolated to tenant A.",
            },
        )
        assert review_response.status_code == 200, review_response.text

        insight_response = client.post(
            f"/api/v1/insights/from-content/{content_a_id}",
            headers=headers_a,
            json={"category": "security-test"},
        )
        assert insight_response.status_code == 200, insight_response.text
        insight_a_id = insight_response.json()["id"]

        # Tenant B must not be able to discover tenant A's content through list APIs.
        b_contents = client.get("/api/v1/contents", headers=headers_b)
        assert b_contents.status_code == 200, b_contents.text
        assert all(item["id"] != content_a_id for item in b_contents.json())

        b_publications = client.get("/api/v1/publications", headers=headers_b)
        assert b_publications.status_code == 200, b_publications.text
        assert all(item["id"] != publication_a_id for item in b_publications.json())

        b_insights = client.get("/api/v1/insights", headers=headers_b)
        assert b_insights.status_code == 200, b_insights.text
        assert all(item["id"] != insight_a_id for item in b_insights.json())

        # Direct object access must fail as not-found, preventing cross-tenant enumeration.
        assert client.get(
            f"/api/v1/contents/{content_a_id}", headers=headers_b
        ).status_code == 404
        assert client.patch(
            f"/api/v1/contents/{content_a_id}",
            headers=headers_b,
            json={"title": "Tenant B takeover"},
        ).status_code == 404
        assert client.delete(
            f"/api/v1/contents/{content_a_id}", headers=headers_b
        ).status_code == 404

        # Tenant B cannot combine its own platform account with tenant A's Content.
        cross_publication = client.post(
            "/api/v1/publications",
            headers=headers_b,
            json={
                "content_id": content_a_id,
                "platform_account_id": account_b_id,
                "status": "draft",
                "platform_tags": [],
            },
        )
        assert cross_publication.status_code == 404, cross_publication.text

        # Tenant B also cannot use tenant A's account with any publication request.
        content_b_response = client.post(
            "/api/v1/contents",
            headers=headers_b,
            json={
                "title": "Tenant B content",
                "content_type": "video",
                "status": "draft",
            },
        )
        assert content_b_response.status_code == 201, content_b_response.text
        content_b_id = content_b_response.json()["id"]
        foreign_account_publication = client.post(
            "/api/v1/publications",
            headers=headers_b,
            json={
                "content_id": content_b_id,
                "platform_account_id": account_a_id,
                "status": "draft",
                "platform_tags": [],
            },
        )
        assert foreign_account_publication.status_code == 404, foreign_account_publication.text

        assert client.get(
            f"/api/v1/analytics/publications/{publication_a_id}/metrics",
            headers=headers_b,
        ).status_code == 404
        assert client.post(
            f"/api/v1/analytics/publications/{publication_a_id}/metrics",
            headers=headers_b,
            json={
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "views": 999999,
                "likes": 0,
                "comments": 0,
                "favorites": 0,
                "shares": 0,
                "followers_gained": 0,
                "extra_metrics": {},
            },
        ).status_code == 404

        assert client.get(
            f"/api/v1/reviews/content/{content_a_id}", headers=headers_b
        ).status_code == 404
        assert client.put(
            f"/api/v1/reviews/content/{content_a_id}",
            headers=headers_b,
            json={"learnings": "Tenant B overwrite"},
        ).status_code == 404
        assert client.post(
            f"/api/v1/insights/from-content/{content_a_id}",
            headers=headers_b,
            json={"category": "stolen"},
        ).status_code == 404
        assert client.patch(
            f"/api/v1/insights/{insight_a_id}",
            headers=headers_b,
            json={"body": "Tenant B overwrite"},
        ).status_code == 404
        assert client.delete(
            f"/api/v1/insights/{insight_a_id}", headers=headers_b
        ).status_code == 404

        # Creator-owned exports are another data-exfiltration boundary.
        for export_name in ("topics", "contents", "publications", "reviews", "insights"):
            export_response = client.get(
                f"/api/v1/exports/{export_name}.csv", headers=headers_b
            )
            assert export_response.status_code == 200, export_response.text
            assert unique_marker not in export_response.text

        # Verify tenant A data was not mutated by the denied requests.
        a_content = client.get(f"/api/v1/contents/{content_a_id}", headers=headers_a)
        assert a_content.status_code == 200, a_content.text
        assert unique_marker in a_content.json()["title"]
        a_metrics = client.get(
            f"/api/v1/analytics/publications/{publication_a_id}/metrics",
            headers=headers_a,
        )
        assert a_metrics.status_code == 200, a_metrics.text
        assert a_metrics.json()[0]["views"] == 1234

    finally:
        user_ids = [UUID(value) for value in (user_a_id, user_b_id) if value is not None]
        if user_ids:
            with SessionLocal() as db:
                db.execute(delete(User).where(User.id.in_(user_ids)))
                db.commit()
