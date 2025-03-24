from typing_extensions import Annotated
from datetime import datetime
from pydantic import BaseModel, BeforeValidator
from app.models.validators import ensure_list


class StudyCountry(BaseModel):
    country: str | None = None
    methodology: list[str] | None = None
    study_type: list[str] | None = None
    value: float | None = None
    currency: str | None = None
    consultant: str | None = None
    description: str | None = None


class StudyCountryCreate(BaseModel):
    country: str
    methodology: list[str] | None = None
    study_type: list[str] | None = None
    value: float | None = None
    currency: str | None = None
    consultant: str | None = None
    description: str | None = None


class StudyCountryUpdate(BaseModel):
    country: str
    methodology: list[str] | None = None
    study_type: list[str] | None = None
    value: float | None = None
    currency: str | None = None
    consultant: str | None = None
    description: str | None = None
    status: str | None = None


class Study(BaseModel):
    study_id: int | None = None
    study_name: str | None = None
    client: str | None = None
    source: str | None = None
    countries: list[StudyCountry] | None = None


class StudyShow(BaseModel):
    study_id: int | None = None
    country: str | None = None
    client: str | None = None
    study_name: str | None = None
    study_type: Annotated[list[str] | None, BeforeValidator(ensure_list)]
    methodology: Annotated[list[str] | None, BeforeValidator(ensure_list)]
    description: str | None = None
    value: float | None = None
    currency: str | None = None
    consultant: str | None = None
    status: str | None = None
    source: str | None = None
    creation_date: datetime | None = None
    last_update_date: datetime | None = None


class StudyShowTotal(BaseModel):
    total_studies: int
    studies: list[StudyShow]


class StudyCreate(BaseModel):
    study_name: str
    client: str
    source: str | None = "app"
    countries: list[StudyCountryCreate]


class StudyUpdate(BaseModel):
    study_name: str
    client: str
    source: str | None = "app"
    creation_date: datetime
    countries: list[StudyCountryUpdate]
