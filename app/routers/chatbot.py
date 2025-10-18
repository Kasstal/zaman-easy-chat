# app/routers/chatbot.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import logging

from app.database import get_db
from app.schemas.schemas import (
    ChatRequest,
    ChatResponse as ChatResponseSchema,
    MessageResponse,
    MessageCreate,
)
from app.crud import crud  # single import — use crud.<fn> everywhere
from app.services.chatbot_service.chatbot_service import chatbot_service

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponseSchema)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Chat endpoint - receives user message and returns AI response.
    Integrates with chatbot service for AI logic.
    """
    try:
        # 🔗 attach a live AsyncSession for tool calls
        chatbot_service.db = db

        # 1) Verify user exists
        user = await crud.get_user(db, request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # 2) Get user's chat
        chat = await crud.get_chat_by_user(db, request.user_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        # 3) Save user message
        user_msg = MessageCreate(role="user", content=request.message)
        await crud.create_message(db, UUID(chat.id), user_msg)

        # 4) Load context
        chat_history = await crud.get_chat_messages(db, UUID(chat.id))
        user_transactions = await crud.get_user_transactions(db, request.user_id)
        user_goals = await crud.get_user_goals(db, request.user_id)

        # 5) Generate AI response
        ai_response_text = await chatbot_service.generate_response(
            user_message=request.message,
            chat_history=chat_history,
            user_transactions=user_transactions,
            user_goals=user_goals,
            user_id=str(request.user_id)
        )

        # 6) Save assistant message
        ai_msg = MessageCreate(role="assistant", content=ai_response_text)
        ai_msg_db = await crud.create_message(db, UUID(chat.id), ai_msg)

        logger.info("💬 Chatbot response stored: %s", ai_msg_db.id)

        return ChatResponseSchema(
            response=ai_response_text,
            message_id=UUID(ai_msg_db.id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in /chat endpoint: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/messages/{user_id}", response_model=List[MessageResponse])
async def get_messages(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for a user."""
    try:
        chat = await crud.get_chat_by_user(db, user_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        messages = await crud.get_chat_messages(db, UUID(chat.id))
        return messages

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in /messages endpoint: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
