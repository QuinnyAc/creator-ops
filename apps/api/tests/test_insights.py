from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_review_learning_can_be_promoted_to_creator_playbook() -> None:
    suffix = uuid4().hex[:8]
    content_id: str | None = None
    insight_id: str | None = None

    try:
        content_response = client.post(
            "/api/v1/contents",
            json={
                "title": f"Playbook integration {suffix}",
                "content_type": "video",
                "status": "review",
            },
        )
        assert content_response.status_code == 201, content_response.text
        content_id = content_response.json()["id"]

        review_response = client.put(
            f"/api/v1/reviews/content/{content_id}",
            json={
                "goal": "验证方法论沉淀",
                "learnings": f"教程内容 {suffix} 应该优先优化收藏率，而不是只追求点赞。",
                "next_action": "下一轮继续验证收藏与转粉的关系",
            },
        )
        assert review_response.status_code == 200, review_response.text

        promote_response = client.post(
            f"/api/v1/insights/from-content/{content_id}",
            json={"category": "content-learning"},
        )
        assert promote_response.status_code == 200, promote_response.text
        insight = promote_response.json()
        insight_id = insight["id"]
        assert suffix in insight["body"]
        assert insight["source_review_id"] == review_response.json()["id"]

        # Promotion is idempotent for the same review and refreshes the existing insight.
        second_promote = client.post(
            f"/api/v1/insights/from-content/{content_id}",
            json={"title": f"Updated playbook rule {suffix}", "category": "validated-learning"},
        )
        assert second_promote.status_code == 200, second_promote.text
        assert second_promote.json()["id"] == insight_id
        assert second_promote.json()["category"] == "validated-learning"

        list_response = client.get("/api/v1/insights?status_filter=active")
        assert list_response.status_code == 200, list_response.text
        assert any(item["id"] == insight_id for item in list_response.json())

        archive_response = client.patch(
            f"/api/v1/insights/{insight_id}",
            json={"status": "archived"},
        )
        assert archive_response.status_code == 200, archive_response.text
        assert archive_response.json()["status"] == "archived"

        export_response = client.get("/api/v1/exports/insights.csv")
        assert export_response.status_code == 200, export_response.text
        assert export_response.headers["content-type"].startswith("text/csv")
        assert suffix in export_response.text

    finally:
        if insight_id is not None:
            response = client.delete(f"/api/v1/insights/{insight_id}")
            assert response.status_code in {204, 404}, response.text
        if content_id is not None:
            response = client.delete(f"/api/v1/contents/{content_id}")
            assert response.status_code in {204, 404}, response.text
