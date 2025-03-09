import logging

from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi import status as http_status

from app.models.study import StudyShow
from app.services.study_service import StudyService, get_study_service


router = APIRouter(
    prefix="/studies",
    tags=["Studies"],
)

logger = logging.getLogger(__name__)


@router.get("/query", response_model=list[StudyShow])
def get_studies(
    limit: int = 50,
    offset: int = 0,
    study_id: list[str] | None = Query(None),
    status: list[str] | None = Query(None),
    country: list[str] | None = Query(None),
    client: list[str] | None = Query(None),
    methodology: list[str] | None = Query(None),
    study_type: list[str] | None = Query(None),
    study_service: StudyService = Depends(get_study_service),
) -> list[StudyShow]:
    kwargs = {
        "study_id": study_id,
        "status": status,
        "country": country,
        "client": client,
        "methodology": methodology,
        "study_type": study_type,
    }

    try:
        studies = study_service.query_studies(limit, offset, **kwargs)
    except Exception as e:
        message = f"Failed to fetch studies: {str(e)}"
        logger.error(message)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )
    return studies
