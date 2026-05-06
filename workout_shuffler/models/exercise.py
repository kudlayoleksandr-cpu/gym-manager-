from models.base_model import BaseModel


class Exercise(BaseModel):
    def __init__(self, id: int, name: str, muscle_group: str, difficulty: str, duration_sets: int):
        self.id = id
        self.name = name
        self.muscle_group = muscle_group
        self.difficulty = difficulty
        self.duration_sets = duration_sets

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'muscle_group': self.muscle_group,
            'difficulty': self.difficulty,
            'duration_sets': self.duration_sets,
        }
