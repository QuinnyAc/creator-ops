from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Content, ContentPillar, MetricSnapshot, Publication, Topic, TopicScore
from app.schemas_recommendations import TopicRecommendation

CANDIDATE_STATUSES = ("evaluating", "approved", "scheduled")


def _latest_metric_snapshot_subquery():
    latest_times = (
        select(
            MetricSnapshot.publication_id,
            func.max(MetricSnapshot.captured_at).label("captured_at"),
        )
        .group_by(MetricSnapshot.publication_id)
        .subquery()
    )
    return (
        select(MetricSnapshot)
        .join(
            latest_times,
            (MetricSnapshot.publication_id == latest_times.c.publication_id)
            & (MetricSnapshot.captured_at == latest_times.c.captured_at),
        )
        .subquery()
    )


def _rate(favorites: int, views: int) -> float:
    return round(favorites / views * 100, 2) if views else 0.0


def _account_baseline(db: Session, user_id: UUID) -> tuple[int, float, float]:
    latest = _latest_metric_snapshot_subquery()
    row = db.execute(
        select(
            func.count(latest.c.id),
            func.coalesce(func.sum(latest.c.views), 0),
            func.coalesce(func.sum(latest.c.favorites), 0),
        )
        .select_from(latest)
        .join(Publication, Publication.id == latest.c.publication_id)
        .join(Content, Content.id == Publication.content_id)
        .where(Content.user_id == user_id)
    ).one()
    publications = int(row[0] or 0)
    views = int(row[1] or 0)
    favorites = int(row[2] or 0)
    avg_views = round(views / publications, 2) if publications else 0.0
    return publications, avg_views, _rate(favorites, views)


def _pillar_baselines(
    db: Session,
    user_id: UUID,
) -> dict[UUID, tuple[int, float, float]]:
    latest = _latest_metric_snapshot_subquery()
    rows = db.execute(
        select(
            Content.pillar_id,
            func.count(latest.c.id),
            func.coalesce(func.sum(latest.c.views), 0),
            func.coalesce(func.sum(latest.c.favorites), 0),
        )
        .select_from(latest)
        .join(Publication, Publication.id == latest.c.publication_id)
        .join(Content, Content.id == Publication.content_id)
        .where(Content.user_id == user_id, Content.pillar_id.is_not(None))
        .group_by(Content.pillar_id)
    ).all()

    result: dict[UUID, tuple[int, float, float]] = {}
    for pillar_id, publications, views, favorites in rows:
        publication_count = int(publications or 0)
        total_views = int(views or 0)
        total_favorites = int(favorites or 0)
        result[pillar_id] = (
            publication_count,
            round(total_views / publication_count, 2) if publication_count else 0.0,
            _rate(total_favorites, total_views),
        )
    return result


def _pillar_trends(
    db: Session,
    user_id: UUID,
    *,
    window_days: int = 30,
) -> dict[UUID, str]:
    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(days=window_days)
    previous_cutoff = now - timedelta(days=window_days * 2)
    latest = _latest_metric_snapshot_subquery()
    rows = db.execute(
        select(
            Content.pillar_id,
            Publication.published_at,
            latest.c.views,
        )
        .select_from(latest)
        .join(Publication, Publication.id == latest.c.publication_id)
        .join(Content, Content.id == Publication.content_id)
        .where(
            Content.user_id == user_id,
            Content.pillar_id.is_not(None),
            Publication.published_at.is_not(None),
            Publication.published_at >= previous_cutoff,
        )
    ).all()

    grouped: dict[UUID, dict[str, list[int]]] = defaultdict(
        lambda: {"recent": [], "previous": []}
    )
    for pillar_id, published_at, views in rows:
        key = "recent" if published_at >= recent_cutoff else "previous"
        grouped[pillar_id][key].append(int(views or 0))

    result: dict[UUID, str] = {}
    for pillar_id, periods in grouped.items():
        recent = periods["recent"]
        previous = periods["previous"]
        if not recent:
            result[pillar_id] = "insufficient"
            continue
        if not previous:
            result[pillar_id] = "new"
            continue
        recent_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous)
        if previous_avg <= 0:
            result[pillar_id] = "new"
            continue
        change = (recent_avg - previous_avg) / previous_avg * 100
        if change >= 20:
            result[pillar_id] = "rising"
        elif change <= -20:
            result[pillar_id] = "falling"
        else:
            result[pillar_id] = "stable"
    return result


def rank_topics(
    db: Session,
    *,
    user_id: UUID,
    limit: int = 10,
) -> list[TopicRecommendation]:
    _, account_avg_views, account_favorite_rate = _account_baseline(db, user_id)
    pillar_baselines = _pillar_baselines(db, user_id)
    pillar_trends = _pillar_trends(db, user_id)

    candidates = db.execute(
        select(Topic, TopicScore, ContentPillar.name.label("pillar_name"))
        .join(TopicScore, TopicScore.topic_id == Topic.id)
        .outerjoin(ContentPillar, ContentPillar.id == Topic.pillar_id)
        .where(
            Topic.user_id == user_id,
            Topic.status.in_(CANDIDATE_STATUSES),
        )
    ).all()

    recommendations: list[TopicRecommendation] = []
    for row in candidates:
        topic = row.Topic
        score = row.TopicScore
        base_score = float(score.priority_score)
        adjustment = 0.0
        reasons: list[str] = []
        evidence_publications = 0
        pillar_avg_views: float | None = None
        pillar_favorite_rate: float | None = None
        trend_signal: str | None = None

        if topic.pillar_id is None:
            reasons.append("未设置 Content Pillar，暂时只使用人工选题评分。")
        else:
            baseline = pillar_baselines.get(topic.pillar_id)
            trend_signal = pillar_trends.get(topic.pillar_id)
            if baseline is None:
                reasons.append("这个 Content Pillar 还没有历史发布数据，暂不做表现加权。")
            else:
                evidence_publications, pillar_avg_views, pillar_favorite_rate = baseline
                if account_avg_views > 0:
                    view_ratio = pillar_avg_views / account_avg_views
                    if view_ratio >= 1.25:
                        adjustment += 5
                        reasons.append("该 Content Pillar 的历史平均浏览显著高于账号基线：+5。")
                    elif view_ratio <= 0.75:
                        adjustment -= 5
                        reasons.append("该 Content Pillar 的历史平均浏览明显低于账号基线：-5。")
                    else:
                        reasons.append("该 Content Pillar 的历史平均浏览接近账号基线。")

                if account_favorite_rate > 0:
                    favorite_ratio = pillar_favorite_rate / account_favorite_rate
                    if favorite_ratio >= 1.2:
                        adjustment += 3
                        reasons.append("该 Content Pillar 的收藏率高于账号基线：+3。")
                    elif favorite_ratio <= 0.8:
                        adjustment -= 3
                        reasons.append("该 Content Pillar 的收藏率低于账号基线：-3。")

            if trend_signal == "rising":
                adjustment += 8
                reasons.append("最近 30 天该 Content Pillar 的平均浏览较前 30 天上升至少 20%：+8。")
            elif trend_signal == "falling":
                adjustment -= 8
                reasons.append("最近 30 天该 Content Pillar 的平均浏览较前 30 天下滑至少 20%：-8。")
            elif trend_signal == "new":
                adjustment += 2
                reasons.append("该 Content Pillar 最近出现新数据但缺少前期样本：探索奖励 +2。")
            elif trend_signal == "stable":
                reasons.append("该 Content Pillar 最近表现稳定，不额外加减分。")

        adjustment = max(-15.0, min(15.0, adjustment))
        recommended_score = max(0.0, min(100.0, base_score + adjustment))
        if not reasons:
            reasons.append("当前没有足够历史证据，推荐分等于人工优先级。")

        recommendations.append(
            TopicRecommendation(
                topic_id=topic.id,
                title=topic.title,
                status=topic.status,
                pillar_id=topic.pillar_id,
                pillar_name=row.pillar_name,
                base_priority_score=round(base_score, 2),
                evidence_adjustment=round(adjustment, 2),
                recommended_score=round(recommended_score, 2),
                evidence_publications=evidence_publications,
                pillar_avg_views=pillar_avg_views,
                account_avg_views=account_avg_views if account_avg_views > 0 else None,
                pillar_favorite_rate=pillar_favorite_rate,
                account_favorite_rate=account_favorite_rate if account_favorite_rate > 0 else None,
                trend_signal=trend_signal,
                reasons=reasons,
            )
        )

    return sorted(
        recommendations,
        key=lambda item: (item.recommended_score, item.base_priority_score),
        reverse=True,
    )[:limit]
