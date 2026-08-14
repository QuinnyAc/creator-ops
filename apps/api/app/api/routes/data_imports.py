import csv
import json
from datetime import datetime, timezone
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content, MetricSnapshot, Publication
from app.schemas_imports import MetricImportResult

router = APIRouter(prefix="/imports", tags=["imports"])

METRIC_FIELDS = ("views", "likes", "comments", "favorites", "shares", "followers_gained")


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _parse_metrics(row: dict[str, str | None]) -> dict[str, int]:
    metrics: dict[str, int] = {}
    for field in METRIC_FIELDS:
        raw = (row.get(field) or "0").strip()
        value = int(raw or "0")
        if field != "followers_gained" and value < 0:
            raise ValueError(f"{field} cannot be negative")
        metrics[field] = value
    return metrics


def _parse_extra_metrics(value: str | None) -> dict[str, int | float | str]:
    if not value or not value.strip():
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("extra_metrics must be a JSON object")
    return {str(key): item for key, item in parsed.items() if isinstance(item, (int, float, str))}


@router.post("/metrics.csv", response_model=MetricImportResult)
def import_metric_snapshots(
    csv_text: str = Body(..., media_type="text/csv"),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> MetricImportResult:
    reader = csv.DictReader(StringIO(csv_text.lstrip("\ufeff")))
    fieldnames = set(reader.fieldnames or [])
    required = {"publication_id", "captured_at"}
    missing = sorted(required - fieldnames)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required CSV columns: {', '.join(missing)}",
        )

    imported = 0
    updated = 0
    skipped = 0
    errors: list[str] = []

    for row_number, row in enumerate(reader, start=2):
        try:
            publication_id = UUID((row.get("publication_id") or "").strip())
            captured_at = _parse_datetime((row.get("captured_at") or "").strip())
            metrics = _parse_metrics(row)
            extra_metrics = _parse_extra_metrics(row.get("extra_metrics"))

            owned_publication_id = db.scalar(
                select(Publication.id)
                .join(Content, Content.id == Publication.content_id)
                .where(Publication.id == publication_id, Content.user_id == user_id)
            )
            if owned_publication_id is None:
                raise ValueError("publication does not belong to current user")

            snapshot = db.scalar(
                select(MetricSnapshot).where(
                    MetricSnapshot.publication_id == publication_id,
                    MetricSnapshot.captured_at == captured_at,
                )
            )
            if snapshot is None:
                snapshot = MetricSnapshot(
                    publication_id=publication_id,
                    captured_at=captured_at,
                    extra_metrics=extra_metrics,
                    **metrics,
                )
                db.add(snapshot)
                imported += 1
            else:
                for field, value in metrics.items():
                    setattr(snapshot, field, value)
                snapshot.extra_metrics = extra_metrics
                updated += 1
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            skipped += 1
            if len(errors) < 50:
                errors.append(f"Row {row_number}: {exc}")

    db.commit()
    return MetricImportResult(
        imported=imported,
        updated=updated,
        skipped=skipped,
        errors=errors,
    )
