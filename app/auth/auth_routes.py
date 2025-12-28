import logging

from fastapi import APIRouter, HTTPException

from app.auth.openemr_auth import get_openemr_auth_manager

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.get("/openemr/status")
async def openemr_status():
    """Expose non-sensitive OpenEMR token status for observability."""

    manager = get_openemr_auth_manager()
    try:
        await manager.refresh_access_token_if_needed()
    except HTTPException:
        # Propagate API-friendly errors while avoiding leaking secrets.
        raise
    except Exception:
        logger.exception("Unexpected error while checking OpenEMR token status")
        raise HTTPException(status_code=500, detail="Failed to check OpenEMR token status")

    health = manager.health()
    jwt_parts = manager.decode_jwt(manager.access_token)

    return {**health, "jwt": jwt_parts}
