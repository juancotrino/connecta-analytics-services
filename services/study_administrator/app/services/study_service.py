import itertools
from pytz import timezone
from datetime import datetime

import pandas as pd

from app.repositories.study_repository import StudyRepository
from app.models.study import StudyShow, StudyCreate, StudyUpdate


class StudyService:
    def __init__(self, study_repository: StudyRepository):
        self.study_repository = study_repository
        self.timezone = timezone("America/Bogota")

    def create_study(self, study: StudyCreate) -> int:
        study_df = self._build_study_entry(study)
        self.study_repository.create_study(study_df)
        return study_df["study_id"].unique()[0]

    def get_study(self, study_id: int) -> StudyShow:
        return self.study_repository.get_study(study_id)

    def query_studies(self, limit: int, offset: int, **kwargs) -> list[StudyShow]:
        return self.study_repository.query_studies(limit, offset, **kwargs)

    def get_all_studies(self) -> list[StudyShow]:
        return self.study_repository.get_studies()

    def update_study(self, study: StudyUpdate):
        self.study_repository.update_study(study)

    def delete_study(self, study_id: int):
        self.study_repository.delete_study(study_id)

    def _build_study_entry(self, study: StudyCreate) -> pd.DataFrame:
        combinations = list(
            itertools.product(study.methodology, study.study_type, study.country)
        )
        study_id = self.study_repository._get_last_id_number() + 1
        current_timestamp = datetime.now(self.timezone)
        initial_status = "Propuesta"
        source = "app"
        study_entry = {
            "study_id": [study_id] * len(combinations),
            "study_name": [study.study_name] * len(combinations),
            "methodology": [combination[0] for combination in combinations],
            "study_type": [combination[1] for combination in combinations],
            "description": [study.description] * len(combinations),
            "country": [combination[2] for combination in combinations],
            "client": [study.client] * len(combinations),
            "value": [study.value] * len(combinations),
            "currency": [study.currency] * len(combinations),
            "supervisor": [study.supervisor] * len(combinations),
            "status": [initial_status] * len(combinations),
            "source": [source] * len(combinations),
            "creation_date": [current_timestamp] * len(combinations),
            "last_update_date": [current_timestamp] * len(combinations),
        }
        return pd.DataFrame(study_entry)


def get_study_service():
    study_repository = StudyRepository()
    return StudyService(study_repository)
