import enum
from datetime import date, datetime

from sqlalchemy import ARRAY, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class InjurySeverity(str, enum.Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class InjuryStatus(str, enum.Enum):
    ACTIVE = "active"
    RECOVERING = "recovering"
    RECOVERED = "recovered"


class Injury(Base):
    __tablename__ = "injuries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    related_workout_id: Mapped[int | None] = mapped_column(
        ForeignKey("workouts.id", ondelete="SET NULL")
    )

    injury_type: Mapped[str] = mapped_column(String(100))
    date_occurred: Mapped[date] = mapped_column(Date)
    severity: Mapped[InjurySeverity] = mapped_column(Enum(InjurySeverity, name="injury_severity"))
    status: Mapped[InjuryStatus] = mapped_column(
        Enum(InjuryStatus, name="injury_status"), default=InjuryStatus.ACTIVE
    )
    recovery_exercises: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    restrictions: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
