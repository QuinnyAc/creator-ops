from decimal import Decimal, ROUND_HALF_UP


WEIGHTS = {
    "pain_point": Decimal("0.25"),
    "search_demand": Decimal("0.20"),
    "trend_heat": Decimal("0.15"),
    "differentiation": Decimal("0.20"),
    "commercial_value": Decimal("0.20"),
}


def calculate_topic_scores(
    *,
    pain_point: int,
    search_demand: int,
    trend_heat: int,
    differentiation: int,
    commercial_value: int,
    production_effort: int,
) -> tuple[Decimal, Decimal]:
    """Return opportunity and effort-adjusted priority on a 0-100 scale.

    Raw opportunity uses the five value dimensions. Production effort then
    discounts the priority by 0%, 10%, 20%, 30%, or 40%.
    """
    weighted_average = (
        Decimal(pain_point) * WEIGHTS["pain_point"]
        + Decimal(search_demand) * WEIGHTS["search_demand"]
        + Decimal(trend_heat) * WEIGHTS["trend_heat"]
        + Decimal(differentiation) * WEIGHTS["differentiation"]
        + Decimal(commercial_value) * WEIGHTS["commercial_value"]
    )
    opportunity = (weighted_average * Decimal("20")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    effort_discount = Decimal("1.0") - Decimal(production_effort - 1) * Decimal("0.10")
    priority = (opportunity * effort_discount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return opportunity, priority
