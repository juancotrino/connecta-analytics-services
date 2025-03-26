from app.repositories.business_repository import BusinessRepository


class BusinessService:
    def __init__(self, business_repository: BusinessRepository):
        self.business_repository = business_repository

    def get_business_data(self) -> dict[str, list[str]]:
        return self.business_repository.get_business_data()

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
