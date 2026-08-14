from sqlalchemy import delete, func, select

from app.core.config import settings
from app.db import SessionLocal
from app.demo_seed import DEMO_PREFIX, seed_demo
from app.models import (
    Content,
    ContentPillar,
    Inspiration,
    MetricSnapshot,
    PlatformAccount,
    Publication,
    Review,
    Tag,
    Topic,
)
from app.models_insights import Insight


def _count(db, model, predicate) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(predicate)) or 0)


def _cleanup_demo_data() -> None:
    with SessionLocal() as db:
        demo_content_ids = select(Content.id).where(Content.title.like(f"{DEMO_PREFIX}%"))
        demo_topic_ids = select(Topic.id).where(Topic.title.like(f"{DEMO_PREFIX}%"))

        db.execute(
            delete(Insight).where(
                Insight.title == "Reusable frameworks create save intent"
            )
        )
        db.execute(delete(Review).where(Review.content_id.in_(demo_content_ids)))
        demo_publication_ids = select(Publication.id).where(
            Publication.content_id.in_(demo_content_ids)
        )
        db.execute(
            delete(MetricSnapshot).where(
                MetricSnapshot.publication_id.in_(demo_publication_ids)
            )
        )
        db.execute(delete(Publication).where(Publication.content_id.in_(demo_content_ids)))
        db.execute(delete(Content).where(Content.id.in_(demo_content_ids)))
        db.execute(delete(Topic).where(Topic.id.in_(demo_topic_ids)))
        db.execute(delete(Inspiration).where(Inspiration.title.like(f"{DEMO_PREFIX}%")))
        db.execute(
            delete(PlatformAccount).where(
                PlatformAccount.handle.in_([
                    "creator-ops-demo-xhs",
                    "creator-ops-demo-bilibili",
                ])
            )
        )
        db.execute(delete(Tag).where(Tag.name.in_(["Tutorial", "Workflow", "High-save"])))
        db.execute(
            delete(ContentPillar).where(
                ContentPillar.name.in_(["Creator Strategy", "AI Tools"])
            )
        )
        db.commit()


def test_demo_seed_is_idempotent() -> None:
    _cleanup_demo_data()
    try:
        with SessionLocal() as db:
            seed_demo(db)
            first = {
                "topics": _count(db, Topic, Topic.title.like(f"{DEMO_PREFIX}%")),
                "contents": _count(db, Content, Content.title.like(f"{DEMO_PREFIX}%")),
                "accounts": _count(
                    db,
                    PlatformAccount,
                    PlatformAccount.handle.in_([
                        "creator-ops-demo-xhs",
                        "creator-ops-demo-bilibili",
                    ]),
                ),
            }

        with SessionLocal() as db:
            seed_demo(db)
            second = {
                "topics": _count(db, Topic, Topic.title.like(f"{DEMO_PREFIX}%")),
                "contents": _count(db, Content, Content.title.like(f"{DEMO_PREFIX}%")),
                "accounts": _count(
                    db,
                    PlatformAccount,
                    PlatformAccount.handle.in_([
                        "creator-ops-demo-xhs",
                        "creator-ops-demo-bilibili",
                    ]),
                ),
            }
            assert first == {"topics": 2, "contents": 2, "accounts": 2}
            assert second == first
            assert _count(
                db,
                Publication,
                Publication.content_id.in_(
                    select(Content.id).where(Content.title.like(f"{DEMO_PREFIX}%"))
                ),
            ) == 3
    finally:
        _cleanup_demo_data()


def test_demo_seed_is_disabled_in_production(monkeypatch) -> None:
    monkeypatch.setattr(settings, "app_env", "production")
    with SessionLocal() as db:
        try:
            seed_demo(db)
        except RuntimeError as exc:
            assert "disabled" in str(exc).lower()
        else:
            raise AssertionError("Demo seed must be disabled in production")
