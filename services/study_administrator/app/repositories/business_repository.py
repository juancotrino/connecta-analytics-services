from typing import TYPE_CHECKING
import os
import requests

from firebase_admin import firestore

from app.core.sharepoint import SharePoint
from app.core.teams import (
    TeamsWebhook,
    AdaptiveCard,
    Container,
    FactSet,
    ContainerStyle,
    TextWeight,
    TextSize,
)
from app.core.firebase import FirebaseAdmin

if TYPE_CHECKING:
    from io import BytesIO


class BusinessRepository:
    def __init__(self):
        self.MS_TEAMS_WEBHOOK_STUDY_STATUS_UPDATE = os.getenv(
            "MS_TEAMS_WEBHOOK_STUDY_STATUS_UPDATE"
        )
        self._firebase = FirebaseAdmin(os.getenv("GCP_PROJECT_ID"))
        self.sharepoint = SharePoint()
        self.db = firestore.client()
        self.sharepoint_base_path = "Documentos compartidos/estudios"

    def get_countries_iso_2_code(self) -> dict[str, str]:
        url = "https://api.worldbank.org/v2/country?format=json&per_page=300&region=LCN"

        response = requests.get(url)

        if response.status_code == 200:
            countries_info = response.json()[1]

            country_names = [
                country["name"]
                for country in countries_info
                if "Latin America & Caribbean" in country["region"]["value"]
            ]
            countries_iso_2_code = {
                country["name"]: country["iso2Code"]
                for country in countries_info
                if country["name"] in country_names
            }

            return countries_iso_2_code

        else:
            return {"Colombia": "CO", "Mexico": "MX", "Ecuador": "EC", "Peru": "PE"}

    def get_business_data(self) -> dict[str, list[str]]:
        document = self.db.collection("settings").document("business_data").get()

        if document.exists:
            business_data = document.to_dict()
            return business_data

    def get_authorized_roles_by_endpoint(self, endpoint_path: str):
        document = (
            self.db.collection("cloudrun_services")
            .document("study_administrator")
            .get()
        )

        if document.exists:
            endpoints = document.to_dict()["endpoints"]
            if endpoint_path not in endpoints:
                raise KeyError(f"No roles for endpoint '{endpoint_path}' are set.")
            return endpoints[endpoint_path]["authorized_roles"]

    def get_upload_files(self) -> dict[str, list[str]]:
        document = self.db.collection("settings").document("upload_files").get()

        if document.exists:
            upload_files = document.to_dict()
            return upload_files

    def get_allowed_upload_files(
        self, upload_files: dict, user_roles: list[str]
    ) -> dict[str, list[str]]:
        filtered_files = {
            file_name: details
            for file_name, details in upload_files.items()
            if any(role in details["authorized_roles"] for role in user_roles)
        }
        return filtered_files

    def create_folder_structure(self, id_study_name: str, base_path: str) -> None:
        business_data = self.get_business_data()
        dirs = business_data["sharepoint_folder_structure"]
        self.check_study_id_sharepoint(id_study_name, base_path)
        study_path = f"{base_path}/{id_study_name}"
        self.sharepoint.create_folder_structure(study_path, dirs)

    def get_last_file_version_in_sharepoint(
        self, id_study_name: str, file_path: str
    ) -> list[str]:
        return self.sharepoint.list_files(
            f"{self.sharepoint_base_path}/{id_study_name}/{file_path}"
        )

    def compose_file_name(
        self,
        upload_files: dict[str, str | list[str]],
        file_name: str,
        id_study_name: str,
    ) -> str:
        file_path = upload_files["path"]
        file_type = file_name.split(".")[-1]
        allowed_file_types = upload_files["file_type"].split(",")
        if file_type not in allowed_file_types:
            raise ValueError("File type not allowed")
        if upload_files["acronym"] and upload_files["file_type"]:
            files = self.get_last_file_version_in_sharepoint(id_study_name, file_path)
            files = [file for file in files if upload_files["acronym"] in file]
            if not files:
                composed_file_name = (
                    f"{id_study_name}_{upload_files['acronym']}_V1.{file_type}"
                )
            else:
                last_version_number = max(
                    int(file.split("_")[-1].split(".")[0].replace("V", ""))
                    for file in files
                )
                composed_file_name = f"{id_study_name}_{upload_files['acronym']}_V{last_version_number + 1}.{file_type}"
        else:
            composed_file_name = file_name

        return composed_file_name

    def upload_file(
        self, full_relative_path: str, file_content: "BytesIO", file_name: str
    ) -> None:
        self.sharepoint.upload_file(full_relative_path, file_content, file_name)

    def check_study_id_sharepoint(self, id_project_name: str, base_path: str) -> None:
        studies_in_sharepoint = self.sharepoint.list_folders(base_path)

        if id_project_name in studies_in_sharepoint:
            raise NameError("Combination of ID, country and study name alreday exists.")

    def msteams_card_study_status_update(self, study_info: dict[str, str]):
        webhook = TeamsWebhook(os.getenv("MS_TEAMS_WEBHOOK_STUDY_STATUS_UPDATE"))

        card = AdaptiveCard(
            title="**STUDY STATUS UPDATE**", title_style=ContainerStyle.DEFAULT
        )

        container = Container(style=ContainerStyle.DEFAULT)

        container.add_text_block(
            f"Study **{study_info['study_id']} {study_info['study_name']}** for country **{study_info['country']}** changed its status to **{study_info['status']}** with these specifications:",
            size=TextSize.DEFAULT,
            weight=TextWeight.DEFAULT,
            color="default",
        )

        factset = FactSet()
        for k, v in study_info.items():
            if k not in ("study_country_folder", "source"):
                if isinstance(v, list):
                    v = ", ".join(v)
                factset.add_facts((f"**{k.replace('_', ' ').capitalize()}**:", v))

        container.add_fact_set(factset)

        card.add_container(container)

        card.add_url_button(
            f"{study_info['country']} study proposal folder",
            f"{study_info['study_country_folder']}/consultoria/propuestas",
        )

        webhook.add_cards(card)
        webhook.send()
