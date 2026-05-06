class BaseModel:
    id: int = None

    def to_dict(self) -> dict:
        raise NotImplementedError
