import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import bcrypt

    HAS_BCRYPT = True
except Exception:  # pragma: no cover - optional dependency
    bcrypt = None  # type: ignore
    HAS_BCRYPT = False

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def _hash_with_pbkdf2(plain_password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 390000)
    return f"pbkdf2${salt.hex()}${digest.hex()}"


def hash_password(plain_password: str) -> str:
    if HAS_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")
    return _hash_with_pbkdf2(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith("pbkdf2$"):
        try:
            _, salt_hex, digest_hex = hashed_password.split("$", 2)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(digest_hex)
            candidate = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 390000)
            return secrets.compare_digest(candidate, expected)
        except Exception:
            return False

    if HAS_BCRYPT:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False
    return False


def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    header = {"alg": ALGORITHM, "typ": "JWT"}

    def _b64encode(content: bytes) -> str:
        return base64.urlsafe_b64encode(content).rstrip(b"=").decode("utf-8")

    header_segment = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64encode(json.dumps(to_encode, default=str, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_segment = _b64encode(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"
