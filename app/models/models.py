from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from app.database import Base
import uuid


# UUID column type that works with SQLite
def UUID():
    return String(36)


class User(Base):
    """User model - one user, one chat"""
    __tablename__ = "users"
    
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid4()), index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat = relationship("Chat", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")


class Chat(Base):
    """Chat model - one chat per user"""
    __tablename__ = "chats"
    
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid4()), index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="chat")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    """Message model - stores chat messages"""
    __tablename__ = "messages"
    
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid4()), index=True)
    chat_id = Column(UUID(), ForeignKey("chats.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")


class Transaction(Base):
    """Transaction model - parsed from bank statements (matches parser structure)"""
    __tablename__ = "transactions"
    
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid4()), index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)  # Store as Decimal
    transaction_type = Column(String, nullable=False)  # 'income' or 'expense'
    description = Column(Text, nullable=False)
    transaction_date = Column(Date, nullable=False)  # Date only, not DateTime
    category = Column(String)  # Optional category
    balance_after = Column(Numeric(precision=15, scale=2))  # Optional balance after transaction
    reference_number = Column(String)  # Optional reference number
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")


class Goal(Base):
    """Goal model - financial goals with progress tracking"""
    __tablename__ = "goals"
    
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid4()), index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    monthly_contribution = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="goals")
