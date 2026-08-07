from datetime import date as date_
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.workout import ExerciseType


class FootballSessionBase(BaseModel):
    position: str | None = None
    match_duration_minutes: int | None = None
    intensity: str | None = None
    performance_notes: str | None = None
    injuries_flagged: bool = False
    areas_for_improvement: str | None = None


class FootballSessionRead(FootballSessionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class HyroxSessionBase(BaseModel):
    ski_erg_seconds: int | None = None
    sled_push_seconds: int | None = None
    sled_pull_seconds: int | None = None
    burpees_reps: int | None = None
    burpees_seconds: int | None = None
    rowing_seconds: int | None = None
    farmers_carry_seconds: int | None = None
    lunges_reps: int | None = None
    wall_balls_reps: int | None = None
    total_time_seconds: int | None = None


class HyroxSessionRead(HyroxSessionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RunningSessionBase(BaseModel):
    distance_km: float | None = None
    pace_per_km: str | None = None
    vo2max_estimate: float | None = None
    avg_heart_rate: int | None = None


class RunningSessionRead(RunningSessionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class WorkoutBase(BaseModel):
    date: date_
    exercise_type: ExerciseType
    sets: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    duration_minutes: float | None = None
    distance_km: float | None = None
    pace: str | None = None
    heart_rate_avg: int | None = None
    calories: int | None = None
    notes: str | None = None


class WorkoutCreate(WorkoutBase):
    user_id: int
    football: FootballSessionBase | None = None
    hyrox: HyroxSessionBase | None = None
    running: RunningSessionBase | None = None


class WorkoutUpdate(BaseModel):
    date: date_ | None = None
    sets: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    duration_minutes: float | None = None
    distance_km: float | None = None
    pace: str | None = None
    heart_rate_avg: int | None = None
    calories: int | None = None
    notes: str | None = None


class WorkoutRead(WorkoutBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    football_session: FootballSessionRead | None = None
    hyrox_session: HyroxSessionRead | None = None
    running_session: RunningSessionRead | None = None
