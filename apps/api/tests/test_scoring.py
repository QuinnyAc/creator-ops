from decimal import Decimal

from app.services.scoring import calculate_topic_scores


def test_topic_score_high_value_low_effort() -> None:
    opportunity, priority = calculate_topic_scores(
        pain_point=5,
        search_demand=5,
        trend_heat=5,
        differentiation=5,
        commercial_value=5,
        production_effort=1,
    )

    assert opportunity == Decimal("100.00")
    assert priority == Decimal("100.00")


def test_topic_score_effort_discount() -> None:
    opportunity, priority = calculate_topic_scores(
        pain_point=4,
        search_demand=4,
        trend_heat=4,
        differentiation=4,
        commercial_value=4,
        production_effort=5,
    )

    assert opportunity == Decimal("80.00")
    assert priority == Decimal("48.00")
