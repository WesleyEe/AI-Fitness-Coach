from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class HyroxSession(Base):
    __tablename__ = "hyrox_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(
        ForeignKey("workouts.id", ondelete="CASCADE"), unique=True
    )

    ski_erg_seconds: Mapped[int | None] = mapped_column(Integer)
    sled_push_seconds: Mapped[int | None] = mapped_column(Integer)
    sled_pull_seconds: Mapped[int | None] = mapped_column(Integer)
    burpees_reps: Mapped[int | None] = mapped_column(Integer)
    burpees_seconds: Mapped[int | None] = mapped_column(Integer)
    rowing_seconds: Mapped[int | None] = mapped_column(Integer)
    farmers_carry_seconds: Mapped[int | None] = mapped_column(Integer)
    lunges_reps: Mapped[int | None] = mapped_column(Integer)
    wall_balls_reps: Mapped[int | None] = mapped_column(Integer)
    total_time_seconds: Mapped[int | None] = mapped_column(Integer)

    workout: Mapped["Workout"] = relationship(back_populates="hyrox_session")
