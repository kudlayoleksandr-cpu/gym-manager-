import random
from services.shuffler_base import BaseShuffler
from models.workout_plan import WorkoutPlan


class RandomShuffler(BaseShuffler):
    def shuffle(self, plan: WorkoutPlan, history: list) -> list[str]:
        names = [e.name for e in plan.exercises]
        random.shuffle(names)
        return names
