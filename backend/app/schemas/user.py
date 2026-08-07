from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    name: str
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    goals: list[str] | None = None
    sports_played: list[str] | None = None
    training_preferences: str | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    goals: list[str] | None = None
    sports_played: list[str] | None = None
    training_preferences: str | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
