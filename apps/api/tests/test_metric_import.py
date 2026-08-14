from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metric_csv_import_creates_and_updates_snapshots() -> None:
    suffix = uuid4().hex[:8]
    content_id: str | None = None
    account_id: str | None = None
    publication_id: str | None = None

    try:
        content_response = client.post(
            "/api/v1/contents",
            json={
                "title": f"Metric import {suffix}",
                "content_type": "video",
                "status": "published",
            },
        )
        assert content_response.status_code == 201, content_response.text
        content_id = content_response.json()["id"]

        platforms_response = client.get("/api/v1/platforms")
        assert platforms_response.status_code == 200, platforms_response.text
        platform = platforms_response.json()[0]

        account_response = client.post(
            "/api/v1/platform-accounts",
            json={
                "platform_id": platform["id"],
                "name": f"Metric Import {suffix}",
                "handle": f"metric-import-{suffix}",
            },
        )
        assert account_response.status_code == 201, account_response.text
        account_id = account_response.json()["id"]

        publication_response = client.post(
            "/api/v1/publications",
            json={
                "content_id": content_id,
                "platform_account_id": account_id,
                "status": "published",
                "published_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert publication_response.status_code == 201, publication_response.text
        publication_id = publication_response.json()["id"]

        captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        csv_text = (
            "publication_id,captured_at,views,likes,comments,favorites,shares,followers_gained,extra_metrics\n"
            f'{publication_id},{captured_at},1000,50,10,80,5,12,"{{""coins"": 7}}"\n'
        )
        import_response = client.post(
            "/api/v1/imports/metrics.csv",
            content=csv_text,
            headers={"Content-Type": "text/csv"},
        )
        assert import_response.status_code == 200, import_response.text
        assert import_response.json()["imported"] == 1
        assert import_response.json()["updated"] == 0
        assert import_response.json()["skipped"] == 0

        update_csv = (
            "publication_id,captured_at,views,likes,comments,favorites,shares,followers_gained\n"
            f"{publication_id},{captured_at},1300,65,12,110,7,18\n"
            f"not-a-uuid,{captured_at},1,1,1,1,1,1\n"
        )
        update_response = client.post(
            "/api/v1/imports/metrics.csv",
            content=update_csv,
            headers={"Content-Type": "text/csv"},
        )
        assert update_response.status_code == 200, update_response.text
        assert update_response.json()["imported"] == 0
        assert update_response.json()["updated"] == 1
        assert update_response.json()["skipped"] == 1
        assert update_response.json()["errors"]

        metrics_response = client.get(
            f"/api/v1/analytics/publications/{publication_id}/metrics"
        )
        assert metrics_response.status_code == 200, metrics_response.text
        metric = metrics_response.json()[0]
        assert metric["views"] == 1300
        assert metric["favorites"] == 110
        assert metric["followers_gained"] == 18

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
