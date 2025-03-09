from app.repositories.study_repository import StudyRepository
from app.models.study import StudyShow, StudyCreate, StudyUpdate


class StudyService:
    def __init__(self, study_repository: StudyRepository):
        self.study_repository = study_repository

    def create_study(self, study: StudyCreate):
        self.study_repository.create_study(study)

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


def get_study_service():
    study_repository = StudyRepository()
    return StudyService(study_repository)
