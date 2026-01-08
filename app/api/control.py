import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.auth.security import create_access_token, verify_password, SECRET_KEY
from app.auth.user_store import User, get_user_store

logger = logging.getLogger(__name__)
router = APIRouter(tags=["control"])


def _oauth_config_present() -> bool:
    return bool(SECRET_KEY)


class TokenRequest(BaseModel):
    email: EmailStr
    password: str


class UserInfo(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str


class TokenResponse(BaseModel):
    digest: str = Field(..., description="JWT token")
    user: UserInfo


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str
    password: str


@router.post("/auth/token", response_model=TokenResponse)
async def issue_token(body: TokenRequest) -> TokenResponse:
    if not _oauth_config_present():
        raise HTTPException(status_code=503, detail="oauth configuration missing")

    store = get_user_store()
    user: User | None = store.get_by_email(body.email)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    digest = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return TokenResponse(digest=digest, user=UserInfo.model_validate(user.model_dump()))


@router.post("/auth/password/forgot")
async def forgot_password(body: ForgotPasswordRequest):
    # This endpoint intentionally does not reveal user existence.
    return {"message": "Reset email sent"}


@router.post("/auth/password/reset")
async def reset_password(body: ResetPasswordRequest):
    store = get_user_store()
    updated = store.update_password(body.email, body.password)
    if not updated:
        raise HTTPException(status_code=400, detail="Unable to reset password")
    return {"message": "Password updated successfully"}


@router.get("/findings")
async def list_findings() -> List[dict]:
    return []


@router.get("/committee/queue")
async def committee_queue() -> List[dict]:
    return []
