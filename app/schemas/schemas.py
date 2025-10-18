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
    monthly_contribution: float


class GoalCreate(GoalBase):
    """Schema for creating a new goal from frontend"""
    pass


class GoalUpdate(BaseModel):
    """Schema for updating goal progress"""
    current_amount: Optional[float] = None
    monthly_contribution: Optional[float] = None
    title: Optional[str] = None
    target_amount: Optional[float] = None


class GoalResponse(GoalBase):
    """Enhanced goal response with calculated fields for frontend"""
    id: UUID
    user_id: UUID
    current_amount: float
    monthly_contribution: float
    created_at: datetime
    # Calculated fields
    progress_percentage: float = 0.0
    remaining_amount: float = 0.0
    months_to_complete: Optional[float] = None
    is_completed: bool = False
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm_with_calculations(cls, goal):
        """Create response with calculated fields"""
        progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        remaining = max(0, goal.target_amount - goal.current_amount)
        months = (remaining / goal.monthly_contribution) if goal.monthly_contribution > 0 else None
        is_completed = goal.current_amount >= goal.target_amount
        
        return cls(
            id=goal.id,
            user_id=goal.user_id,
            title=goal.title,
            target_amount=goal.target_amount,
            current_amount=goal.current_amount,
            monthly_contribution=goal.monthly_contribution,
            created_at=goal.created_at,
            progress_percentage=round(progress, 2),
            remaining_amount=round(remaining, 2),
            months_to_complete=round(months, 1) if months else None,
            is_completed=is_completed
        )
