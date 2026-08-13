from fastapi import APIRouter

from app.api.routes import (
    analytics,
    auth,
    contents,
    dashboard,
    inspirations,
    publishing,
    reviews,
    settings,
    title_analytics,
    topics,
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
api_router.include_router(reviews.router)
