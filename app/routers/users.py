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
    """
    Create a new goal for a user
    
    Example request body:
    {
        "title": "Vacation Fund",
        "target_amount": 500000,
        "monthly_contribution": 50000
    }
    
    Returns goal with calculated fields:
    - progress_percentage: % completed
    - remaining_amount: KZT left to goal
    - months_to_complete: Estimated months
    - is_completed: Boolean completion status
    """
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_goal = await crud.create_goal(db, user_id, goal)
    return GoalResponse.from_orm_with_calculations(db_goal)


@router.get("/{user_id}/goals", response_model=List[GoalResponse])
async def get_user_goals(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all goals for a user with calculated progress fields
    
    Returns array of goals with:
    - progress_percentage: Current progress %
    - remaining_amount: Amount left to reach goal
    - months_to_complete: Estimated months based on monthly contribution
    - is_completed: Whether goal is achieved
    """
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    goals = await crud.get_user_goals(db, user_id)
    return [GoalResponse.from_orm_with_calculations(g) for g in goals]


@router.get("/goals/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific goal by ID with calculated fields"""
    goal = await crud.get_goal(db, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return GoalResponse.from_orm_with_calculations(goal)


@router.put("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    goal_update: GoalUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update goal progress or any field
    
    Example request body (all fields optional):
    {
        "current_amount": 150000,
        "monthly_contribution": 60000,
        "title": "Updated Vacation Fund",
        "target_amount": 600000
    }
    """
    goal = await crud.update_goal_progress(db, goal_id, goal_update)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return GoalResponse.from_orm_with_calculations(goal)


@router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a goal"""
    goal = await crud.get_goal(db, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    await crud.delete_goal(db, goal_id)
    return {"message": "Goal deleted successfully", "goal_id": str(goal_id)}
