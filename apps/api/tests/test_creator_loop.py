from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_complete_creator_operations_loop() -> None:
    suffix = uuid4().hex[:8]
    pillar_id: str | None = None
    inspiration_id: str | None = None
    topic_id: str | None = None
    content_id: str | None = None
    account_id: str | None = None
    publication_id: str | None = None

    try:
        pillar_response = client.post(
            "/api/v1/content-pillars",
            json={
                "name": f"Integration Pillar {suffix}",
                "description": "Created by the end-to-end creator loop test.",
            },
        )
        assert pillar_response.status_code == 201, pillar_response.text
        pillar_id = pillar_response.json()["id"]

        inspiration_response = client.post(
            "/api/v1/inspirations",
            json={
                "title": f"收藏率为什么比点赞更重要 {suffix}",
                "note": "验证知识型创作者的内容决策闭环。",
                "source": "integration-test",
            },
        )
        assert inspiration_response.status_code == 201, inspiration_response.text
        inspiration_id = inspiration_response.json()["id"]

        topic_response = client.post(
            f"/api/v1/inspirations/{inspiration_id}/convert",
            json={
                "pillar_id": pillar_id,
                "target_audience": "知识型内容创作者",
                "user_problem": "不知道应该关注哪些内容指标",
                "angle": "从收藏行为解释内容长期价值",
                "goal": "growth",
                "planned_platforms": ["bilibili", "xiaohongshu"],
            },
        )
        assert topic_response.status_code == 201, topic_response.text
        topic = topic_response.json()
        topic_id = topic["id"]
        assert topic["inspiration_id"] == inspiration_id
        assert topic["pillar_id"] == pillar_id

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
        score = score_response.json()
        assert float(score["opportunity_score"]) == 89.0
        assert float(score["priority_score"]) == 80.1

        approve_response = client.patch(
            f"/api/v1/topics/{topic_id}",
            json={"status": "approved"},
        )
        assert approve_response.status_code == 200, approve_response.text

        content_response = client.post(
            "/api/v1/contents",
            json={
                "title": f"收藏率比点赞更重要的 3 个原因 {suffix}",
                "topic_id": topic_id,
                "pillar_id": pillar_id,
                "content_type": "video",
                "status": "research",
            },
        )
        assert content_response.status_code == 201, content_response.text
        content_id = content_response.json()["id"]

        workspace_response = client.patch(
            f"/api/v1/contents/{content_id}",
            json={
                "status": "ready",
                "research_notes": "收藏往往代表用户未来还会回来消费内容。",
                "outline": "问题 → 指标解释 → 三个原因 → CTA",
                "script": "这是一条用于集成测试的完整脚本。",
                "copywriting": "别只盯着点赞，收藏可能更接近长期价值。",
                "cta": "把你最想复盘的指标记下来。",
            },
        )
        assert workspace_response.status_code == 200, workspace_response.text
        assert workspace_response.json()["status"] == "ready"

        platforms_response = client.get("/api/v1/platforms")
        assert platforms_response.status_code == 200, platforms_response.text
        platforms = platforms_response.json()
        bilibili = next(platform for platform in platforms if platform["slug"] == "bilibili")

        account_response = client.post(
            "/api/v1/platform-accounts",
            json={
                "platform_id": bilibili["id"],
                "name": f"Integration Bilibili {suffix}",
                "handle": f"integration-{suffix}",
            },
        )
        assert account_response.status_code == 201, account_response.text
        account_id = account_response.json()["id"]

        published_at = datetime.now(timezone.utc).isoformat()
        publication_response = client.post(
            "/api/v1/publications",
            json={
                "content_id": content_id,
                "platform_account_id": account_id,
                "title": f"为什么收藏率值得创作者重点关注 {suffix}",
                "copywriting": "集成测试发布文案",
                "platform_tags": ["创作者", "内容运营"],
                "status": "published",
                "published_at": published_at,
                "url": f"https://example.com/integration/{suffix}",
            },
        )
        assert publication_response.status_code == 201, publication_response.text
        publication_id = publication_response.json()["id"]

        metric_response = client.post(
            f"/api/v1/analytics/publications/{publication_id}/metrics",
            json={
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "views": 1200,
                "likes": 96,
                "favorites": 144,
                "comments": 30,
                "shares": 18,
                "followers_gained": 22,
                "extra_metrics": {"coins": 12},
            },
        )
        assert metric_response.status_code == 201, metric_response.text
        assert metric_response.json()["favorites"] == 144

        analytics_response = client.get("/api/v1/analytics/summary")
        assert analytics_response.status_code == 200, analytics_response.text
        analytics = analytics_response.json()
        assert analytics["views"] >= 1200
        assert analytics["favorites"] >= 144
        assert analytics["followers_gained"] >= 22

        platform_analytics_response = client.get("/api/v1/analytics/platforms")
        assert platform_analytics_response.status_code == 200, platform_analytics_response.text
        bilibili_analytics = next(
            item
            for item in platform_analytics_response.json()
            if item["platform_slug"] == "bilibili"
        )
        assert bilibili_analytics["views"] >= 1200
        assert bilibili_analytics["favorites"] >= 144
        assert bilibili_analytics["publications"] >= 1

        review_response = client.put(
            f"/api/v1/reviews/content/{content_id}",
            json={
                "goal": "验证高收藏内容是否更值得系列化",
                "expected_outcome": "收藏率高于点赞率",
                "what_worked": "选题问题明确，内容结构具体",
                "what_didnt_work": "还需要更真实的平台数据",
                "learnings": "知识型内容应该长期观察收藏和涨粉，而不是只看点赞",
                "next_action": "继续制作收藏率与转粉率系列内容",
            },
        )
        assert review_response.status_code == 200, review_response.text

        get_review_response = client.get(f"/api/v1/reviews/content/{content_id}")
        assert get_review_response.status_code == 200, get_review_response.text
        assert "长期观察收藏" in get_review_response.json()["learnings"]

        for export_path in ("topics", "contents", "publications", "reviews"):
            export_response = client.get(f"/api/v1/exports/{export_path}.csv")
            assert export_response.status_code == 200, export_response.text
            assert export_response.headers["content-type"].startswith("text/csv")
            assert suffix in export_response.text

        dashboard_response = client.get("/api/v1/dashboard/summary")
        assert dashboard_response.status_code == 200, dashboard_response.text
        dashboard = dashboard_response.json()
        assert dashboard["topics_approved"] >= 1

    finally:
        if publication_id is not None:
            response = client.delete(f"/api/v1/publications/{publication_id}")
            assert response.status_code in {204, 404}, response.text
        if content_id is not None:
            response = client.delete(f"/api/v1/contents/{content_id}")
            assert response.status_code in {204, 404}, response.text
        if topic_id is not None:
            response = client.delete(f"/api/v1/topics/{topic_id}")
            assert response.status_code in {204, 404}, response.text
        if inspiration_id is not None:
            response = client.delete(f"/api/v1/inspirations/{inspiration_id}")
            assert response.status_code in {204, 404}, response.text
        if account_id is not None:
            response = client.delete(f"/api/v1/platform-accounts/{account_id}")
            assert response.status_code in {204, 404}, response.text
        if pillar_id is not None:
            response = client.delete(f"/api/v1/content-pillars/{pillar_id}")
            assert response.status_code in {204, 404}, response.text
