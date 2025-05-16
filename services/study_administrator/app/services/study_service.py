from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo
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
        self.timezone = ZoneInfo("America/Bogota")
        self.countries_iso_2_code = self.business_repository.get_countries_iso_2_code()
        self.study_root_folder_url = "https://connectasas.sharepoint.com/sites/connecta-ciencia_de_datos/Documentos%20compartidos/estudios"
        self.initial_status = "Propuesta"

    def create_study(self, study: StudyCreate) -> int:
        study_df = self._build_study_create_entry(study)
        self.study_repository.create_study(study_df)
        return study_df["study_id"].unique()[0]

    def get_study(self, study_id: int) -> StudyShow:
        return self.study_repository.get_study(study_id)

    def get_total_studies(self, **kwargs) -> int:
        return self.study_repository.get_total_studies(**kwargs)

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

    def _get_naive_datetime(self, value: datetime) -> datetime:
        # First make the naive datetime UTC-aware
        utc_dt = value.replace(tzinfo=ZoneInfo("UTC"))
        # Then convert to target timezone
        converted = utc_dt.astimezone(self.timezone)
        # Finally make it naive again
        return converted.replace(tzinfo=None)

    def _convert_datetime_fields_to_timezone(self, study: StudyShow) -> None:
        """
        Convert all datetime fields in an object to the specified timezone.

        Args:
            obj: The object whose datetime fields should be converted
        """
        for attr_name, attr_value in study.model_dump().items():
            if isinstance(attr_value, datetime):
                naive_datetime = self._get_naive_datetime(attr_value)
                setattr(study, attr_name, naive_datetime)

    def query_studies(self, limit: int, offset: int, **kwargs) -> list[StudyShow]:
        studies = self.study_repository.query_studies(limit, offset, **kwargs)
        for study in studies:
            self._convert_datetime_fields_to_timezone(study)
        return studies

    def _postprocess_studies(self, studies: list[StudyShow]) -> list[StudyShow]:
        for study in studies:
            try:
                study.consultant = self.auth_repository.get_user_name_from_id(
                    study.consultant
                )
            except Exception as e:
                logger.warning(f"Error getting user name from id: {e}")
        return studies

    def query_filtered_studies(
        self, user: "User", limit: int, offset: int, **kwargs
    ) -> tuple[list[str], list[StudyShow]]:
        studies = self.query_studies(limit, offset, **kwargs)
        authorized_columns = self.business_repository.get_authorized_columns()
        roles_authorized_columns = self._get_roles_authorized_columns(
            authorized_columns, user.roles
        )
        studies_filtered = self._filter_columns_by_roles(
            studies, roles_authorized_columns
        )
        studies_filtered = self._postprocess_studies(studies_filtered)
        return roles_authorized_columns, studies_filtered

    def get_all_studies(self) -> list[StudyShow]:
        return self.study_repository.get_studies()

    def _get_consultant_id(self, consultant: str) -> str:
        consultant_id = self.auth_repository.get_user_id_from_name(consultant)
        if not consultant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultant not found.",
            )
        return consultant_id

    def _compose_current_study_df(
        self, current_study_data: list[StudyShow]
    ) -> pd.DataFrame:
        current_study_dicts = [data.model_dump() for data in current_study_data]
        for i, current_study_dict in enumerate(current_study_dicts):
            current_study_dicts[i] = {
                k: v if not isinstance(v, list) else ",".join(v)
                for k, v in current_study_dict.items()
            }
        return (
            pd.DataFrame(current_study_dicts)
            .sort_values(by="country")
            .reset_index(drop=True)
            .T.sort_index()
        )

    def _compose_new_study_df(
        self, study_id: int, new_study_data: StudyUpdate
    ) -> pd.DataFrame:
        return (
            self._build_update_study_entry(study_id, new_study_data)
            .sort_values(by="country")
            .reset_index(drop=True)
            .T.sort_index()
        )

    def _is_updated(
        self,
        country: str,
        current_study_df: pd.DataFrame,
        new_study_df: pd.DataFrame,
    ) -> bool:
        current_study_df = current_study_df.T
        current_study_df = (
            current_study_df[current_study_df["country"] == country]
            .reset_index(drop=True)
            .T.sort_index()
        )
        if current_study_df.empty:
            return False
        new_study_df = new_study_df.T
        new_study_df = (
            new_study_df[new_study_df["country"] == country]
            .reset_index(drop=True)
            .T.sort_index()
        )
        return not current_study_df.equals(new_study_df)

    def _check_deleted(
        self, user: "User", current_study_df: pd.DataFrame, new_study_df: pd.DataFrame
    ) -> bool:
        current_study_df = current_study_df.T
        new_study_df = new_study_df.T
        if len(current_study_df) > len(new_study_df):
            for country in current_study_df["country"].values:
                if country in new_study_df["country"].values:
                    continue
                country_df = current_study_df[
                    current_study_df["country"] == country
                ].reset_index(drop=True)
                consultant_id = country_df["consultant"][0]
                consultant_delegates = self.auth_repository.get_user_delegates(
                    consultant_id
                )
                if (
                    user.user_id != consultant_id
                    and user.user_id not in consultant_delegates
                    and country not in new_study_df["country"].values
                ):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=(
                            f"Cannot update study '{country_df['study_name'][0]}' "
                            f"for country '{country}'. You are not the "
                            "study's consultant or a consultant's delegate."
                        ),
                    )

    def _get_current_consultant(
        self, country: str, current_study_df: pd.DataFrame
    ) -> str:
        return current_study_df.T[current_study_df.T["country"] == country].reset_index(
            drop=True
        )["consultant"][0]

    def update_study(self, study_id: int, study: StudyUpdate, user: "User"):
        study_dict = study.model_dump()
        study_dict["study_id"] = study_id

        current_study_data = self.query_studies(50, 0, study_id=study_id)
        current_study_df = self._compose_current_study_df(current_study_data)
        new_study_df = self._compose_new_study_df(study_id, study)
        self._check_deleted(user, current_study_df, new_study_df)

        for country in study.countries:
            if country.country in current_study_df.T["country"].values:
                consultant_id = self._get_current_consultant(
                    country.country, current_study_df
                )
            else:
                consultant_id = self._get_consultant_id(country.consultant)

            consultant_delegates = self.auth_repository.get_user_delegates(
                consultant_id
            )
            is_updated = self._is_updated(
                country.country, current_study_df, new_study_df
            )

            if not is_updated:
                continue

            if (
                user.name != country.consultant
                and user.user_id not in consultant_delegates
                and is_updated
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        f"Cannot update study '{study.study_name}' for country "
                        f"'{country.country}'. You are not the study's "
                        "consultant or a consultant's delegate."
                    ),
                )

            current_study_country_data = [
                study_country
                for study_country in current_study_data
                if study_country.country == country.country
            ]

            if country.status != self.initial_status:
                if (
                    current_study_country_data
                    and current_study_country_data[0].status == self.initial_status
                ):
                    country_code = self.countries_iso_2_code[country.country].lower()
                    id_study_name = (
                        f"{study_id}_{country_code}_"
                        f"{study.study_name.replace(' ', '_').lower()}"
                    )

                    folder_url = f"{self.study_root_folder_url}/{id_study_name}"

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

                    self._send_msteams_card(study_dict, country, folder_url)

        study_df = self._build_update_study_entry(study_id, study)
        self.study_repository.update_study(study_id, study_df)

    def delete_study(self, study_id: int):
        self.study_repository.delete_study(study_id)

    def _send_msteams_card(
        self, study_dict: dict, country: StudyCountryUpdate, folder_url: str
    ):
        try:
            study_general_info = {
                k: v for k, v in study_dict.items() if not isinstance(v, list)
            }
            if country.status != self.initial_status:
                study_country = study_general_info | country.model_dump()
                study_country["study_country_folder"] = folder_url
                for attribute, value in study_country.items():
                    if isinstance(value, datetime):
                        study_country[attribute] = value.strftime("%d/%m/%Y %H:%M:%S")
                self.business_repository.msteams_card_study_status_update(study_country)
                logger.info(
                    "Successfully sent Microsoft Teams card for study_id "
                    f"'{study_dict['study_id']}', country '{country.country}'"
                )
        except Exception as e:
            logger.error(f"Failed to send Microsoft Teams card. Error: {str(e)}")

    def _get_existing_study(self, **kwargs: dict) -> list[StudyShow]:
        return self.query_studies(1, 0, **kwargs)

    def upload_file(
        self,
        study_id: int,
        country: str,
        study_name: str,
        file_name: str,
        file: "UploadFile",
        user: "User",
    ) -> None:
        existing_study = self._get_existing_study(
            study_id=study_id, country=country, study_name=study_name
        )
        if not existing_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Study does not exist."
            )

        if file_name != "proposal" and existing_study[0].status == self.initial_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "You cannot upload the selected file to a "
                    "study that is not in the initial status"
                ),
            )

        upload_files = self.business_repository.get_upload_files()
        allowed_upload_files = self.business_repository.get_allowed_upload_files(
            upload_files, user.roles
        )
        if file_name not in allowed_upload_files:
            raise PermissionError(
                "You are not authorized to upload this file or the file does not exist"
            )

        study_path_name = self._build_study_path_name(study_id, country, study_name)
        upload_file_data = allowed_upload_files[file_name]

        if existing_study[0].status == self.initial_status and file_name == "proposal":
            full_relative_path = self.business_repository.sharepoint_proposal_path
            new_file_name = self.business_repository.compose_file_name(
                upload_file_data,
                file.filename,
                study_path_name,
                status=self.initial_status,
            )
        else:
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

        if upload_files[file_name]["msteams_card"]:
            ms_teams_study_info = {
                "study_id": study_id,
                "study_name": study_name,
                "country": country,
                "file_name": new_file_name,
                "author": user.name,
                "file_folder": f"{self.study_root_folder_url}/{study_path_name}/{upload_file_data['path']}",
            }
            try:
                self.business_repository.msteams_card_file_update(
                    file_name, ms_teams_study_info
                )
            except AttributeError as e:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        f"Error sending MSTeams Card for study id: '{study_id}', "
                        f"study name: {study_name}, country: {country}, file: {file_name}. "
                        f"Error: {str(e)}"
                    ),
                )

        return (
            f"{self.study_root_folder_url}/{study_path_name}/{upload_file_data['path']}"
        )

    def _build_study_path_name(
        self, study_id: int, country: str, study_name: str
    ) -> str:
        country_code = self.countries_iso_2_code[country]
        return (
            f"{study_id}_{country_code.lower()}_{study_name.replace(' ', '_').lower()}"
        )

    def _transform_data(self, data: list[dict]) -> list[dict]:
        for element in data:
            for attribute, value in element.items():
                if attribute == "consultant":
                    element[attribute] = self._get_consultant_id(value)
                if attribute in ("last_update_date", "creation_date"):
                    if value is None:
                        element[attribute] = datetime.now(ZoneInfo("UTC")).replace(
                            tzinfo=None
                        )
                    elif isinstance(value, datetime):
                        element[attribute] = (
                            value.replace(tzinfo=self.timezone)
                            .astimezone(ZoneInfo("UTC"))
                            .replace(tzinfo=None)
                        )
                if isinstance(value, list):
                    joined_value = ",".join(value)
                    element[attribute] = joined_value if joined_value else None
        return data

    def _build_update_study_entry(
        self, study_id: int, study: StudyUpdate
    ) -> pd.DataFrame:
        countries = [country.model_dump() for country in study.countries]
        countries = self._transform_data(countries)

        study_df = pd.DataFrame(countries)

        study_df["study_id"] = study_id
        study_df["study_name"] = study.study_name
        study_df["client"] = study.client
        study_df["source"] = study.source

        return study_df

    def _build_study_create_entry(self, study: StudyCreate) -> pd.DataFrame:
        current_timestamp = datetime.now(ZoneInfo("UTC")).replace(tzinfo=None)

        countries = [country.model_dump() for country in study.countries]
        countries = self._transform_data(countries)

        study_df = pd.DataFrame(countries)

        study_df["study_id"] = self.study_repository._get_last_id_number() + 1
        study_df["study_name"] = study.study_name
        study_df["client"] = study.client
        study_df["source"] = study.source
        study_df["creation_date"] = current_timestamp
        study_df["last_update_date"] = current_timestamp
        study_df["status"] = self.initial_status

        return study_df


def get_study_service():
    study_repository = StudyRepository()
    return StudyService(study_repository)
