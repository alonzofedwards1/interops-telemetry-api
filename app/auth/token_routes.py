import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.auth.openemr_auth import get_openemr_auth_manager

router = APIRouter(prefix="/tokens", tags=["tokens"])
logger = logging.getLogger(__name__)


class ManualTokenRequest(BaseModel):
    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    scope: Optional[str] = None


class ManualTokenResponse(BaseModel):
    token_present: bool
    expires_in_seconds: Optional[int] = None
    scope: Optional[str] = None


class TokenStatusResponse(BaseModel):
    token_present: bool
    expires_in_seconds: Optional[int] = None
    expires_soon: bool


@router.post("/manual", response_model=ManualTokenResponse)
async def manual_token_fetch(body: ManualTokenRequest) -> ManualTokenResponse:
    manager = get_openemr_auth_manager()

    if not manager.token_url:
        logger.error("OpenEMR token endpoint is not configured")
        raise HTTPException(status_code=500, detail="OpenEMR token endpoint not configured")

    prior_values = {
        "client_id": manager.client_id,
        "client_secret": manager.client_secret,
        "username": manager.username,
        "password": manager.password,
        "scope": manager.scope,
        "user_role": getattr(manager, "user_role", None),
    }

    try:
        async with manager._lock:
            manager.client_id = body.client_id
            manager.client_secret = body.client_secret
            manager.username = body.username
            manager.password = body.password
            manager.scope = body.scope or manager.scope
            manager.user_role = "users"
            await manager._refresh_access_token()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during manual OpenEMR token fetch")
        raise HTTPException(status_code=502, detail="Failed to fetch OpenEMR token")
    finally:
        manager.client_id = prior_values["client_id"]
        manager.client_secret = prior_values["client_secret"]
        manager.username = prior_values["username"]
        manager.password = prior_values["password"]
        manager.scope = manager.scope or prior_values["scope"]
        manager.user_role = prior_values["user_role"]
    health = manager.health()
    return ManualTokenResponse(
        token_present=health["token_present"],
        expires_in_seconds=health["expires_in_seconds"],
        scope=health.get("scope"),
    )


@router.get("/status", response_model=TokenStatusResponse)
async def token_status() -> TokenStatusResponse:
    manager = get_openemr_auth_manager()
    health = manager.health()
    return TokenStatusResponse(
        token_present=health["token_present"],
        expires_in_seconds=health["expires_in_seconds"],
        expires_soon=health["expires_soon"],
    )


@router.post("/refresh")
async def token_refresh():
    manager = get_openemr_auth_manager()
    try:
        async with manager._lock:
            manager.access_token = None
            manager.expires_at = None
            await manager._refresh_access_token()
    except HTTPException as exc:
        raise HTTPException(status_code=502, detail=exc.detail)
    except Exception:
        logger.exception("Failed to refresh OpenEMR token")
        raise HTTPException(status_code=502, detail="Failed to refresh OpenEMR token")

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
