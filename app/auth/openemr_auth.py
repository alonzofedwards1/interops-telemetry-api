import asyncio
import base64
import json
import logging
import time
from typing import Any, Dict, Optional

from fastapi import HTTPException

from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class OpenEMRAuthManager:
    """Minimal OAuth2 password-grant manager for OpenEMR.

    This POC-oriented manager keeps token state in-memory and refreshes
    proactively to avoid expired requests from future orchestration flows.
    """

    def __init__(self, settings: Settings):
        self.client_id = settings.openemr_client_id
        self.client_secret = settings.openemr_client_secret
        self.token_url = settings.openemr_token_url
        self.username = settings.openemr_username
        self.password = settings.openemr_password
        self.scope = settings.openemr_scope
        self.user_role = getattr(settings, "openemr_user_role", None)

        self.access_token: Optional[str] = None
        self.expires_at: Optional[float] = None
        self._lock = asyncio.Lock()

    def expires_in_seconds(self) -> Optional[int]:
        if not self.expires_at:
            return None
        return int(self.expires_at - time.time())

    def is_expired(self) -> bool:
        expires_in = self.expires_in_seconds()
        return expires_in is None or expires_in <= 0

    def expires_soon(self, buffer_seconds: int = 300) -> bool:
        expires_in = self.expires_in_seconds()
        return expires_in is None or expires_in <= buffer_seconds

    async def get_access_token(self) -> Optional[str]:
        await self.refresh_access_token_if_needed()
        return self.access_token

    async def refresh_access_token_if_needed(self) -> None:
        """Refresh the access token when missing, expired, or nearing expiry."""

        async with self._lock:
            if self.access_token and not self.expires_soon():
                return

            await self._refresh_access_token()

    async def _refresh_access_token(self) -> None:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - environment guardrail
            logger.error("httpx is required for OpenEMR token refresh; install from requirements.txt")
            raise HTTPException(status_code=500, detail="httpx dependency missing") from exc

        if not all([self.client_id, self.client_secret, self.token_url, self.username, self.password]):
            logger.error("OpenEMR OAuth settings are incomplete; cannot refresh token")
            raise HTTPException(status_code=500, detail="OpenEMR OAuth configuration incomplete")

        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
        }

        if self.scope:
            payload["scope"] = self.scope
        if self.user_role:
            payload["user_role"] = self.user_role

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.token_url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "OpenEMR token endpoint returned error",
                extra={"status_code": exc.response.status_code, "response": exc.response.text},
            )
            raise HTTPException(status_code=502, detail="Failed to refresh OpenEMR token") from exc
        except Exception as exc:  # pragma: no cover - guardrail for unexpected networking errors
            logger.exception("Unexpected error refreshing OpenEMR token")
            raise HTTPException(status_code=500, detail="Unexpected OpenEMR token error") from exc

        token_data = response.json()
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)

        if not access_token:
            logger.error("OpenEMR token response missing access_token")
            raise HTTPException(status_code=502, detail="OpenEMR token response invalid")

        now = time.time()
        self.access_token = access_token
        self.expires_at = now + expires_in
        self.scope = token_data.get("scope", self.scope)

        logger.info(
            "OpenEMR access token refreshed",
            extra={"expires_at": self.expires_at, "expires_in": expires_in},
        )

    def decode_jwt(self, token: Optional[str]) -> Dict[str, Any]:
        """Decode JWT header and claims without verification for observability."""

        if not token:
            return {}

        try:
            parts = token.split(".")
            if len(parts) < 2:
                return {}

            def _decode(segment: str) -> Any:
                padded = segment + "=" * (-len(segment) % 4)
                decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
                return json.loads(decoded.decode("utf-8"))

            header = _decode(parts[0])
            claims = _decode(parts[1])
            return {"header": header, "claims": claims}
        except Exception:
            logger.exception("Failed to decode JWT for OpenEMR token")
            return {}

    def health(self) -> Dict[str, Any]:
        expires_in = self.expires_in_seconds()
        return {
            "token_present": self.access_token is not None,
            "expires_at": int(self.expires_at) if self.expires_at else None,
            "expires_in_seconds": expires_in,
            "expires_soon": self.expires_soon(),
            "scope": self.scope,
        }


def get_openemr_auth_manager() -> OpenEMRAuthManager:
    # A simple factory to keep stateful token cache shared across the process.
    global _auth_manager
    try:
        return _auth_manager
    except NameError:
        _auth_manager = OpenEMRAuthManager(get_settings())
        return _auth_manager
