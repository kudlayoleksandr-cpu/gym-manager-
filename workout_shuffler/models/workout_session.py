from models.base_model import BaseModel


class WorkoutSession(BaseModel):
    def __init__(self, id: int, plan_id: int, plan_name: str, date: str, order_used: str):
        self.id = id
        self.plan_id = plan_id
        self.plan_name = plan_name
        self.date = date
        self.order_used = order_used

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'plan_name': self.plan_name,
            'date': self.date,
            'order_used': self.order_used,
        }
