import logging

from fastapi import APIRouter, HTTPException

from app.auth.openemr_auth import get_openemr_auth_manager

router = APIRouter(prefix="/tokens", tags=["tokens"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def token_status():
    manager = get_openemr_auth_manager()
    try:
        await manager.refresh_access_token_if_needed()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to check OpenEMR token status")
        raise HTTPException(status_code=500, detail="Failed to check token status")

    return manager.health()


@router.post("/refresh")
async def token_refresh():
    manager = get_openemr_auth_manager()
    try:
        async with manager._lock:
            manager.access_token = None
            manager.expires_at = None
            await manager._refresh_access_token()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to refresh OpenEMR token")
        raise HTTPException(status_code=500, detail="Failed to refresh token")

    return manager.health()


@router.get("/jwt")
async def token_jwt():
    manager = get_openemr_auth_manager()
    try:
        await manager.refresh_access_token_if_needed()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to load OpenEMR token for JWT decode")
        raise HTTPException(status_code=500, detail="Failed to decode token")

    return manager.decode_jwt(manager.access_token)
