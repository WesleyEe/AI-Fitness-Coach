from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class FootballSession(Base):
    __tablename__ = "football_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.id", ondelete="CASCADE"), unique=True
    )

    position: Mapped[str | None] = mapped_column(String(50))
    match_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    intensity: Mapped[str | None] = mapped_column(String(20))
    performance_notes: Mapped[str | None] = mapped_column(Text)
    injuries_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    areas_for_improvement: Mapped[str | None] = mapped_column(Text)

    workout: Mapped["Workout"] = relationship(back_populates="football_session")
