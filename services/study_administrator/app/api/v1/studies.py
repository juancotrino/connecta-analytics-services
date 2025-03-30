from typing import TYPE_CHECKING
import logging

from fastapi import APIRouter, Query, HTTPException, Depends, UploadFile, File
from fastapi import status as http_status

from app.models.study import StudyShowTotal, StudyCreate, StudyUpdate
from app.services.study_service import StudyService, get_study_service

from app.dependencies.authentication import get_user
from app.dependencies.authorization import authorize

if TYPE_CHECKING:
    from app.models.user import User

router = APIRouter(
    prefix="/studies",
    tags=["Studies"],
)

logger = logging.getLogger(__name__)


@router.get(
    "/query",
    response_model=StudyShowTotal,
    status_code=http_status.HTTP_200_OK,
    dependencies=[Depends(authorize)],
)
def query_studies(
    limit: int = 50,
    offset: int = 0,
    study_id: list[int] | None = Query(None),
    status: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    client: list[str] | None = Query(None),
    methodology: list[str] | None = Query(None),
    study_type: list[str] | None = Query(None),
    study_service: StudyService = Depends(get_study_service),
    user: "User" = Depends(get_user),
) -> StudyShowTotal:
    kwargs = {
        "study_id": study_id,
        "status": status,
        "country": country,
        "client": client,
        "methodology": methodology,
        "study_type": study_type,
    }

    try:
        studies = study_service.query_filtered_studies(user, limit, offset, **kwargs)
        total_studies = study_service.get_total_studies(**kwargs)
    except Exception as e:
        message = f"Failed to fetch studies: {str(e)}"
        logger.error(message)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )
    return {"total_studies": total_studies, "studies": studies}


@router.post(
    "/create",
    response_model=dict[str, str],
    status_code=http_status.HTTP_201_CREATED,
    dependencies=[Depends(authorize)],
)
def create(
    study: StudyCreate,
    study_service: StudyService = Depends(get_study_service),
) -> dict[str, str]:
    try:
        study_id = study_service.create_study(study)
    except Exception as e:
        message = f"Failed to fetch studies: {str(e)}"
        logger.error(message)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )
    return {"message": f"Study successfully created with ID: {study_id}"}


@router.patch(
    "/update/{study_id}",
    response_model=dict[str, str],
    status_code=http_status.HTTP_200_OK,
    dependencies=[Depends(authorize)],
)
def update(
    study_id: int,
    study: StudyUpdate,
    study_service: StudyService = Depends(get_study_service),
    user: "User" = Depends(get_user),
) -> dict[str, str]:
    try:
        study_service.update_study(study_id, study, user)
    except Exception as e:
        message = f"Failed to fetch studies: {str(e)}"
        logger.error(message)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )
    return {"message": f"Study ID: {study_id}, successfully updated"}


@router.post(
    "/upload_file/{study_id}",
    response_model=dict[str, str],
    status_code=http_status.HTTP_200_OK,
    dependencies=[Depends(authorize)],
)
def upload(
    study_id: int,
    country: str,
    study_name: str,
    file_name: str,
    file: UploadFile = File(...),
    study_service: StudyService = Depends(get_study_service),
    user: "User" = Depends(get_user),
) -> dict[str, str]:
    try:
        study_service.upload_file(
            study_id, country, study_name, file_name, file, user.roles
        )
    except Exception as e:
        message = (
            f"Failed to upload file to study '{study_id}', country '{country}', "
            f"study name '{study_name}'. Error: {str(e)}"
        )
        logger.error(message)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )
    return {"message": f"File uploaded successfully to Study ID: {study_id}"}
