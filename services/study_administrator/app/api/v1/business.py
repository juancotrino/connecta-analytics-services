from typing import TYPE_CHECKING
import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi import status as http_status

from app.services.business_service import BusinessService, get_business_service
from app.dependencies.authentication import get_user

if TYPE_CHECKING:
    from app.models.user import User

router = APIRouter(
    prefix="/business",
    tags=["Business"],
)

logger = logging.getLogger(__name__)


@router.get("/get_business_data", response_model=dict, dependencies=[Depends(get_user)])
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


@router.get(
    "/get_allowed_files", response_model=dict, status_code=http_status.HTTP_200_OK
)
def get_allowed_files(
    business_service: BusinessService = Depends(get_business_service),
    user: "User" = Depends(get_user),
) -> dict[str, list[str]]:
    try:
        allowed_upload_files = business_service.get_allowed_upload_files(user.roles)
    except Exception as e:
        message = f"Failed to get allowed upload files data: {str(e)}"
        logger.error(message)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )
    return allowed_upload_files
