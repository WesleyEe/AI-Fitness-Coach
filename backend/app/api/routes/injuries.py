from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.injury import Injury
from app.models.user import User
from app.schemas.injury import InjuryCreate, InjuryRead, InjuryUpdate

router = APIRouter(prefix="/injuries", tags=["injuries"])


@router.post("", response_model=InjuryRead, status_code=201)
def create_injury(payload: InjuryCreate, db: Session = Depends(get_db)) -> Injury:
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    injury = Injury(**payload.model_dump())
    db.add(injury)
    db.commit()
    db.refresh(injury)
    return injury


@router.get("", response_model=list[InjuryRead])
def list_injuries(user_id: int, db: Session = Depends(get_db)) -> list[Injury]:
    return (
        db.query(Injury)
        .filter(Injury.user_id == user_id)
        .order_by(Injury.date_occurred.desc())
        .all()
    )


@router.get("/{injury_id}", response_model=InjuryRead)
def get_injury(injury_id: int, db: Session = Depends(get_db)) -> Injury:
    injury = db.get(Injury, injury_id)
    if injury is None:
        raise HTTPException(status_code=404, detail="Injury not found")
    return injury


@router.patch("/{injury_id}", response_model=InjuryRead)
def update_injury(injury_id: int, payload: InjuryUpdate, db: Session = Depends(get_db)) -> Injury:
    injury = db.get(Injury, injury_id)
    if injury is None:
        raise HTTPException(status_code=404, detail="Injury not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(injury, field, value)
    db.commit()
    db.refresh(injury)
    return injury
