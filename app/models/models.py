from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey, Numeric, Date, Integer
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
    income_monthly_kzt = Column(Numeric(precision=15, scale=2))

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
    __tablename__ = "goals"
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid4()), index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    monthly_contribution = Column(Float, default=0.0, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="goals")


class Budget(Base):
    __tablename__ = "budgets"
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid4()), index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    month = Column(Date, nullable=False, index=True)  # normalized to first day of month
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")
    items = relationship("BudgetItem", back_populates="budget", cascade="all, delete-orphan")

class BudgetItem(Base):
    __tablename__ = "budget_items"
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid4()), index=True)
    budget_id = Column(UUID(), ForeignKey("budgets.id"), nullable=False)
    category = Column(String, nullable=False)
    amount_kzt = Column(Numeric(precision=15, scale=2), nullable=False)
    budget = relationship("Budget", back_populates="items")

class CreditRequest(Base):
    __tablename__ = "credit_requests"
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid4()), index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    product_id = Column(String)  # Optional external product ref
    amount_kzt = Column(Numeric(precision=15, scale=2), nullable=False)
    term_months = Column(Integer, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")

class DepositRequest(Base):
    __tablename__ = "deposit_requests"
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid4()), index=True)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    product_id = Column(String)
    initial_deposit_kzt = Column(Numeric(precision=15, scale=2), nullable=False)
    term_months = Column(Integer, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")

