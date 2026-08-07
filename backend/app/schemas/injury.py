from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.injury import InjurySeverity, InjuryStatus


class InjuryBase(BaseModel):
    injury_type: str
    date_occurred: date
    severity: InjurySeverity
    status: InjuryStatus = InjuryStatus.ACTIVE
    recovery_exercises: list[str] | None = None
    restrictions: str | None = None
    related_workout_id: int | None = None


class InjuryCreate(InjuryBase):
    user_id: int


class InjuryUpdate(BaseModel):
    severity: InjurySeverity | None = None
    status: InjuryStatus | None = None
    recovery_exercises: list[str] | None = None
    restrictions: str | None = None


class InjuryRead(InjuryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
