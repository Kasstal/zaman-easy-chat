from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID
from app.models.models import User, Chat, Message, Transaction, Goal
from app.schemas.schemas import (
    UserCreate, MessageCreate, TransactionCreate, 
    GoalCreate, GoalUpdate
)


# User CRUD
async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """Create a new user with associated chat"""
    db_user = User(username=user.username)
    db.add(db_user)
    await db.flush()
    
    # Create chat for the user
    db_chat = Chat(user_id=db_user.id)
    db.add(db_chat)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get user by ID"""
    result = await db.execute(select(User).where(User.id == str(user_id)))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


# Chat CRUD
async def get_chat_by_user(db: AsyncSession, user_id: UUID) -> Optional[Chat]:
    """Get chat for a user"""
    result = await db.execute(select(Chat).where(Chat.user_id == str(user_id)))
    return result.scalar_one_or_none()


# Message CRUD
async def create_message(
    db: AsyncSession, 
    chat_id: UUID, 
    message: MessageCreate
) -> Message:
    """Create a new message in a chat"""
    db_message = Message(
        chat_id=str(chat_id),
        role=message.role,
        content=message.content
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message


async def get_chat_messages(db: AsyncSession, chat_id: UUID) -> List[Message]:
    """Get all messages for a chat"""
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == str(chat_id))
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())


# Transaction CRUD
async def create_transaction(
    db: AsyncSession, 
    user_id: UUID, 
    transaction: TransactionCreate
) -> Transaction:
    """Create a new transaction"""
    # Determine transaction type based on amount
    transaction_type = "income" if transaction.amount >= 0 else "expense"
    
    db_transaction = Transaction(
        user_id=str(user_id),
        amount=abs(transaction.amount),
        transaction_type=transaction_type,
        description=transaction.description or "Transaction",
        category=transaction.category,
        transaction_date=transaction.transaction_date.date()
    )
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction


async def create_transactions_bulk(
    db: AsyncSession,
    user_id: UUID,
    transactions: List[TransactionCreate]
) -> List[Transaction]:
    """Create multiple transactions at once"""
    db_transactions = []
    for t in transactions:
        # Determine transaction type based on amount
        transaction_type = "income" if t.amount >= 0 else "expense"
        
        db_transaction = Transaction(
            user_id=str(user_id),
            amount=abs(t.amount),
            transaction_type=transaction_type,
            description=t.description or "Transaction",
            category=t.category,
            transaction_date=t.transaction_date.date()
        )
        db_transactions.append(db_transaction)
    
    db.add_all(db_transactions)
    await db.commit()
    for t in db_transactions:
        await db.refresh(t)
    return db_transactions


async def get_user_transactions(db: AsyncSession, user_id: UUID) -> List[Transaction]:
    """Get all transactions for a user"""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == str(user_id))
        .order_by(Transaction.transaction_date.desc())
    )
    return list(result.scalars().all())


# Goal CRUD
async def create_goal(db: AsyncSession, user_id: UUID, goal: GoalCreate) -> Goal:
    """Create a new goal"""
    db_goal = Goal(
        user_id=str(user_id),
        title=goal.title,
        target_amount=goal.target_amount,
        current_amount=0.0,
        monthly_contribution=goal.monthly_contribution
    )
    db.add(db_goal)
    await db.commit()
    await db.refresh(db_goal)
    return db_goal


async def get_goal(db: AsyncSession, goal_id: UUID) -> Optional[Goal]:
    """Get goal by ID"""
    result = await db.execute(select(Goal).where(Goal.id == str(goal_id)))
    return result.scalar_one_or_none()


async def get_user_goals(db: AsyncSession, user_id: UUID) -> List[Goal]:
    """Get all goals for a user"""
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == str(user_id))
        .order_by(Goal.created_at.desc())
    )
    return list(result.scalars().all())


async def update_goal_progress(
    db: AsyncSession, 
    goal_id: UUID, 
    goal_update: GoalUpdate
) -> Optional[Goal]:
    """Update goal progress and other fields"""
    db_goal = await get_goal(db, goal_id)
    if db_goal:
        if goal_update.current_amount is not None:
            db_goal.current_amount = goal_update.current_amount
        if goal_update.monthly_contribution is not None:
            db_goal.monthly_contribution = goal_update.monthly_contribution
        if goal_update.title is not None:
            db_goal.title = goal_update.title
        if goal_update.target_amount is not None:
            db_goal.target_amount = goal_update.target_amount
        await db.commit()
        await db.refresh(db_goal)
    return db_goal


async def delete_goal(db: AsyncSession, goal_id: UUID) -> bool:
    """Delete a goal"""
    db_goal = await get_goal(db, goal_id)
    if db_goal:
        await db.delete(db_goal)
        await db.commit()
        return True
    return False
