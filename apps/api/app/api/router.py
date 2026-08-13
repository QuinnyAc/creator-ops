from fastapi import APIRouter

from app.api.routes import analytics, contents, dashboard, inspirations, publishing, reviews, topics

api_router = APIRouter()
api_router.include_router(dashboard.router)
api_router.include_router(inspirations.router)
api_router.include_router(topics.router)
api_router.include_router(contents.router)
api_router.include_router(publishing.router)
api_router.include_router(analytics.router)
api_router.include_router(reviews.router)
