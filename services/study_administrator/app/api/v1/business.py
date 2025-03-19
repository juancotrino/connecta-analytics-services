import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi import status as http_status

from app.services.business_service import BusinessService, get_business_service

router = APIRouter(
    prefix="/business",
    tags=["Business"],
)

logger = logging.getLogger(__name__)


@router.get("/get_business_data", response_model=dict)
def get_business_data(
    business_service: BusinessService = Depends(get_business_service),
) -> dict[str, list[str]]:
    try:
        business_data = business_service.get_business_data()
    except Exception as e:
        message = f"Failed to get business data: {str(e)}"
        logger.error(message)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )
    return business_data
