from typing import TYPE_CHECKING
from pytz import timezone
from datetime import datetime
import logging

import pandas as pd

from fastapi import status
from fastapi.exceptions import HTTPException

from app.repositories.auth_repository import AuthRepository
from app.repositories.study_repository import StudyRepository
from app.repositories.business_repository import BusinessRepository
from app.models.study import (
    StudyShow,
    StudyCreate,
    StudyUpdate,
    StudyCountryUpdate,
)

if TYPE_CHECKING:
    from fastapi import UploadFile
    from app.models.user import User

logger = logging.getLogger(__name__)


class StudyService:
    def __init__(self, study_repository: StudyRepository):
        self.study_repository = study_repository
        self.business_repository = BusinessRepository()
        self.auth_repository = AuthRepository()
        self.timezone = timezone("America/Bogota")
        self.countries_iso_2_code = self.business_repository.get_countries_iso_2_code()
        self.study_root_folder_url = "https://connectasas.sharepoint.com/sites/connecta-ciencia_de_datos/Documentos%20compartidos/estudios"
        self.initial_status = "Propuesta"

    def create_study(self, user: "User", study: StudyCreate) -> int:
        study_df = self._build_study_create_entry(user, study)
        self.study_repository.create_study(study_df)
        return study_df["study_id"].unique()[0]

    def get_study(self, study_id: int) -> StudyShow:
        return self.study_repository.get_study(study_id)

    def get_total_studies(self) -> int:
        return self.study_repository.get_total_studies()

    def _get_roles_authorized_columns(
        self, authorized_columns: dict[str, list[str]], user_roles: list[str]
    ) -> list[str]:
        return [
            column
            for column, roles in authorized_columns.items()
            if any(role in roles for role in user_roles)
        ]

    def _filter_columns_by_roles(
        self, studies: list[StudyShow], roles_authorized_columns: list[str]
    ):
        for study in studies:
            all_attributes = set(study.model_fields.keys())
            for column in all_attributes - set(roles_authorized_columns):
                delattr(study, column)
        return studies

    def query_studies(self, limit: int, offset: int, **kwargs) -> list[StudyShow]:
        return self.study_repository.query_studies(limit, offset, **kwargs)

    def query_filtered_studies(
        self, user: "User", limit: int, offset: int, **kwargs
    ) -> tuple[list[str], list[StudyShow]]:
        studies = self.study_repository.query_studies(limit, offset, **kwargs)
        authorized_columns = self.business_repository.get_authorized_columns()
        roles_authorized_columns = self._get_roles_authorized_columns(
            authorized_columns, user.roles
        )
        studies_filtered = self._filter_columns_by_roles(
            studies, roles_authorized_columns
        )
        return roles_authorized_columns, studies_filtered

    def get_all_studies(self) -> list[StudyShow]:
        return self.study_repository.get_studies()

    def update_study(self, study_id: int, study: StudyUpdate, user: "User"):
        study_dict = study.model_dump(exclude={"creation_date"})
        study_dict["study_id"] = study_id

        study_country_folders = {}

        for country in study.countries:
            country.last_update_date = datetime.now(self.timezone)
            # TODO: Create in firestore a document for delegates of each user.
            # Use uuid of the delegate. Create 'delegates' list in users colection
            # for each user
            consultant_delegates = self.auth_repository.get_user_delegates(
                country.consultant
            )
            if (
                user.name != country.consultant
                or user.user_id not in consultant_delegates
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        f"Cannot update study '{study.study_name}' for country "
                        f"'{country.country}'. You are not the study's "
                        "consultant or a consultant's delegate."
                    ),
                )
            if country.status == "En ejecución":
                current_study_data = self.query_studies(
                    50, 0, study_id=study_id, country=country.country
                )
                if (
                    current_study_data
                    and current_study_data[0].status != "En ejecución"
                ):
                    country_code = self.countries_iso_2_code[country.country].lower()
                    id_study_name = (
                        f"{study_id}_{country_code}_"
                        f"{study.study_name.replace(' ', '_').lower()}"
                    )
                    folder_url = f"{self.study_root_folder_url}/{id_study_name}"
                    study_country_folders[country.country] = folder_url
                    try:
                        self.business_repository.create_folder_structure(
                            id_study_name,
                            self.business_repository.sharepoint_base_path,
                        )
                        logger.info(
                            f"Study root folder created successfully for "
                            f"country '{country.country}'. URL: {folder_url}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to create study root folder for country "
                            f"'{country.country}'. Error: {str(e)}"
                        )

            self._send_msteams_card(study_dict, country, study_country_folders)

        study_df = self._build_update_study_entry(study_id, study)
        self.study_repository.update_study(study_id, study_df)

    def delete_study(self, study_id: int):
        self.study_repository.delete_study(study_id)

    def _send_msteams_card(
        self, study_dict: dict, country: StudyCountryUpdate, study_country_folders: dict
    ):
        try:
            study_general_info = {
                k: v for k, v in study_dict.items() if not isinstance(v, list)
            }
            if country.status != self.initial_status:
                study_country = study_general_info | country.model_dump()
                study_country["study_country_folder"] = study_country_folders[
                    country.country
                ]
                self.business_repository.msteams_card_study_status_update(study_country)
                logger.info(
                    "Successfully sent Microsoft Teams card for study_id "
                    f"'{study_dict['study_id']}', country '{country.country}'"
                )
        except Exception as e:
            logger.error(f"Failed to send Microsoft Teams card. Error: {str(e)}")

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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Study does not exist."
            )

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

    def _transform_list_data(self, data: list[dict]) -> list[dict]:
        for element in data:
            for attribute, value in element.items():
                if isinstance(value, list):
                    element[attribute] = ",".join(element[attribute])
        return data

    def _build_update_study_entry(
        self, study_id: int, study: StudyUpdate
    ) -> pd.DataFrame:
        countries = [country.model_dump() for country in study.countries]
        countries = self._transform_list_data(countries)

        study_df = pd.DataFrame(countries)

        study_df["study_id"] = study_id
        study_df["study_name"] = study.study_name
        study_df["client"] = study.client
        study_df["source"] = study.source
        study_df["creation_date"] = study.creation_date

        return study_df

    def _build_study_create_entry(
        self, user: "User", study: StudyCreate
    ) -> pd.DataFrame:
        current_timestamp = datetime.now(self.timezone)

        countries = [country.model_dump() for country in study.countries]
        countries = self._transform_list_data(countries)

        study_df = pd.DataFrame(countries)

        study_df["study_id"] = self.study_repository._get_last_id_number() + 1
        study_df["study_name"] = study.study_name
        study_df["client"] = study.client
        study_df["source"] = study.source
        study_df["creation_date"] = current_timestamp
        study_df["last_update_date"] = current_timestamp
        study_df["status"] = self.initial_status
        study_df["consultant"] = f"{user.user_id}:{user.name}"

        return study_df


def get_study_service():
    study_repository = StudyRepository()
    return StudyService(study_repository)
