import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Account, Role, KnowledgeFile, KnowledgeChunk
from ..schemas import AccountCreate, AccountOut
from ..security import generate_temp_password, hash_password
from ..deps import require_role, get_current_account
from ..mailer import send_temp_password_email
from ..ingestion import extract_text, split_into_chunks, embed_texts

router = APIRouter(prefix="/admin", tags=["admin"])
_only_org_admin = require_role("org_admin", "super_admin")


@router.post("/users", response_model=AccountOut)
def create_member(payload: AccountCreate, db: Session = Depends(get_db), admin: Account = Depends(_only_org_admin)):
    temp_password = generate_temp_password()
    member = Account(
        organization_id=admin.organization_id,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(temp_password),
        role=Role.member,
        must_change_password=True,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    send_temp_password_email(member.email, member.full_name, temp_password)
    return member


@router.get("/users", response_model=list[AccountOut])
def list_members(db: Session = Depends(get_db), admin: Account = Depends(_only_org_admin)):
    return (
        db.query(Account)
        .filter(Account.organization_id == admin.organization_id, Account.role == Role.member)
        .all()
    )


@router.post("/documents")
def upload_document(
    file: UploadFile = File(...),
    tag: str = Form(default=""),
    db: Session = Depends(get_db),
    admin: Account = Depends(_only_org_admin),
):
    raw = file.file.read()
    text = extract_text(file.filename, raw)
    if not text.strip():
        raise HTTPException(400, "تعذّر استخراج نص من هذا الملف")

    kb_file = KnowledgeFile(
        organization_id=admin.organization_id,
        filename=file.filename,
        file_type=file.filename.split(".")[-1].lower(),
        tag=tag or None,
        uploaded_by=admin.id,
    )
    db.add(kb_file)
    db.flush()  # get kb_file.id before commit

    pieces = split_into_chunks(text)
    if not pieces:
        db.rollback()
        raise HTTPException(400, "الملف لا يحتوي على نص قابل للفهرسة")

    vectors = embed_texts(pieces)
    for piece, vec in zip(pieces, vectors):
        db.add(KnowledgeChunk(
            file_id=kb_file.id,
            organization_id=admin.organization_id,
            content=piece,
            embedding=vec,
        ))
    db.commit()
    return {"status": "ok", "file_id": str(kb_file.id), "chunks_indexed": len(pieces)}


@router.get("/documents")
def list_documents(db: Session = Depends(get_db), admin: Account = Depends(_only_org_admin)):
    files = (
        db.query(KnowledgeFile)
        .filter(KnowledgeFile.organization_id == admin.organization_id)
        .order_by(KnowledgeFile.created_at.desc())
        .all()
    )
    return [
        {"id": str(f.id), "filename": f.filename, "type": f.file_type, "tag": f.tag, "uploaded_at": f.created_at}
        for f in files
    ]


@router.delete("/documents/{file_id}")
def delete_document(file_id: str, db: Session = Depends(get_db), admin: Account = Depends(_only_org_admin)):
    kb_file = (
        db.query(KnowledgeFile)
        .filter(KnowledgeFile.id == file_id, KnowledgeFile.organization_id == admin.organization_id)
        .first()
    )
    if not kb_file:
        raise HTTPException(404, "الملف غير موجود")
    db.delete(kb_file)  # cascades to chunks
    db.commit()
    return {"status": "deleted"}
