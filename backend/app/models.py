import uuid
import enum
import datetime as dt

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey, Enum, Float, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .database import Base
from .config import settings


def new_uuid():
    return uuid.uuid4()


class Role(str, enum.Enum):
    super_admin = "super_admin"
    org_admin = "org_admin"
    member = "member"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    name = Column(String(150), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    accounts = relationship("Account", back_populates="organization", cascade="all, delete-orphan")
    files = relationship("KnowledgeFile", back_populates="organization", cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(Role), nullable=False, default=Role.member)
    must_change_password = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    organization = relationship("Organization", back_populates="accounts")
    conversations = relationship("Conversation", back_populates="account", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="account", cascade="all, delete-orphan")


class KnowledgeFile(Base):
    __tablename__ = "knowledge_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    tag = Column(String(100), nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    organization = relationship("Organization", back_populates="files")
    chunks = relationship("KnowledgeChunk", back_populates="file", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    file_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_files.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(settings.EMBEDDING_DIM))

    file = relationship("KnowledgeFile", back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    title = Column(String(200), default="محادثة جديدة")
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    account = relationship("Account", back_populates="conversations")
    turns = relationship("ConversationTurn", back_populates="conversation", cascade="all, delete-orphan")


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    was_fallback = Column(Boolean, default=False)
    sources = Column(Text, nullable=True)  # comma-separated filenames
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="turns")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    turn_id = Column(UUID(as_uuid=True), ForeignKey("conversation_turns.id"), nullable=True)
    score = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    account = relationship("Account", back_populates="ratings")
