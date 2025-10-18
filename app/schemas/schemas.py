from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from decimal import Decimal


# User Schemas
class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Chat Schemas
class ChatResponse(BaseModel):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Message Schemas
class MessageBase(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: UUID
    chat_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Chat Request/Response
class ChatRequest(BaseModel):
    user_id: UUID
    message: str


class ChatResponse(BaseModel):
    response: str
    message_id: UUID


# Transaction Schemas
class TransactionBase(BaseModel):
    amount: float
    description: Optional[str] = None
    category: Optional[str] = None
    transaction_date: datetime


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    amount: Decimal
    transaction_type: str  # 'income' or 'expense'
    description: str
    transaction_date: date
    category: Optional[str] = None
    balance_after: Optional[Decimal] = None
    reference_number: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Statement Upload Response
class StatementUploadResponse(BaseModel):
    message: str
    transactions_count: int
    transactions: List[TransactionResponse]


# Goal Schemas
class GoalBase(BaseModel):
    title: str
    target_amount: float


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    current_amount: float


class GoalResponse(GoalBase):
    id: UUID
    user_id: UUID
    current_amount: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
