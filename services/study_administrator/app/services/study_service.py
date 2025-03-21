from typing import TYPE_CHECKING
import itertools
from pytz import timezone
from datetime import datetime
import logging

import pandas as pd

from app.repositories.study_repository import StudyRepository
from app.repositories.business_repository import BusinessRepository
from app.models.study import StudyShow, StudyCreate, StudyUpdate

if TYPE_CHECKING:
    from fastapi import UploadFile

logger = logging.getLogger(__name__)


class StudyService:
    def __init__(self, study_repository: StudyRepository):
        self.study_repository = study_repository
        self.business_repository = BusinessRepository()
        self.timezone = timezone("America/Bogota")
        self.countries_iso_2_code = self.business_repository.get_countries_iso_2_code()
        self.study_root_folder_url = "https://connectasas.sharepoint.com/sites/connecta-ciencia_de_datos/Documentos%20compartidos/estudios"

    def create_study(self, study: StudyCreate) -> int:
        study_df = self._build_study_entry(study)
        self.study_repository.create_study(study_df)
        return study_df["study_id"].unique()[0]

    def get_study(self, study_id: int) -> StudyShow:
        return self.study_repository.get_study(study_id)

    def get_total_studies(self) -> int:
        return self.study_repository.get_total_studies()

    def query_studies(self, limit: int, offset: int, **kwargs) -> list[StudyShow]:
        return self.study_repository.query_studies(limit, offset, **kwargs)

    def get_all_studies(self) -> list[StudyShow]:
        return self.study_repository.get_studies()

    def update_study(self, study_id: int, study: StudyUpdate):
        if study.status == "En ejecución":
            current_study_data = self.query_studies(50, 0, study_id=study_id)
            if current_study_data and current_study_data[0].status != "En ejecución":
                countries_folders = {}
                for country in study.country:
                    country_code = self.countries_iso_2_code[country].lower()
                    id_study_name = f"{study_id}_{country_code}_{study.study_name.replace(' ', '_').lower()}"
                    try:
                        self.business_repository.create_folder_structure(
                            id_study_name, self.business_repository.sharepoint_base_path
                        )
                        folder_url = f"{self.study_root_folder_url}/{id_study_name}"
                        countries_folders[country] = folder_url
                        logger.info(
                            f"Study root folder created successfully for country '{country}'. URL: {folder_url}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to create study root folder for country '{country}': {str(e)}"
                        )

                try:
                    self.business_repository.msteams_card_study_status_update(
                        {
                            "study_id": study_id,
                            "study_name": study.study_name,
                            "methodology": ", ".join(study.methodology),
                            "study_type": ", ".join(study.study_type),
                            "description": study.description,
                            "country": ", ".join(study.country),
                            "client": study.client,
                            "value": f"{'{:,}'.format(study.value).replace(',', '.')} {study.currency}",
                            "consultant": study.supervisor,
                            "status": study.status,
                            "study_folder": countries_folders,
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send Microsoft Teams card: {str(e)}")

        study_df = self._build_update_study_entry(study_id, study)
        self.study_repository.update_study(study_id, study_df)

    def delete_study(self, study_id: int):
        self.study_repository.delete_study(study_id)

    def _check_study_exists(self, **kwargs: dict) -> bool:
        return self.query_studies(1, 0, **kwargs) != []

    def upload_file(
        self,
        study_id: int,
        country: str,
        study_name: str,
        file_name: str,
        file: "UploadFile",
        user_roles: list[str],
    ) -> None:
        study_exists = self._check_study_exists(
            study_id=study_id, country=country, study_name=study_name
        )
        if not study_exists:
            raise ValueError("Study does not exist")

        upload_files = self.business_repository.get_upload_files()
        allowed_upload_files = self.business_repository.get_allowed_upload_files(
            upload_files, user_roles
        )
        if file_name not in allowed_upload_files:
            raise PermissionError(
                "You are not authorized to upload this file or the file does not exist"
            )

        study_path_name = self._build_study_path_name(study_id, country, study_name)
        upload_file_data = allowed_upload_files[file_name]

        full_relative_path = (
            f"{self.business_repository.sharepoint_base_path}/"
            f"{study_path_name}/{upload_file_data['path']}"
        )

        new_file_name = self.business_repository.compose_file_name(
            upload_file_data, file.filename, study_path_name
        )

        self.business_repository.upload_file(
            full_relative_path, file.file, new_file_name
        )

    def _build_study_path_name(
        self, study_id: int, country: str, study_name: str
    ) -> str:
        country_code = self.countries_iso_2_code[country]
        return (
            f"{study_id}_{country_code.lower()}_{study_name.replace(' ', '_').lower()}"
        )

    def _build_update_study_entry(
        self, study_id: int, study: StudyUpdate
    ) -> pd.DataFrame:
        combinations = list(
            itertools.product(study.methodology, study.study_type, study.country)
        )
        current_timestamp = datetime.now(self.timezone)
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
            "status": [study.status] * len(combinations),
            "source": [study.source] * len(combinations),
            "creation_date": [study.creation_date] * len(combinations),
            "last_update_date": [current_timestamp] * len(combinations),
        }
        return pd.DataFrame(study_entry)

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
