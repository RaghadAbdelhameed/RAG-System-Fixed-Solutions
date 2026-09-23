import uuid
import datetime as dt
from typing import Optional, List

from pydantic import BaseModel, EmailStr


# ---- Auth ----
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    role: str
    full_name: str
    must_change_password: bool
    organization_id: Optional[uuid.UUID] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ---- Organizations ----
class OrgCreate(BaseModel):
    name: str


class OrgOut(BaseModel):
    id: uuid.UUID
    name: str
    is_active: bool
    created_at: dt.datetime

    class Config:
        from_attributes = True


# ---- Accounts ----
class AccountCreate(BaseModel):
    full_name: str
    email: EmailStr
    role: str = "member"  # "org_admin" or "member" (super_admin created separately)
    organization_id: Optional[uuid.UUID] = None


class AccountOut(BaseModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ---- Chat ----
class AskRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    question: str


class AskResponse(BaseModel):
    conversation_id: uuid.UUID
    turn_id: uuid.UUID
    answer: str
    was_fallback: bool
    sources: List[str]


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


class TurnOut(BaseModel):
    id: uuid.UUID
    question: str
    answer: str
    was_fallback: bool
    sources: Optional[str]
    created_at: dt.datetime

    class Config:
        from_attributes = True


# ---- Feedback ----
class RatingCreate(BaseModel):
    turn_id: Optional[uuid.UUID] = None
    score: int
    comment: Optional[str] = None


class RatingOut(BaseModel):
    id: uuid.UUID
    score: int
    comment: Optional[str]
    reviewed: bool
    created_at: dt.datetime

    class Config:
        from_attributes = True


class RatingStats(BaseModel):
    average_score: float
    total_ratings: int
    per_account: dict
