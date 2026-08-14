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
PLATFORM_SLUGS = {"xiaohongshu", "bilibili", "wechat_official", "youtube"}


def _topic_score(topic: Topic, **values: int) -> TopicScore:
    opportunity, priority = calculate_topic_scores(**values)
    return TopicScore(
        topic_id=topic.id,
        opportunity_score=opportunity,
        priority_score=priority,
        **values,
    )


def _metric(
    publication: Publication,
    *,
    day: int,
    views: int,
    likes: int,
    comments: int,
    favorites: int,
    shares: int,
    followers: int,
    extra: dict[str, int | float | str] | None = None,
) -> MetricSnapshot:
    if publication.published_at is None:
        raise ValueError("Demo metric publication must have published_at.")
    return MetricSnapshot(
        publication_id=publication.id,
        captured_at=publication.published_at + timedelta(days=day),
        views=views,
        likes=likes,
        comments=comments,
        favorites=favorites,
        shares=shares,
        followers_gained=followers,
        extra_metrics=extra or {},
    )


def seed_demo() -> None:
    if settings.app_env == "production":
        raise SystemExit("Demo seed is disabled when APP_ENV=production.")

    now = datetime.now(timezone.utc).replace(microsecond=0)

    with SessionLocal() as db:
        user = db.get(User, settings.default_user_id)
        if user is None:
            raise SystemExit("Run `alembic upgrade head` before seeding demo data.")

        exists = db.scalar(
            select(ContentPillar.id).where(
                ContentPillar.user_id == user.id,
                ContentPillar.name == DEMO_MARKER,
            )
        )
        if exists is not None:
            print("Creator Ops demo data already exists; nothing changed.")
            return

        platforms = {
            item.slug: item
            for item in db.scalars(select(Platform).where(Platform.slug.in_(PLATFORM_SLUGS)))
        }
        if set(platforms) != PLATFORM_SLUGS:
            raise SystemExit("Platform catalog is incomplete. Run all migrations first.")

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
        tags = {
            key: Tag(user_id=user.id, name=f"Demo · {key}")
            for key in ("教程", "清单", "案例", "增长")
        }
        db.add_all([*pillars.values(), *tags.values()])
        db.flush()

        inspiration_metrics = Inspiration(
            user_id=user.id,
            title="Demo · 为什么知识型内容的收藏率值得重点看？",
            note="后台有很多数字，但哪些真正能指导下一条内容？",
            source="评论区",
            status="inbox",
        )
        inspiration_os = Inspiration(
            user_id=user.id,
            title="Demo · 创作者为什么需要自己的 Operating System",
            note="通用表格能记录内容，但很难形成数据闭环。",
            source="产品思考",
            status="inbox",
        )
        db.add_all([inspiration_metrics, inspiration_os])
        db.flush()

        topics = {
            "ai": Topic(
                user_id=user.id,
                pillar_id=pillars["ai"].id,
                title="Demo · AI 研究工作流：从 2 小时到 20 分钟",
                core_idea="展示真实可复制的 AI 辅助研究流程，而不是罗列工具。",
                target_audience="知识型创作者、独立开发者",
                user_problem="资料多、整理慢、研究过程无法复用",
                angle="完整工作流 + 前后耗时对比",
                goal="growth",
                status="approved",
                planned_platforms=["bilibili", "xiaohongshu"],
            ),
            "metrics": Topic(
                user_id=user.id,
                inspiration_id=inspiration_metrics.id,
                pillar_id=pillars["growth"].id,
                title="Demo · 别只看点赞：知识型内容更值得追踪的 3 个指标",
                core_idea="用收藏率、互动率和转粉率解释内容长期价值。",
                target_audience="正在认真运营账号的知识型创作者",
                user_problem="看了后台数据，却不知道如何指导下一轮创作",
                angle="从决策价值而不是虚荣指标出发",
                goal="retention",
                status="approved",
                planned_platforms=["xiaohongshu", "bilibili"],
            ),
            "os": Topic(
                user_id=user.id,
                inspiration_id=inspiration_os.id,
                pillar_id=pillars["product"].id,
                title="Demo · 从内容表格到 Creator OS：创作者真正需要什么系统？",
                core_idea="解释通用数据库与垂直 Creator Operations System 的差别。",
                target_audience="个人 IP、独立创作者、内容团队负责人",
                user_problem="信息能记录，但选题、发布、数据和复盘没有闭环",
                angle="Topic → Content → Publication → Metrics → Review",
                goal="brand",
                status="evaluating",
                planned_platforms=["bilibili", "youtube"],
            ),
            "title": Topic(
                user_id=user.id,
                pillar_id=pillars["ai"].id,
                title="Demo · 7 个 AI 标题公式，哪些真的能提高收藏？",
                core_idea="把标题模式与历史收藏表现连接起来。",
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

        score_values = {
            "ai": dict(
                pain_point=5,
                search_demand=5,
                trend_heat=5,
                differentiation=4,
                commercial_value=5,
                production_effort=2,
            ),
            "metrics": dict(
                pain_point=5,
                search_demand=4,
                trend_heat=4,
                differentiation=5,
                commercial_value=4,
                production_effort=2,
            ),
            "os": dict(
                pain_point=4,
                search_demand=3,
                trend_heat=3,
                differentiation=5,
                commercial_value=5,
                production_effort=3,
            ),
            "title": dict(
                pain_point=4,
                search_demand=5,
                trend_heat=4,
                differentiation=4,
                commercial_value=4,
                production_effort=2,
            ),
        }
        db.add_all([_topic_score(topics[key], **values) for key, values in score_values.items()])
        db.execute(
            insert(topic_tags),
            [
                {"topic_id": topics["ai"].id, "tag_id": tags["教程"].id},
                {"topic_id": topics["ai"].id, "tag_id": tags["案例"].id},
                {"topic_id": topics["metrics"].id, "tag_id": tags["增长"].id},
                {"topic_id": topics["metrics"].id, "tag_id": tags["清单"].id},
                {"topic_id": topics["os"].id, "tag_id": tags["案例"].id},
                {"topic_id": topics["title"].id, "tag_id": tags["清单"].id},
            ],
        )

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
            "ai": Content(
                user_id=user.id,
                topic_id=topics["ai"].id,
                pillar_id=pillars["ai"].id,
                title="Demo · 我用 AI 把内容研究从 2 小时压缩到 20 分钟",
                content_type="video",
                status="published",
                research_notes="记录任务拆分、资料检索、事实核对和大纲整理的真实耗时。",
                outline="痛点 → 原流程 → 新流程 → 前后对比 → 适用边界",
                script="先把研究任务拆成问题清单，再让 AI 找候选答案，关键事实仍由人核对。",
                copywriting="真正省时间的不是某个 AI 工具，而是一套可重复使用的研究流程。",
                cta="收藏这套流程，下次做深度内容时直接跑一遍。",
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
                script="点赞说明这一秒觉得不错，收藏往往代表用户认为以后还会回来。",
                copywriting="如果目标是长期增长，只盯点赞很容易做错下一条。",
                cta="把最近 10 条内容的收藏率和转粉率拉出来看一次。",
            ),
            "os": Content(
                user_id=user.id,
                topic_id=topics["os"].id,
                pillar_id=pillars["product"].id,
                title="Demo · Creator OS 的产品结构",
                content_type="article",
                status="script",
                outline="Notion 优势 → 垂直系统必要性 → 核心实体 → 数据飞轮",
                script="一张表能记录内容，但它不知道 Topic、Content 和 Publication 为什么不同。",
            ),
            "title": Content(
                user_id=user.id,
                topic_id=topics["title"].id,
                pillar_id=pillars["ai"].id,
                title="Demo · 7 个 AI 标题公式实测",
                content_type="video",
                status="ready",
                outline="7 种公式 → 历史数据 → 选择 3 个继续测试",
                script="标题不是玄学，先从自己的历史内容里找出真正有效的结构。",
                planned_publish_at=now + timedelta(days=3),
            ),
        }
        db.add_all(contents.values())
        db.flush()
        db.execute(
            insert(content_tags),
            [
                {"content_id": contents["ai"].id, "tag_id": tags["教程"].id},
                {"content_id": contents["ai"].id, "tag_id": tags["案例"].id},
                {"content_id": contents["metrics"].id, "tag_id": tags["增长"].id},
                {"content_id": contents["metrics"].id, "tag_id": tags["清单"].id},
                {"content_id": contents["os"].id, "tag_id": tags["案例"].id},
                {"content_id": contents["title"].id, "tag_id": tags["清单"].id},
            ],
        )

        publications = {
            "ai_bili": Publication(
                content_id=contents["ai"].id,
                platform_account_id=accounts["bilibili"].id,
                title="2 小时 → 20 分钟：我的 AI 内容研究工作流",
                platform_tags=["AI", "效率", "自媒体"],
                status="published",
                published_at=now - timedelta(days=11),
                url="https://example.com/demo/bilibili/ai-workflow",
            ),
            "ai_xhs": Publication(
                content_id=contents["ai"].id,
                platform_account_id=accounts["xiaohongshu"].id,
                title="我把内容研究从 2 小时压缩到 20 分钟的 5 步流程",
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

        db.add_all(
            [
                _metric(publications["ai_bili"], day=1, views=11000, likes=720, comments=88, favorites=620, shares=96, followers=180, extra={"coins": 150}),
                _metric(publications["ai_bili"], day=7, views=24500, likes=1450, comments=210, favorites=1380, shares=240, followers=390, extra={"coins": 310}),
                _metric(publications["ai_xhs"], day=1, views=8200, likes=690, comments=76, favorites=980, shares=110, followers=145),
                _metric(publications["ai_xhs"], day=7, views=16800, likes=1260, comments=142, favorites=2120, shares=250, followers=280),
                _metric(publications["metrics_previous"], day=1, views=9800, likes=720, comments=95, favorites=1350, shares=120, followers=160),
                _metric(publications["metrics_previous"], day=7, views=14200, likes=990, comments=150, favorites=2160, shares=210, followers=230),
                _metric(publications["metrics_recent"], day=1, views=4200, likes=260, comments=46, favorites=310, shares=42, followers=55, extra={"coins": 30}),
                _metric(publications["metrics_recent"], day=7, views=6900, likes=420, comments=75, favorites=520, shares=76, followers=82, extra={"coins": 54}),
            ]
        )

        ai_review = Review(
            content_id=contents["ai"].id,
            goal="验证工作流教程是否同时带来收藏和涨粉。",
            expected_outcome="两个平台都获得明显收藏与长尾。",
            what_worked="明确结果 + 可复制步骤让价值很直观。",
            what_didnt_work="B站标题偏功能描述，后续可以测试更强结果型包装。",
            learnings="知识型教程里，明确结果 + 可复制步骤比单纯工具清单更容易产生高收藏；跨平台应保留价值结构，但改写标题包装。",
            next_action="继续做 AI 创作工作流系列，每次只测试一个包装变量。",
        )
        metrics_review = Review(
            content_id=contents["metrics"].id,
            goal="判断创作者指标主题是否仍值得继续做。",
            expected_outcome="高收藏，但近期曝光可能低于上一个周期。",
            what_worked="用户问题明确，收藏信号仍然存在。",
            what_didnt_work="近期平均浏览下降，包装或用户兴趣可能变化。",
            learnings="历史高表现不代表当前兴趣，应该比较最近 30 天与前 30 天。",
            next_action="保留数据复盘主题，换成更具体的案例标题再验证一次。",
        )
        db.add_all([ai_review, metrics_review])
        db.flush()
        db.add(
            Insight(
                user_id=user.id,
                source_review_id=ai_review.id,
                title="Demo · 教程内容：明确结果 + 可复制步骤",
                body=ai_review.learnings or "",
                category="validated-learning",
                status="active",
            )
        )

        db.commit()
        print("Creator Ops demo data seeded successfully.")
        print("Open http://localhost:3000 to explore the populated workspace.")


if __name__ == "__main__":
    seed_demo()
