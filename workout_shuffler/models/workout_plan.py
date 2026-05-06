from __future__ import annotations
from models.base_model import BaseModel
from models.exercise import Exercise


class WorkoutPlan(BaseModel):
    def __init__(self, id: int, name: str, exercises: list[Exercise] = None):
        self.id = id
        self.name = name
        self.exercises: list[Exercise] = exercises or []

    def add_exercise(self, exercise: Exercise) -> None:
        self.exercises.append(exercise)

    def remove_exercise(self, exercise_id: int) -> None:
        self.exercises = [e for e in self.exercises if e.id != exercise_id]

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'exercises': [e.to_dict() for e in self.exercises],
        }
