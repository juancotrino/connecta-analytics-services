import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi import status as http_status

from app.services.auth_service import AuthService, get_auth_service
from app.models.user import User

from app.dependencies.authentication import get_firebase_user_from_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

logger = logging.getLogger(__name__)


@router.get("/get_custom_token", response_model=str)
def get_custom_token(
    user: User | None = Depends(get_firebase_user_from_token),
    auth_service: AuthService = Depends(get_auth_service),
) -> str:
    try:
        custom_token = auth_service.get_custom_token(user)
    except Exception as e:
        message = f"Failed to create custom token: {str(e)}"
        logger.error(message)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        )
    return custom_token
