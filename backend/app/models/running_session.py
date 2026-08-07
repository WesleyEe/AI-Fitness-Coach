from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RunningSession(Base):
    __tablename__ = "running_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.id", ondelete="CASCADE"), unique=True
    )

    distance_km: Mapped[float | None] = mapped_column(Numeric(6, 2))
    pace_per_km: Mapped[str | None] = mapped_column(String(20))
    vo2max_estimate: Mapped[float | None] = mapped_column(Numeric(4, 1))
    avg_heart_rate: Mapped[int | None] = mapped_column(Integer)

    workout: Mapped["Workout"] = relationship(back_populates="running_session")
