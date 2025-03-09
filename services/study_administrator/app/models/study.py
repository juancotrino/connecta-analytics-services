from datetime import datetime
from pydantic import BaseModel


class Study(BaseModel):
    study_id: int | None = None
    study_name: str | None = None
    study_type: str | None = None
    description: str | None = None
    country: str | None = None
    client: str | None = None
    value: float | None = None
    currency: str | None = None
    creation_date: datetime | None = None
    last_update_date: datetime | None = None
    supervisor: str | None = None
    status: str | None = None
    source: str | None = None
    methodology: str | None = None


class StudyShow(Study): ...


class StudyCreate(Study): ...


class StudyUpdate(Study): ...
