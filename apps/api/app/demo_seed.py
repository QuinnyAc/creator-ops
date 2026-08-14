from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

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

DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_PREFIX = "Creator Ops Demo"


def _get_or_create_pillar(db: Session, name: str, description: str) -> ContentPillar:
    item = db.scalar(
        select(ContentPillar).where(
            ContentPillar.user_id == DEFAULT_USER_ID,
            ContentPillar.name == name,
        )
    )
    if item is None:
        item = ContentPillar(
            user_id=DEFAULT_USER_ID,
            name=name,
            description=description,
        )
        db.add(item)
        db.flush()
    return item


def _get_or_create_tag(db: Session, name: str) -> Tag:
    item = db.scalar(
        select(Tag).where(Tag.user_id == DEFAULT_USER_ID, Tag.name == name)
    )
    if item is None:
        item = Tag(user_id=DEFAULT_USER_ID, name=name)
        db.add(item)
        db.flush()
    return item


def _ensure_topic_tag(db: Session, topic_id: UUID, tag_id: UUID) -> None:
    exists = db.execute(
        select(topic_tags.c.topic_id).where(
            topic_tags.c.topic_id == topic_id,
            topic_tags.c.tag_id == tag_id,
        )
    ).first()
    if exists is None:
        db.execute(insert(topic_tags).values(topic_id=topic_id, tag_id=tag_id))


def _ensure_content_tag(db: Session, content_id: UUID, tag_id: UUID) -> None:
    exists = db.execute(
        select(content_tags.c.content_id).where(
            content_tags.c.content_id == content_id,
            content_tags.c.tag_id == tag_id,
        )
    ).first()
    if exists is None:
        db.execute(insert(content_tags).values(content_id=content_id, tag_id=tag_id))


def _get_or_create_topic(
    db: Session,
    *,
    title: str,
    pillar: ContentPillar,
    core_idea: str,
    status: str,
    goal: str,
    scores: tuple[int, int, int, int, int, int],
) -> Topic:
    topic = db.scalar(
        select(Topic).where(Topic.user_id == DEFAULT_USER_ID, Topic.title == title)
    )
    if topic is None:
        topic = Topic(
            user_id=DEFAULT_USER_ID,
            pillar_id=pillar.id,
            title=title,
            core_idea=core_idea,
            target_audience="Knowledge creators who want a repeatable content system",
            user_problem="Ideas, production status and performance learnings live in separate tools.",
            angle="Show the workflow as a closed operating loop instead of another generic database.",
            goal=goal,
            status=status,
            planned_platforms=["xiaohongshu", "bilibili", "youtube"],
        )
        db.add(topic)
        db.flush()

    existing_score = db.scalar(select(TopicScore).where(TopicScore.topic_id == topic.id))
    if existing_score is None:
        pain, search, heat, differentiation, commercial, effort = scores
        opportunity, priority = calculate_topic_scores(
            pain_point=pain,
            search_demand=search,
            trend_heat=heat,
            differentiation=differentiation,
            commercial_value=commercial,
            production_effort=effort,
        )
        db.add(
            TopicScore(
                topic_id=topic.id,
                pain_point=pain,
                search_demand=search,
                trend_heat=heat,
                differentiation=differentiation,
                commercial_value=commercial,
                production_effort=effort,
                opportunity_score=Decimal(str(opportunity)),
                priority_score=Decimal(str(priority)),
            )
        )
    return topic


def _get_or_create_content(
    db: Session,
    *,
    topic: Topic,
    pillar: ContentPillar,
    title: str,
    status: str,
    planned_publish_at: datetime | None,
) -> Content:
    content = db.scalar(
        select(Content).where(Content.user_id == DEFAULT_USER_ID, Content.title == title)
    )
    if content is None:
        content = Content(
            user_id=DEFAULT_USER_ID,
            topic_id=topic.id,
            pillar_id=pillar.id,
            title=title,
            content_type="video",
            status=status,
            research_notes="Collect creator workflow examples, recurring pain points and platform-specific constraints.",
            outline="Hook → fragmented workflow → operating loop → metrics → review → next decision",
            script="A creator does not need another place to store rows. They need a system that learns from every published piece.",
            copywriting="From idea to insight: one operating loop for creator work.",
            cta="Save this workflow and use the review to choose your next topic.",
            planned_publish_at=planned_publish_at,
        )
        db.add(content)
        db.flush()
    return content


def _get_or_create_account(
    db: Session,
    *,
    platform_slug: str,
    name: str,
    handle: str,
) -> PlatformAccount:
    platform = db.scalar(select(Platform).where(Platform.slug == platform_slug))
    if platform is None:
        raise RuntimeError(f"Platform catalog is missing {platform_slug!r}; run migrations first.")
    account = db.scalar(
        select(PlatformAccount).where(
            PlatformAccount.user_id == DEFAULT_USER_ID,
            PlatformAccount.platform_id == platform.id,
            PlatformAccount.handle == handle,
        )
    )
    if account is None:
        account = PlatformAccount(
            user_id=DEFAULT_USER_ID,
            platform_id=platform.id,
            name=name,
            handle=handle,
        )
        db.add(account)
        db.flush()
    return account


def _get_or_create_publication(
    db: Session,
    *,
    content: Content,
    account: PlatformAccount,
    title: str,
    status: str,
    published_at: datetime | None = None,
    scheduled_at: datetime | None = None,
) -> Publication:
    publication = db.scalar(
        select(Publication).where(
            Publication.content_id == content.id,
            Publication.platform_account_id == account.id,
            Publication.title == title,
        )
    )
    if publication is None:
        publication = Publication(
            content_id=content.id,
            platform_account_id=account.id,
            title=title,
            copywriting="Demo publication showing the Creator Ops operating loop.",
            platform_tags=["creatorops", "contentworkflow"],
            status=status,
            published_at=published_at,
            scheduled_at=scheduled_at,
            url=None,
        )
        db.add(publication)
        db.flush()
    return publication


def _ensure_snapshot(
    db: Session,
    *,
    publication: Publication,
    offset_hours: int,
    views: int,
    likes: int,
    favorites: int,
    comments: int,
    shares: int,
    followers: int,
) -> None:
    if publication.published_at is None:
        return
    captured_at = publication.published_at + timedelta(hours=offset_hours)
    exists = db.scalar(
        select(MetricSnapshot).where(
            MetricSnapshot.publication_id == publication.id,
            MetricSnapshot.captured_at == captured_at,
        )
    )
    if exists is None:
        db.add(
            MetricSnapshot(
                publication_id=publication.id,
                captured_at=captured_at,
                views=views,
                likes=likes,
                favorites=favorites,
                comments=comments,
                shares=shares,
                followers_gained=followers,
                extra_metrics={},
            )
        )


def seed_demo(db: Session) -> None:
    if settings.app_env == "production":
        raise RuntimeError("Demo seed is disabled when APP_ENV=production.")

    user = db.scalar(select(User).where(User.id == DEFAULT_USER_ID))
    if user is None:
        raise RuntimeError("Local demo creator is missing; run `alembic upgrade head` first.")

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    strategy = _get_or_create_pillar(
        db,
        "Creator Strategy",
        "Systems, planning and operating methods for independent creators.",
    )
    ai_tools = _get_or_create_pillar(
        db,
        "AI Tools",
        "Practical AI workflows and tools for creator productivity.",
    )

    tutorial = _get_or_create_tag(db, "Tutorial")
    workflow = _get_or_create_tag(db, "Workflow")
    high_save = _get_or_create_tag(db, "High-save")

    inspiration_title = f"{DEMO_PREFIX}: creators lose learnings after publishing"
    inspiration = db.scalar(
        select(Inspiration).where(
            Inspiration.user_id == DEFAULT_USER_ID,
            Inspiration.title == inspiration_title,
        )
    )
    if inspiration is None:
        db.add(
            Inspiration(
                user_id=DEFAULT_USER_ID,
                title=inspiration_title,
                note="Turn post-performance review into reusable decision evidence.",
                source="demo",
                status="inbox",
            )
        )

    operating_topic = _get_or_create_topic(
        db,
        title=f"{DEMO_PREFIX}: build a creator operating system",
        pillar=strategy,
        core_idea="The highest leverage is closing the loop from idea to performance learning.",
        status="completed",
        goal="save",
        scores=(5, 4, 4, 5, 4, 3),
    )
    ai_topic = _get_or_create_topic(
        db,
        title=f"{DEMO_PREFIX}: 5 AI workflows that save creators hours",
        pillar=ai_tools,
        core_idea="Teach repeatable creator workflows rather than isolated AI prompts.",
        status="approved",
        goal="growth",
        scores=(4, 5, 5, 4, 4, 2),
    )
    _ensure_topic_tag(db, operating_topic.id, workflow.id)
    _ensure_topic_tag(db, operating_topic.id, high_save.id)
    _ensure_topic_tag(db, ai_topic.id, tutorial.id)

    published_content = _get_or_create_content(
        db,
        topic=operating_topic,
        pillar=strategy,
        title=f"{DEMO_PREFIX}: From idea to insight",
        status="review",
        planned_publish_at=now - timedelta(days=3),
    )
    upcoming_content = _get_or_create_content(
        db,
        topic=ai_topic,
        pillar=ai_tools,
        title=f"{DEMO_PREFIX}: 5 AI workflows for creators",
        status="editing",
        planned_publish_at=now + timedelta(days=2),
    )
    _ensure_content_tag(db, published_content.id, workflow.id)
    _ensure_content_tag(db, published_content.id, high_save.id)
    _ensure_content_tag(db, upcoming_content.id, tutorial.id)

    xhs = _get_or_create_account(
        db,
        platform_slug="xiaohongshu",
        name="Creator Ops Demo · Xiaohongshu",
        handle="creator-ops-demo-xhs",
    )
    bilibili = _get_or_create_account(
        db,
        platform_slug="bilibili",
        name="Creator Ops Demo · Bilibili",
        handle="creator-ops-demo-bilibili",
    )

    published_at = now - timedelta(days=2)
    xhs_publication = _get_or_create_publication(
        db,
        content=published_content,
        account=xhs,
        title="为什么创作者需要一个从选题到复盘的闭环？",
        status="published",
        published_at=published_at,
    )
    bili_publication = _get_or_create_publication(
        db,
        content=published_content,
        account=bilibili,
        title="我把自媒体工作流做成了一个 Creator OS",
        status="published",
        published_at=published_at + timedelta(hours=2),
    )
    _get_or_create_publication(
        db,
        content=upcoming_content,
        account=xhs,
        title="5 个能真正节省创作者时间的 AI 工作流",
        status="scheduled",
        scheduled_at=now + timedelta(days=2),
    )

    _ensure_snapshot(
        db,
        publication=xhs_publication,
        offset_hours=24,
        views=12800,
        likes=880,
        favorites=1460,
        comments=126,
        shares=94,
        followers=138,
    )
    _ensure_snapshot(
        db,
        publication=xhs_publication,
        offset_hours=36,
        views=18600,
        likes=1240,
        favorites=2110,
        comments=181,
        shares=141,
        followers=216,
    )
    _ensure_snapshot(
        db,
        publication=bili_publication,
        offset_hours=24,
        views=9200,
        likes=730,
        favorites=610,
        comments=164,
        shares=87,
        followers=102,
    )

    review = db.scalar(select(Review).where(Review.content_id == published_content.id))
    if review is None:
        review = Review(
            content_id=published_content.id,
            goal="Validate whether creator workflow content produces saves and qualified followers.",
            expected_outcome="Strong save rate because the framework is reusable after watching.",
            what_worked="The operating-loop framing was concrete and the multi-platform adaptation remained consistent.",
            what_didnt_work="The opening could communicate the before/after outcome faster.",
            learnings="Workflow content with a reusable framework earns stronger save intent than isolated productivity tips.",
            next_action="Turn the operating loop into a short series and test a more outcome-led title.",
        )
        db.add(review)
        db.flush()

    insight = db.scalar(
        select(Insight).where(
            Insight.user_id == DEFAULT_USER_ID,
            Insight.source_review_id == review.id,
        )
    )
    if insight is None:
        db.add(
            Insight(
                user_id=DEFAULT_USER_ID,
                source_review_id=review.id,
                title="Reusable frameworks create save intent",
                body=review.learnings or "",
                category="content-learning",
                status="active",
            )
        )

    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed_demo(db)
    print("Creator Ops demo data is ready.")


if __name__ == "__main__":
    main()
