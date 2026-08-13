from uuid import UUID

from fastapi import Header, HTTPException, status

from app.core.config import settings


def get_current_user_id(x_user_id: str | None = Header(default=None)) -> UUID:
    """Temporary single-user dependency until authentication is introduced."""
    if x_user_id is None:
        return settings.default_user_id

    try:
        return UUID(x_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-ID must be a valid UUID.",
        ) from exc
