import tempfile
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Account, Conversation, ConversationTurn
from ..schemas import AskRequest, AskResponse, ConversationOut, TurnOut
from ..deps import get_current_account
from ..rag_engine import answer_question
from ..speech import transcribe_audio

router = APIRouter(tags=["chat"])


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, db: Session = Depends(get_db), account: Account = Depends(get_current_account)):
    if not account.organization_id:
        raise HTTPException(400, "هذا الحساب غير مرتبط بأي مؤسسة")

    if payload.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == payload.conversation_id, Conversation.account_id == account.id)
            .first()
        )
        if not conversation:
            raise HTTPException(404, "المحادثة غير موجودة")
    else:
        conversation = Conversation(account_id=account.id, title=payload.question[:60])
        db.add(conversation)
        db.flush()

    result = answer_question(db, account.organization_id, payload.question)

    turn = ConversationTurn(
        conversation_id=conversation.id,
        question=payload.question,
        answer=result["answer"],
        was_fallback=result["was_fallback"],
        sources=", ".join(result["sources"]) if result["sources"] else None,
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)

    return AskResponse(
        conversation_id=conversation.id,
        turn_id=turn.id,
        answer=turn.answer,
        was_fallback=turn.was_fallback,
        sources=result["sources"],
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db), account: Account = Depends(get_current_account)):
    return (
        db.query(Conversation)
        .filter(Conversation.account_id == account.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )


@router.get("/conversations/{conversation_id}/turns", response_model=list[TurnOut])
def get_turns(conversation_id: str, db: Session = Depends(get_db), account: Account = Depends(get_current_account)):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.account_id == account.id)
        .first()
    )
    if not conversation:
        raise HTTPException(404, "المحادثة غير موجودة")
    return (
        db.query(ConversationTurn)
        .filter(ConversationTurn.conversation_id == conversation_id)
        .order_by(ConversationTurn.created_at.asc())
        .all()
    )


@router.post("/speech/transcribe")
async def speech_to_text(file: UploadFile = File(...), account: Account = Depends(get_current_account)):
    suffix = os.path.splitext(file.filename)[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        text = transcribe_audio(tmp_path)
    finally:
        os.unlink(tmp_path)
    return {"text": text}
