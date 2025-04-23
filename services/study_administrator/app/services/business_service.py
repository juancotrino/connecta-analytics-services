import logging

from app.repositories.business_repository import BusinessRepository
from app.repositories.auth_repository import AuthRepository

logger = logging.getLogger(__name__)


class BusinessService:
    def __init__(self, business_repository: BusinessRepository):
        self.business_repository = business_repository
        self.auth_repository = AuthRepository()

    def get_business_data(self) -> dict[str, list[str]]:
        business_data = self.business_repository.get_business_data()
        for i, consultant in enumerate(business_data["consultants"]):
            try:
                consultant_name = self.auth_repository.get_user_name_from_id(consultant)
                business_data["consultants"][i] = consultant_name
            except Exception as e:
                logger.warning(f"Error getting user name from id: {e}")
        return business_data

    def get_authorized_roles_by_endpoint(self, endpoint_path: str):
        return self.business_repository.get_authorized_roles_by_endpoint(endpoint_path)

    def get_allowed_upload_files(self, user_roles: list[str]):
        upload_files = self.business_repository.get_upload_files()
        return self.business_repository.get_allowed_upload_files(
            upload_files, user_roles
        )


def get_business_service():
    business_repository = BusinessRepository()
    return BusinessService(business_repository)
