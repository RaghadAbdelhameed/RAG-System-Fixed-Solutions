from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Account
from ..schemas import LoginRequest, LoginResponse, ChangePasswordRequest
from ..security import verify_password, hash_password, create_access_token
from ..deps import get_current_account

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.email == payload.email).first()
    if not account or not account.is_active or not verify_password(payload.password, account.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "بيانات الدخول غير صحيحة")

    token = create_access_token(account.id, account.role.value, account.organization_id)
    return LoginResponse(
        access_token=token,
        role=account.role.value,
        full_name=account.full_name,
        must_change_password=account.must_change_password,
        organization_id=account.organization_id,
    )


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
):
    if not verify_password(payload.current_password, account.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "كلمة المرور الحالية غير صحيحة")
    if len(payload.new_password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "كلمة المرور الجديدة قصيرة جداً")

    account.password_hash = hash_password(payload.new_password)
    account.must_change_password = False
    db.commit()
    return {"status": "ok"}
