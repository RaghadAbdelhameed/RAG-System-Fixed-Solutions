from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Organization, Account, Role
from ..schemas import OrgCreate, OrgOut, AccountCreate, AccountOut
from ..security import generate_temp_password, hash_password
from ..deps import require_role
from ..mailer import send_temp_password_email

router = APIRouter(prefix="/super-admin", tags=["super-admin"])
_only_super_admin = require_role("super_admin")


@router.post("/organizations", response_model=OrgOut)
def create_organization(payload: OrgCreate, db: Session = Depends(get_db), _=Depends(_only_super_admin)):
    org = Organization(name=payload.name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("/organizations", response_model=list[OrgOut])
def list_organizations(db: Session = Depends(get_db), _=Depends(_only_super_admin)):
    return db.query(Organization).order_by(Organization.created_at.desc()).all()


@router.post("/organizations/{org_id}/admins", response_model=AccountOut)
def create_org_admin(org_id: str, payload: AccountCreate, db: Session = Depends(get_db), _=Depends(_only_super_admin)):
    temp_password = generate_temp_password()
    admin = Account(
        organization_id=org_id,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(temp_password),
        role=Role.org_admin,
        must_change_password=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    send_temp_password_email(admin.email, admin.full_name, temp_password)
    return admin
