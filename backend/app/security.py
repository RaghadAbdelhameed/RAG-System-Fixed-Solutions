import datetime as dt
import secrets
import string

import bcrypt
import jwt

from .config import settings


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))


def generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%*_-"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_access_token(account_id, role: str, organization_id) -> str:
    payload = {
        "sub": str(account_id),
        "role": role,
        "org": str(organization_id) if organization_id else None,
        "exp": dt.datetime.utcnow() + dt.timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
