import csv
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models_insights import Insight

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/insights.csv")
def export_insights(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    insights = list(
        db.scalars(
            select(Insight)
            .where(Insight.user_id == user_id)
            .order_by(Insight.updated_at.desc())
        )
    )

    buffer = StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "title",
            "body",
            "category",
            "status",
            "source_review_id",
            "created_at",
            "updated_at",
        ]
    )
    for item in insights:
        writer.writerow(
            [
                item.id,
                item.title,
                item.body,
                item.category,
                item.status,
                item.source_review_id or "",
                item.created_at,
                item.updated_at,
            ]
        )

    return Response(
        content="\ufeff" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="creator-ops-insights.csv"'},
    )
