from flask_login import UserMixin
from models.base_model import BaseModel


class User(UserMixin, BaseModel):
    def __init__(self, id: int, username: str):
        self.id = id
        self.username = username

    def to_dict(self) -> dict:
        return {'id': self.id, 'username': self.username}
