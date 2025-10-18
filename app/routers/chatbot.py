from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.database import get_db
from app.schemas.schemas import (
    ChatRequest, ChatResponse as ChatResponseSchema,
    MessageResponse, MessageCreate
)
from app.crud import crud
from app.services.chatbot_service import chatbot_service


router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.post("/chat", response_model=ChatResponseSchema)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Chat endpoint - receives user message and returns AI response.
    Integrates with chatbot service for AI logic.
    """
    # Verify user exists
    user = await crud.get_user(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's chat
    chat = await crud.get_chat_by_user(db, request.user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Save user message
    user_message = MessageCreate(role="user", content=request.message)
    await crud.create_message(db, UUID(chat.id), user_message)
    
    # Get chat history for context
    chat_history = await crud.get_chat_messages(db, UUID(chat.id))
    
    # Get user context (transactions and goals) for better responses
    user_transactions = await crud.get_user_transactions(db, request.user_id)
    user_goals = await crud.get_user_goals(db, request.user_id)
    
    # Generate AI response using the service
    ai_response_text = await chatbot_service.generate_response(
        user_message=request.message,
        chat_history=chat_history,
        user_transactions=user_transactions,
        user_goals=user_goals
    )
    
    # Save AI response
    ai_message = MessageCreate(role="assistant", content=ai_response_text)
    ai_message_db = await crud.create_message(db, UUID(chat.id), ai_message)
    
    return ChatResponseSchema(
        response=ai_response_text,
        message_id=UUID(ai_message_db.id)
    )


@router.get("/messages/{user_id}", response_model=List[MessageResponse])
async def get_messages(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get chat history for a user"""
    # Get user's chat
    chat = await crud.get_chat_by_user(db, user_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get all messages
    messages = await crud.get_chat_messages(db, UUID(chat.id))
    return messages
