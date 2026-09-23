import uuid
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import jwt

from .database import get_db
from .models import Account
from .security import decode_access_token


def get_current_account(
    authorization: str = Header(default=None),
    db: Session = Depends(get_db),
) -> Account:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    account = db.query(Account).filter(Account.id == uuid.UUID(payload["sub"])).first()
    if not account or not account.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account not found or disabled")
    return account


def require_role(*allowed_roles: str):
    def _checker(account: Account = Depends(get_current_account)) -> Account:
        if account.role.value not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return account
    return _checker
