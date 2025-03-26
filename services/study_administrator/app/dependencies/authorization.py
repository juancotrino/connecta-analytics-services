from typing import TYPE_CHECKING

from fastapi import Request, Depends, status, Security
from fastapi.exceptions import HTTPException

from app.services.business_service import BusinessService, get_business_service
from app.dependencies.authentication import get_user

if TYPE_CHECKING:
    from app.models.user import User


async def authorize(
    request: Request,
    business_service: BusinessService = Depends(get_business_service),
    user: "User" = Security(get_user),
):
    """Authorize user based on Firestore role mapping."""
    try:
        endpoint_path = request.url.path.split("/")[4]
        authorized_roles = business_service.get_authorized_roles_by_endpoint(
            endpoint_path
        )

        if not any(role in authorized_roles for role in user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Insufficient permissions",
            )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"An error occurred authorizing the user: {str(e)}",
        )

    return True
