import enum
from datetime import date as date_
from datetime import datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ExerciseType(str, enum.Enum):
    STRENGTH = "strength"
    CARDIO = "cardio"
    FOOTBALL = "football"
    HYROX = "hyrox"
    RUNNING = "running"
    MOBILITY = "mobility"
    OTHER = "other"


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    date: Mapped[date_] = mapped_column(Date)
    exercise_type: Mapped[ExerciseType] = mapped_column(Enum(ExerciseType, name="exercise_type"))

    sets: Mapped[int | None] = mapped_column(Integer)
    reps: Mapped[int | None] = mapped_column(Integer)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    duration_minutes: Mapped[float | None] = mapped_column(Numeric(6, 2))
    distance_km: Mapped[float | None] = mapped_column(Numeric(6, 2))
    pace: Mapped[str | None] = mapped_column(String(20))
    heart_rate_avg: Mapped[int | None] = mapped_column(Integer)
    calories: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    football_session: Mapped["FootballSession | None"] = relationship(
        back_populates="workout", uselist=False, cascade="all, delete-orphan"
    )
    hyrox_session: Mapped["HyroxSession | None"] = relationship(
        back_populates="workout", uselist=False, cascade="all, delete-orphan"
    )
    running_session: Mapped["RunningSession | None"] = relationship(
        back_populates="workout", uselist=False, cascade="all, delete-orphan"
    )
