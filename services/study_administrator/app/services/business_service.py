from app.repositories.business_repository import BusinessRepository


class BusinessService:
    def __init__(self, business_repository: BusinessRepository):
        self.business_repository = business_repository

    def get_business_data(self) -> dict[str, dict]:
        return self.business_repository.get_business_data()


def get_business_service():
    business_repository = BusinessRepository()
    return BusinessService(business_repository)
