from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Content, MetricSnapshot, Publication
from app.schemas_review_assistant import ReviewMetricsSummary, ReviewSuggestion
from app.services.title_patterns import PATTERN_LABELS, classify_title_patterns


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


def _summary_from_row(row: Sequence[object]) -> ReviewMetricsSummary:
    publications, views, likes, comments, favorites, shares, followers = [
        int(value or 0) for value in row
    ]
    interactions = likes + comments + favorites + shares
    return ReviewMetricsSummary(
        publications=publications,
        views=views,
        likes=likes,
        comments=comments,
        favorites=favorites,
        shares=shares,
        followers_gained=followers,
        avg_views=round(views / publications, 2) if publications else 0.0,
        engagement_rate=round(interactions / views * 100, 2) if views else 0.0,
        favorite_rate=round(favorites / views * 100, 2) if views else 0.0,
        follower_conversion_rate=round(followers / views * 100, 2) if views else 0.0,
    )


def _metrics_summary(
    db: Session,
    user_id: UUID,
    *,
    content_id: UUID | None = None,
) -> ReviewMetricsSummary:
    latest = _latest_metric_snapshot_subquery()
    query = (
        select(
            func.count(latest.c.id),
            func.coalesce(func.sum(latest.c.views), 0),
            func.coalesce(func.sum(latest.c.likes), 0),
            func.coalesce(func.sum(latest.c.comments), 0),
            func.coalesce(func.sum(latest.c.favorites), 0),
            func.coalesce(func.sum(latest.c.shares), 0),
            func.coalesce(func.sum(latest.c.followers_gained), 0),
        )
        .select_from(latest)
        .join(Publication, Publication.id == latest.c.publication_id)
        .join(Content, Content.id == Publication.content_id)
        .where(Content.user_id == user_id)
    )
    if content_id is not None:
        query = query.where(Content.id == content_id)
    return _summary_from_row(db.execute(query).one())


def _title_patterns(db: Session, content: Content) -> list[str]:
    titles = list(
        db.scalars(
            select(func.coalesce(Publication.title, Content.title))
            .select_from(Publication)
            .join(Content, Content.id == Publication.content_id)
            .where(Publication.content_id == content.id)
        )
    )
    if not titles:
        titles = [content.title]

    patterns: set[str] = set()
    for title in titles:
        patterns.update(classify_title_patterns(title or ""))
    return [PATTERN_LABELS.get(pattern, pattern) for pattern in sorted(patterns)]


def _above(value: float, baseline: float, fallback: float) -> bool:
    return value >= baseline * 1.15 if baseline > 0 else value >= fallback


def _below(value: float, baseline: float) -> bool:
    return baseline > 0 and value <= baseline * 0.85


def build_review_suggestion(
    db: Session,
    *,
    content: Content,
    user_id: UUID,
) -> ReviewSuggestion:
    metrics = _metrics_summary(db, user_id, content_id=content.id)
    baseline = _metrics_summary(db, user_id)
    title_patterns = _title_patterns(db, content)

    if metrics.publications == 0:
        return ReviewSuggestion(
            metrics=metrics,
            baseline=baseline,
            title_patterns=title_patterns,
            what_worked="尚无可验证的数据快照，暂时不要把主观感觉当作结论。",
            what_didnt_work="当前最大的缺口是数据不足：至少为一个已发布 Publication 记录最新指标。",
            learnings="这条内容还不能形成稳定方法论。先补充发布数据，再比较收藏率、互动率和转粉率。",
            next_action="到数据分析页记录发布后的指标快照，再回来生成数据辅助复盘。",
        )

    strengths: list[str] = []
    weaknesses: list[str] = []

    if _above(metrics.avg_views, baseline.avg_views, 1000):
        strengths.append(
            f"平均浏览 {metrics.avg_views:.0f}，高于当前账号整体基线 {baseline.avg_views:.0f}。"
        )
    if _above(metrics.favorite_rate, baseline.favorite_rate, 3.0):
        strengths.append(
            f"收藏率 {metrics.favorite_rate:.2f}% 表现突出，说明内容具备较强的长期参考价值。"
        )
    if _above(metrics.follower_conversion_rate, baseline.follower_conversion_rate, 0.5):
        strengths.append(
            f"转粉率 {metrics.follower_conversion_rate:.2f}% 较好，内容与目标用户的匹配度较高。"
        )
    if _above(metrics.engagement_rate, baseline.engagement_rate, 5.0):
        strengths.append(
            f"互动率 {metrics.engagement_rate:.2f}% 较好，内容能推动用户进一步动作。"
        )

    if _below(metrics.avg_views, baseline.avg_views):
        weaknesses.append(
            f"平均浏览 {metrics.avg_views:.0f} 低于账号基线 {baseline.avg_views:.0f}，需要优先检查选题包装、标题、封面或分发时机。"
        )
    if _below(metrics.favorite_rate, baseline.favorite_rate):
        weaknesses.append(
            f"收藏率 {metrics.favorite_rate:.2f}% 低于账号基线 {baseline.favorite_rate:.2f}%，内容的可保存价值可能不足。"
        )
    if _below(metrics.follower_conversion_rate, baseline.follower_conversion_rate):
        weaknesses.append(
            f"转粉率 {metrics.follower_conversion_rate:.2f}% 低于账号基线 {baseline.follower_conversion_rate:.2f}%，需要检查定位、受众和 CTA。"
        )
    if _below(metrics.engagement_rate, baseline.engagement_rate):
        weaknesses.append(
            f"互动率 {metrics.engagement_rate:.2f}% 低于账号基线 {baseline.engagement_rate:.2f}%，可以增强观点冲突、问题设计或评论引导。"
        )

    if not strengths:
        strengths.append("目前没有明显高于账号基线的指标；这本身也是一个有效结论，避免强行归因。")
    if not weaknesses:
        weaknesses.append("暂未发现明显低于账号基线的核心指标，下一轮可以优先验证可复制性。")

    patterns = "、".join(title_patterns) if title_patterns else "未识别"
    learnings = (
        f"基于 {metrics.publications} 个发布实例的最新快照：平均浏览 {metrics.avg_views:.0f}，"
        f"互动率 {metrics.engagement_rate:.2f}%，收藏率 {metrics.favorite_rate:.2f}%，"
        f"转粉率 {metrics.follower_conversion_rate:.2f}%。当前标题模式：{patterns}。"
    )

    strong_value = _above(metrics.favorite_rate, baseline.favorite_rate, 3.0)
    strong_reach = _above(metrics.avg_views, baseline.avg_views, 1000)
    weak_reach = _below(metrics.avg_views, baseline.avg_views)
    weak_conversion = _below(metrics.follower_conversion_rate, baseline.follower_conversion_rate)

    if strong_value and strong_reach:
        next_action = "把该主题做成系列，并保持核心价值结构；下一条只改变一个变量（标题、角度或案例）验证可复制性。"
    elif strong_value and weak_reach:
        next_action = "内容价值信号不错但曝光偏弱：保留主题与结构，优先 A/B 测试标题、封面和发布时机。"
    elif strong_reach and weak_conversion:
        next_action = "曝光不错但转粉偏弱：下一条收窄目标用户、强化账号定位表达，并设计更明确的关注 CTA。"
    else:
        next_action = "下一轮只改变一个关键变量并继续记录数据，避免同时改选题、标题、结构和发布时间导致无法归因。"

    return ReviewSuggestion(
        metrics=metrics,
        baseline=baseline,
        title_patterns=title_patterns,
        what_worked="\n".join(f"- {item}" for item in strengths),
        what_didnt_work="\n".join(f"- {item}" for item in weaknesses),
        learnings=learnings,
        next_action=next_action,
    )
