from fastapi import APIRouter

from app.api.routes import (
    analytics,
    auth,
    contents,
    dashboard,
    data_exports,
    data_imports,
    inspirations,
    insight_exports,
    insights,
    publishing,
    review_assistant,
    reviews,
    settings,
    title_analytics,
    topics,
    trend_analytics,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(settings.router)
api_router.include_router(inspirations.router)
api_router.include_router(topics.router)
api_router.include_router(contents.router)
api_router.include_router(publishing.router)
api_router.include_router(analytics.router)
api_router.include_router(title_analytics.router)
api_router.include_router(trend_analytics.router)
api_router.include_router(data_exports.router)
api_router.include_router(insight_exports.router)
api_router.include_router(data_imports.router)
api_router.include_router(insights.router)
api_router.include_router(review_assistant.router)
api_router.include_router(reviews.router)
