import logging
import time
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
    status: str
    expires_in: int
    scope: Optional[str] = None


class TokenStatusResponse(BaseModel):
    token_present: bool
    expires_in: Optional[int] = None
    expires_at: Optional[int] = None
    scope: Optional[str] = None


@router.post("/manual")
async def manual_token_fetch(body: ManualTokenRequest) -> ManualTokenResponse:
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover - environment guardrail
        logger.error("httpx is required for manual OpenEMR token fetch; install from requirements.txt")
        raise HTTPException(status_code=500, detail="httpx dependency missing") from exc

    manager = get_openemr_auth_manager()

    if not manager.token_url:
        logger.error("OpenEMR token endpoint is not configured")
        raise HTTPException(status_code=500, detail="OpenEMR token endpoint not configured")

    payload = {
        "grant_type": "password",
        "client_id": body.client_id,
        "client_secret": body.client_secret,
        "username": body.username,
        "password": body.password,
        "user_role": "users",
    }

    if body.scope:
        payload["scope"] = body.scope

    try:
        async with manager._lock:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    manager.token_url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()

            token_data = response.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)

            if not access_token:
                logger.error("OpenEMR token response missing access_token during manual fetch")
                raise HTTPException(status_code=502, detail="OpenEMR token response invalid")

            manager.access_token = access_token
            manager.expires_at = time.time() + expires_in
            manager.scope = token_data.get("scope", body.scope or manager.scope)
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "OpenEMR token endpoint returned error during manual fetch",
            extra={"status_code": exc.response.status_code, "response": exc.response.text},
        )
        raise HTTPException(status_code=502, detail="Failed to fetch OpenEMR token") from exc
    except Exception:
        logger.exception("Unexpected error during manual OpenEMR token fetch")
        raise HTTPException(status_code=502, detail="Failed to fetch OpenEMR token")

    return ManualTokenResponse(status="ok", expires_in=int(expires_in), scope=manager.scope)


@router.get("/status")
async def token_status() -> TokenStatusResponse:
    manager = get_openemr_auth_manager()
    expires_in = manager.expires_in_seconds()
    return TokenStatusResponse(
        token_present=manager.access_token is not None,
        expires_in=expires_in,
        expires_at=int(manager.expires_at) if manager.expires_at else None,
        scope=manager.scope,
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
