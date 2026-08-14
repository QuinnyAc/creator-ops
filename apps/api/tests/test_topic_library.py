from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_topic_library_includes_assigned_tags() -> None:
    suffix = uuid4().hex[:8]
    topic_id: str | None = None
    tag_id: str | None = None

    try:
        topic_response = client.post(
            "/api/v1/topics",
            json={
                "title": f"Topic library tags {suffix}",
                "core_idea": "Verify that the topic list exposes assigned tags.",
                "planned_platforms": [],
            },
        )
        assert topic_response.status_code == 201, topic_response.text
        topic_id = topic_response.json()["id"]

        tag_response = client.post(
            "/api/v1/tags",
            json={"name": f"library-{suffix}"},
        )
        assert tag_response.status_code == 201, tag_response.text
        tag_id = tag_response.json()["id"]

        assignment_response = client.put(
            f"/api/v1/topics/{topic_id}/tags",
            json={"tag_ids": [tag_id]},
        )
        assert assignment_response.status_code == 200, assignment_response.text

        list_response = client.get("/api/v1/topics")
        assert list_response.status_code == 200, list_response.text
        item = next(topic for topic in list_response.json() if topic["id"] == topic_id)

        assert [tag["id"] for tag in item["tags"]] == [tag_id]
        assert item["tags"][0]["name"] == f"library-{suffix}"
    finally:
        if topic_id is not None:
            response = client.delete(f"/api/v1/topics/{topic_id}")
            assert response.status_code in {204, 404}, response.text
        if tag_id is not None:
            response = client.delete(f"/api/v1/tags/{tag_id}")
            assert response.status_code in {204, 404}, response.text
