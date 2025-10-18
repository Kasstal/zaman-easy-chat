from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.database import get_db
from app.schemas.schemas import (
    UserCreate, UserResponse, GoalCreate, GoalResponse, GoalUpdate
)
from app.crud import crud


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (automatically creates a chat for them)"""
    # Check if username already exists
    existing_user = await crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    db_user = await crud.create_user(db, user)
    return db_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID"""
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/{user_id}/goals", response_model=GoalResponse)
async def create_goal(
    user_id: UUID,
    goal: GoalCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new goal for a user"""
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_goal = await crud.create_goal(db, user_id, goal)
    return db_goal


@router.get("/{user_id}/goals", response_model=List[GoalResponse])
async def get_user_goals(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all goals for a user"""
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    goals = await crud.get_user_goals(db, user_id)
    return goals


@router.put("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    goal_update: GoalUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update goal progress"""
    goal = await crud.update_goal_progress(db, goal_id, goal_update)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal
