"""Security primitives: password hashing, JWT creation, role enforcement.

``passlib`` CryptContext is used for hashing, with the old hand-rolled
``pbkdf2_hmac`` format kept as a fallback so that existing seeded users
(notably ``supplier@ankh.com``) keep working without a manual rehash. Passwords
stored under the old ``salt:hexkey`` scheme are transparently upgraded to the
passlib format on the next successful login.
"""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from . import models

logger = logging.getLogger(__name__)

# --- configuration ----------------------------------------------------------
#
# Read from the environment via os.getenv, with backend/.env loaded as a
# convenience for local development (python-dotenv). The path is anchored to
# this file's directory, so it works whether uvicorn runs from backend/ or
# pytest runs from the repo root. Real environment variables always win over
# the .env file. See backend/.env.example for the documented template.
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

_is_production = (
    os.getenv("DEPLOYMENT_ENV") == "production"
    or os.getenv("PRODUCTION") == "true"
    or os.getenv("ENV") == "production"
)

# The default is deliberately ephemeral: a fresh random key per process, so a
# freshly cloned repo runs out of the box without a shared secret. Tokens then
# only survive for the life of one process, which is fine for a local demo and
# obviously wrong in production — where we refuse to start instead.
SECRET_KEY = os.getenv("ANKH_SECRET_KEY") or secrets.token_urlsafe(64)
JWT_ALGORITHM = os.getenv("ANKH_JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ANKH_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ANKH_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

if _is_production and not os.getenv("ANKH_SECRET_KEY"):
    raise RuntimeError(
        "ANKH_SECRET_KEY must be set in production. Refusing to start with an "
        "ephemeral key: tokens would be invalidated on every restart."
    )
if not os.getenv("ANKH_SECRET_KEY"):
    logger.warning(
        "ANKH_SECRET_KEY is not set; using an ephemeral key valid only for "
        "this process. Set it in backend/.env (see .env.example) for any "
        "deployment that restarts or runs more than one worker."
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# Recognises passlib-managed hashes. pbkdf2_sha256 is the active scheme: it is
# the same algorithm the hand-rolled code used, but passlib owns the salt,
# round count, encoding, and constant-time comparison.
#
# bcrypt is deliberately NOT used here — passlib 1.7.4 reads
# ``bcrypt.__about__.__version__``, which bcrypt removed in 4.1, so the pairing
# installed in this venv (passlib 1.7.4 + bcrypt 5.0.0) raises on every hash.
_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# --- password hashing --------------------------------------------------------


def get_password_hash(password: str) -> str:
    return _pwd_context.hash(password)


def _verify_legacy(plain_password: str, salt: str, key_hex: str) -> bool:
    """Verify against the old ``salt:hexkey`` storage format.

    This predates passlib — it is just a sha256 pbkdf2_hmac with 100 000
    rounds. We keep it around so the seeded ``supplier@ankh.com`` account
    does not break.
    """
    try:
        candidate = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return candidate.hex() == key_hex
    except Exception:
        return False


def verify_password(plain_password: str, stored_hash: str) -> bool:
    # The old format uses ``:`` as a delimiter and is plain hex — no leading
    # ``$``. If we see that pattern, verify with the legacy path first.
    if ":" in stored_hash and not stored_hash.startswith("$"):
        parts = stored_hash.rsplit(":", 1)
        if len(parts) == 2:
            return _verify_legacy(plain_password, parts[0], parts[1])
    return _pwd_context.verify(plain_password, stored_hash)


def _upgrade_hash_if_needed(db, user: models.User, plain_password: str) -> None:
    """Transparently re-hash a password that was stored in the old format."""
    if not user.hashed_password.startswith("$"):
        user.hashed_password = _pwd_context.hash(plain_password)
        db.commit()


# --- JWT --------------------------------------------------------------------


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = (datetime.now(timezone.utc) + expires_delta) if expires_delta else (
        datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


# --- role enforcement --------------------------------------------------------


def require_role(role: str):
    """Dependency factory enforcing a single role.

    Replaces the ten hand-written ``if current_user.role != "...": raise 403``
    blocks that used to open each protected handler. Declaring it as a
    dependency also puts the requirement in the OpenAPI schema instead of
    hiding it in the function body.
    """

    def _require(
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only {role}s can perform this action",
            )
        return current_user

    return _require


require_buyer = require_role("buyer")
require_supplier = require_role("supplier")
