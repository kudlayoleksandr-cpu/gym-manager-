from models.base_model import BaseModel


class Exercise(BaseModel):
    def __init__(self, id: int, name: str, muscle_group: str, difficulty: str, duration_min: int):
        self.id = id
        self.name = name
        self.muscle_group = muscle_group
        self.difficulty = difficulty
        self.duration_min = duration_min

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'muscle_group': self.muscle_group,
            'difficulty': self.difficulty,
            'duration_min': self.duration_min,
        }
