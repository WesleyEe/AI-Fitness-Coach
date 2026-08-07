from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.football_session import FootballSession
from app.models.hyrox_session import HyroxSession
from app.models.running_session import RunningSession
from app.models.user import User
from app.models.workout import ExerciseType, Workout
from app.schemas.workout import WorkoutCreate, WorkoutRead, WorkoutUpdate

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.post("", response_model=WorkoutRead, status_code=201)
def create_workout(payload: WorkoutCreate, db: Session = Depends(get_db)) -> Workout:
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")

    data = payload.model_dump(exclude={"football", "hyrox", "running"})
    workout = Workout(**data)
    db.add(workout)
    db.flush()  # assigns workout.id without committing yet

    if payload.football is not None:
        workout.football_session = FootballSession(**payload.football.model_dump())
    if payload.hyrox is not None:
        workout.hyrox_session = HyroxSession(**payload.hyrox.model_dump())
    if payload.running is not None:
        workout.running_session = RunningSession(**payload.running.model_dump())

    db.commit()
    db.refresh(workout)
    return workout


@router.get("", response_model=list[WorkoutRead])
def list_workouts(
    user_id: int,
    exercise_type: ExerciseType | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
) -> list[Workout]:
    query = db.query(Workout).filter(Workout.user_id == user_id)
    if exercise_type is not None:
        query = query.filter(Workout.exercise_type == exercise_type)
    if date_from is not None:
        query = query.filter(Workout.date >= date_from)
    if date_to is not None:
        query = query.filter(Workout.date <= date_to)
    return query.order_by(Workout.date.desc()).all()


@router.get("/{workout_id}", response_model=WorkoutRead)
def get_workout(workout_id: int, db: Session = Depends(get_db)) -> Workout:
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.patch("/{workout_id}", response_model=WorkoutRead)
def update_workout(workout_id: int, payload: WorkoutUpdate, db: Session = Depends(get_db)) -> Workout:
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(workout, field, value)
    db.commit()
    db.refresh(workout)
    return workout


@router.delete("/{workout_id}", status_code=204)
def delete_workout(workout_id: int, db: Session = Depends(get_db)) -> None:
    workout = db.get(Workout, workout_id)
    if workout is None:
        raise HTTPException(status_code=404, detail="Workout not found")
    db.delete(workout)
    db.commit()
