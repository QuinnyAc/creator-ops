from datetime import datetime, timedelta, timezone

from sqlalchemy import insert, select

from app.core.config import settings
from app.db import SessionLocal
from app.models import (
    Content,
    ContentPillar,
    Inspiration,
    MetricSnapshot,
    Platform,
    PlatformAccount,
    Publication,
    Review,
    Tag,
    Topic,
    TopicScore,
    User,
    content_tags,
    topic_tags,
)
from app.models_insights import Insight
from app.services.scoring import calculate_topic_scores

DEMO_MARKER = "Demo · AI Tools"


def _score(topic: Topic, **values: int) -> TopicScore:
    opportunity, priority = calculate_topic_scores(**values)
    return TopicScore(
        topic_id=topic.id,
        opportunity_score=opportunity,
        priority_score=priority,
        **values,
    )


def seed_demo() -> None:
    if settings.app_env == "production":
        raise SystemExit("Demo seed is disabled when APP_ENV=production.")

    now = datetime.now(timezone.utc).replace(microsecond=0)

    with SessionLocal() as db:
        user = db.get(User, settings.default_user_id)
        if user is None:
            raise SystemExit(
                "Seeded local creator user is missing. Run `alembic upgrade head` first."
            )

        already_seeded = db.scalar(
            select(ContentPillar.id).where(
                ContentPillar.user_id == user.id,
                ContentPillar.name == DEMO_MARKER,
            )
        )
        if already_seeded is not None:
            print("Creator Ops demo data already exists; nothing changed.")
            return

        pillars = {
            "ai": ContentPillar(
                user_id=user.id,
                name=DEMO_MARKER,
                description="AI tools, workflows, and practical creator tutorials.",
            ),
            "growth": ContentPillar(
                user_id=user.id,
                name="Demo · Creator Growth",
                description="Data-driven creator operations and growth systems.",
            ),
            "product": ContentPillar(
                user_id=user.id,
                name="Demo · Product Thinking",
                description="Product thinking for creators and independent builders.",
            ),
        }
        db.add_all(pillars.values())
        db.flush()

        tags = {
            name: Tag(user_id=user.id, name=f"Demo · {name}")
            for name in ("教程", "清单", "新手", "案例", "增长")
        }
        db.add_all(tags.values())
        db.flush()

        inspirations = [
            Inspiration(
                user_id=user.id,
                title="Demo · 为什么知识型内容的收藏率值得重点看？",
                note="评论区反复有人问：播放量之外，到底哪个指标更值得长期观察？",
                source="评论区",
                status="inbox",
            ),
            Inspiration(
                user_id=user.id,
                title="Demo · 用 AI 把 2 小时研究压缩到 20 分钟",
                note="把真实研究工作流拆成可以复用的步骤。",
                source="工作流复盘",
                status="inbox",
            ),
            Inspiration(
                user_id=user.id,
                title="Demo · 创作者为什么需要自己的 Operating System",
                note="把 Notion 模板升级成完整运营闭环的产品观点。",
                source="产品思考",
                status="inbox",
            ),
        ]
        db.add_all(inspirations)
        db.flush()

        topics = {
            "ai_workflow": Topic(
                user_id=user.id,
                inspiration_id=inspirations[1].id,
                pillar_id=pillars["ai"].id,
                title="Demo · AI 研究工作流：从 2 小时到 20 分钟",
                core_idea="展示一套真实可复制的 AI 辅助研究流程，而不是罗列工具。",
                target_audience="知识型创作者、独立开发者",
                user_problem="研究资料多、整理慢、难以形成内容结构",
                angle="完整工作流 + 前后时间对比",
                goal="growth",
                status="approved",
                planned_platforms=["bilibili", "xiaohongshu"],
            ),
            "metrics": Topic(
                user_id=user.id,
                inspiration_id=inspirations[0].id,
                pillar_id=pillars["growth"].id,
                title="Demo · 别只看点赞：知识型内容更值得追踪的 3 个指标",
                core_idea="用收藏率、互动率和转粉率解释内容的长期价值。",
                target_audience="正在认真运营账号的知识型创作者",
                user_problem="看了后台数据，但不知道什么指标能指导下一条内容",
                angle="从决策价值而不是虚荣指标出发",
                goal="retention",
                status="approved",
                planned_platforms=["xiaohongshu", "bilibili"],
            ),
            "creator_os": Topic(
                user_id=user.id,
                inspiration_id=inspirations[2].id,
                pillar_id=pillars["product"].id,
                title="Demo · 从内容表格到 Creator OS：创作者真正需要什么系统？",
                core_idea="解释通用数据库与垂直 Creator Operations System 的差别。",
                target_audience="个人 IP、独立创作者、内容团队负责人",
                user_problem="Notion / 表格能记录内容，但无法形成数据驱动闭环",
                angle="以 Topic → Content → Publication → Metrics → Review 为主线",
                goal="brand",
                status="evaluating",
                planned_platforms=["bilibili", "youtube"],
            ),
            "title": Topic(
                user_id=user.id,
                pillar_id=pillars["ai"].id,
                title="Demo · 7 个 AI 标题公式，哪些真的能提高收藏？",
                core_idea="把标题模式与真实收藏表现连接起来。",
                target_audience="知识型自媒体创作者",
                user_problem="标题靠感觉，没有自己的历史证据",
                angle="标题模式 + 数据对比",
                goal="engagement",
                status="scheduled",
                planned_platforms=["youtube", "xiaohongshu"],
            ),
        }
        db.add_all(topics.values())
        db.flush()

        db.add_all(
            [
                _score(
                    topics["ai_workflow"],
                    pain_point=5,
                    search_demand=5,
                    trend_heat=5,
                    differentiation=4,
                    commercial_value=5,
                    production_effort=2,
                ),
                _score(
                    topics["metrics"],
                    pain_point=5,
                    search_demand=4,
                    trend_heat=4,
                    differentiation=5,
                    commercial_value=4,
                    production_effort=2,
                ),
                _score(
                    topics["creator_os"],
                    pain_point=4,
                    search_demand=3,
                    trend_heat=3,
                    differentiation=5,
                    commercial_value=5,
                    production_effort=3,
                ),
                _score(
                    topics["title"],
                    pain_point=4,
                    search_demand=5,
                    trend_heat=4,
                    differentiation=4,
                    commercial_value=4,
                    production_effort=2,
                ),
            ]
        )

        db.execute(
            insert(topic_tags),
            [
                {"topic_id": topics["ai_workflow"].id, "tag_id": tags["教程"].id},
                {"topic_id": topics["ai_workflow"].id, "tag_id": tags["案例"].id},
                {"topic_id": topics["metrics"].id, "tag_id": tags["增长"].id},
                {"topic_id": topics["metrics"].id, "tag_id": tags["清单"].id},
                {"topic_id": topics["creator_os"].id, "tag_id": tags["案例"].id},
                {"topic_id": topics["title"].id, "tag_id": tags["清单"].id},
            ],
        )

        platform_rows = db.execute(
            select(Platform).where(
                Platform.slug.in_(["xiaohongshu", "bilibili", "wechat", "youtube"])
            )
        ).scalars()
        platforms = {platform.slug: platform for platform in platform_rows}
        required_platforms = {"xiaohongshu", "bilibili", "wechat", "youtube"}
        if set(platforms) != required_platforms:
            raise SystemExit("Platform catalog is incomplete. Run all Alembic migrations first.")

        accounts = {
            slug: PlatformAccount(
                user_id=user.id,
                platform_id=platform.id,
                name=f"Demo · {platform.name}",
                handle=f"creator-ops-demo-{slug}",
            )
            for slug, platform in platforms.items()
        }
        db.add_all(accounts.values())
        db.flush()

        contents = {
            "ai_workflow": Content(
                user_id=user.id,
                topic_id=topics["ai_workflow"].id,
                pillar_id=pillars["ai"].id,
                title="Demo · 我用 AI 把内容研究从 2 小时压缩到 20 分钟",
                content_type="video",
                status="published",
                research_notes="记录研究任务拆分、资料抓取、事实核对和最终大纲生成的真实耗时。",
                outline="痛点 → 原流程 → 新流程 → 前后对比 → 适用边界",
                script="不要从工具开始。先把研究任务拆成问题清单，再让 AI 帮你寻找候选答案，最后人工核对关键事实。",
                copywriting="真正省时间的不是某个 AI 工具，而是一套可以重复使用的研究流程。",
                cta="收藏这套流程，下次做深度内容时直接照着跑一遍。",
                planned_publish_at=now - timedelta(days=12),
            ),
            "metrics": Content(
                user_id=user.id,
                topic_id=topics["metrics"].id,
                pillar_id=pillars["growth"].id,
                title="Demo · 知识博主别只看点赞：更值得追踪的 3 个指标",
                content_type="video",
                status="review",
                research_notes="比较收藏、互动、转粉对下一轮内容决策的解释力。",
                outline="虚荣指标 → 收藏率 → 互动率 → 转粉率 → 如何复盘",
                script="点赞说明这一秒觉得不错，收藏往往意味着用户认为以后还会回来。",
                copywriting="如果你的内容目标是长期增长，只盯点赞很容易做错下一条。",
                cta="把你最近 10 条内容的收藏率和转粉率拉出来看一次。",
                planned_publish_at=now - timedelta(days=40),
            ),
            "creator_os": Content(
                user_id=user.id,
                topic_id=topics["creator_os"].id,
                pillar_id=pillars["product"].id,
                title="Demo · Creator OS 的产品结构",
                content_type="article",
                status="script",
                research_notes="梳理通用工具与垂直内容运营系统的差异。",
                outline="Notion 的优势 → 垂直系统的必要性 → 核心实体 → 数据飞轮",
                script="一张表能记录内容，但它不知道 Topic、Content 和 Publication 为什么是不同对象。",
            ),
            "title": Content(
                user_id=user.id,
                topic_id=topics["title"].id,
                pillar_id=pillars["ai"].id,
                title="Demo · 7 个 AI 标题公式实测",
                content_type="video",
                status="ready",
                research_notes="用历史标题模式分析决定测试样本。",
                outline="7 种公式 → 历史数据 → 选择 3 个继续测试",
                script="标题不是玄学。先从自己的历史内容里找出哪些结构真正有效。",
                planned_publish_at=now + timedelta(days=3),
            ),
        }
        db.add_all(contents.values())
        db.flush()

        db.execute(
            insert(content_tags),
            [
                {"content_id": contents["ai_workflow"].id, "tag_id": tags["教程"].id},
                {"content_id": contents["ai_workflow"].id, "tag_id": tags["案例"].id},
                {"content_id": contents["metrics"].id, "tag_id": tags["增长"].id},
                {"content_id": contents["metrics"].id, "tag_id": tags["清单"].id},
                {"content_id": contents["creator_os"].id, "tag_id": tags["案例"].id},
                {"content_id": contents["title"].id, "tag_id": tags["清单"].id},
            ],
        )

        publications = {
            "ai_bilibili": Publication(
                content_id=contents["ai_workflow"].id,
                platform_account_id=accounts["bilibili"].id,
                title="2 小时 → 20 分钟：我的 AI 内容研究工作流",
                copywriting="完整展示我现在如何做深度内容研究。",
                platform_tags=["AI", "效率", "自媒体"],
                status="published",
                published_at=now - timedelta(days=11),
                url="https://example.com/demo/bilibili/ai-workflow",
            ),
            "ai_xhs": Publication(
                content_id=contents["ai_workflow"].id,
                platform_account_id=accounts["xiaohongshu"].id,
                title="我把内容研究从 2 小时压缩到 20 分钟的 5 步流程",
                copywriting="不是工具清单，是我每天真的在用的研究 SOP。",
                platform_tags=["AI工具", "内容创作", "效率"],
                status="published",
                published_at=now - timedelta(days=10),
                url="https://example.com/demo/xiaohongshu/ai-workflow",
            ),
            "metrics_previous": Publication(
                content_id=contents["metrics"].id,
                platform_account_id=accounts["xiaohongshu"].id,
                title="别只看点赞：知识博主更该看的 3 个指标",
                platform_tags=["自媒体运营", "数据分析"],
                status="published",
                published_at=now - timedelta(days=42),
                url="https://example.com/demo/xiaohongshu/creator-metrics",
            ),
            "metrics_recent": Publication(
                content_id=contents["metrics"].id,
                platform_account_id=accounts["bilibili"].id,
                title="为什么收藏率比点赞更值得创作者关注？",
                platform_tags=["自媒体", "数据复盘"],
                status="published",
                published_at=now - timedelta(days=8),
                url="https://example.com/demo/bilibili/creator-metrics",
            ),
            "title_scheduled": Publication(
                content_id=contents["title"].id,
                platform_account_id=accounts["youtube"].id,
                title="7 AI Title Formulas: What Actually Gets Saved?",
                platform_tags=["creator", "AI", "titles"],
                status="scheduled",
                scheduled_at=now + timedelta(days=3),
            ),
        }
        db.add_all(publications.values())
        db.flush()

        metric_specs = [
            ("ai_bilibili", 1, 11000, 720, 88, 620, 96, 180, {"coins": 150}),
            ("ai_bilibili", 7, 24500, 1450, 210, 1380, 240, 390, {"coins": 310}),
            ("ai_xhs", 1, 8200, 690, 76, 980, 110, 145, {}),
            ("ai_xhs", 7, 16800, 1260, 142, 2120, 250, 280, {}),
            ("metrics_previous", 1, 9800, 720, 95, 1350, 120, 160, {}),
            ("metrics_previous", 7, 14200, 990, 150, 2160, 210, 230, {}),
            ("metrics_recent", 1, 4200, 260, 46, 310, 42, 55, {"coins": 30}),
            ("metrics_recent", 7, 6900, 420, 75, 520, 76, 82, {"coins": 54}),
        ]
        for key, day, views, likes, comments, favorites, shares, followers, extra in metric_specs:
            publication = publications[key]
            db.add(
                MetricSnapshot(
                    publication_id=publication.id,
                    captured_at=publication.published_at + timedelta(days=day),
                    views=views,
                    likes=likes,
                    comments=comments,
                    favorites=favorites,
                    shares=shares,
                    followers_gained=followers,
                    extra_metrics=extra,
                )
            )

        review = Review(
            content_id=contents["ai_workflow"].id,
            goal="验证工作流教程是否同时带来收藏和涨粉。",
            expected_outcome="收藏率高于普通观点内容，并在两个平台都能获得持续长尾。",
            what_worked="具体时间对比让价值非常直观；步骤足够具体，收藏动机强。",
            what_didnt_work="B站标题偏功能描述，后续可以测试更强的结果型包装。",
            learnings="对知识型教程，明确结果 + 可复制步骤比单纯工具清单更容易产生高收藏；同一核心内容跨平台时应保留价值结构但改写标题包装。",
            next_action="继续做 AI 创作工作流系列，并为同一内容预先设计两种平台标题模式。",
        )
        db.add(review)
        db.flush()
        db.add(
            Insight(
                user_id=user.id,
                source_review_id=review.id,
                title="Demo · 教程内容：明确结果 + 可复制步骤",
                body=review.learnings or "",
                category="validated-learning",
                status="active",
            )
        )

        db.add(
            Review(
                content_id=contents["metrics"].id,
                goal="判断创作者指标主题是否仍值得继续做。",
                expected_outcome="高收藏，但近期曝光可能低于上一个周期。",
                what_worked="用户问题明确，收藏信号仍然存在。",
                what_didnt_work="近期版本平均浏览下降，说明包装或用户兴趣可能发生变化。",
                learnings="同一 Content Pillar 的历史高表现不能永久代表当前兴趣，应该比较最近 30 天与前 30 天。",
                next_action="保留数据复盘主题，但换成更具体的案例标题再验证一次。",
            )
        )

        db.commit()
        print("Creator Ops demo data seeded successfully.")
        print("Open http://localhost:3000 to explore the populated workspace.")


if __name__ == "__main__":
    seed_demo()
