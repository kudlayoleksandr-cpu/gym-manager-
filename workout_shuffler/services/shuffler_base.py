from abc import ABC, abstractmethod
from models.workout_plan import WorkoutPlan


class BaseShuffler(ABC):
    @abstractmethod
    def shuffle(self, plan: WorkoutPlan, history: list) -> list[str]:
        pass
