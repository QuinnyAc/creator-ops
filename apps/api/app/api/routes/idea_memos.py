from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import IdeaMemo
from app.schemas import IdeaMemoCreate, IdeaMemoRead, IdeaMemoUpdate

router = APIRouter(prefix="/idea-memos", tags=["idea-memos"])


def _get_owned(db: Session, memo_id: UUID, user_id: UUID) -> IdeaMemo:
    memo = db.scalar(
        select(IdeaMemo).where(IdeaMemo.id == memo_id, IdeaMemo.user_id == user_id)
    )
    if memo is None:
        raise HTTPException(status_code=404, detail="备忘录不存在。")
    return memo


@router.get("", response_model=list[IdeaMemoRead])
def list_memos(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[IdeaMemo]:
    return list(
        db.scalars(
            select(IdeaMemo)
            .where(IdeaMemo.user_id == user_id)
            .order_by(IdeaMemo.updated_at.desc(), IdeaMemo.created_at.desc())
        )
    )


@router.post("", response_model=IdeaMemoRead, status_code=status.HTTP_201_CREATED)
def create_memo(
    payload: IdeaMemoCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> IdeaMemo:
    memo = IdeaMemo(user_id=user_id, **payload.model_dump())
    db.add(memo)
    db.commit()
    db.refresh(memo)
    return memo


@router.patch("/{memo_id}", response_model=IdeaMemoRead)
def update_memo(
    memo_id: UUID,
    payload: IdeaMemoUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> IdeaMemo:
    memo = _get_owned(db, memo_id, user_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(memo, key, value)
    db.commit()
    db.refresh(memo)
    return memo


@router.delete("/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memo(
    memo_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    memo = _get_owned(db, memo_id, user_id)
    db.delete(memo)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
