from pydantic import BaseModel


class User(BaseModel):
    user_id: str
    name: str
    email: str
    delegates: tuple[str, ...] | None = None
    roles: tuple[str, ...] | None = None
    expiration_date: float | None = None
