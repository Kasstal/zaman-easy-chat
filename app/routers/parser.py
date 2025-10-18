from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.database import get_db
from app.schemas.schemas import (
    StatementUploadResponse, TransactionResponse, TransactionCreate
)
from app.crud import crud
from app.services.parser_service import parser_service


router = APIRouter(prefix="/parser", tags=["Statement Parser"])


@router.post("/upload-statement/{user_id}", response_model=StatementUploadResponse)
async def upload_statement(
    user_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload bank statement and parse transactions.
    File is NOT stored, only parsed transactions are saved to DB.
    Integrates with parser service for extraction logic.
    """
    # Verify user exists
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Read file content
    content = await file.read()
    
    # Parse the statement using the service
    parsed_transactions = await parser_service.parse_statement(
        file_content=content,
        filename=file.filename,
        user_id=user_id
    )
    
    # Save transactions to database
    db_transactions = await crud.create_transactions_bulk(
        db, user_id, parsed_transactions
    )
    
    return StatementUploadResponse(
        message="Statement parsed successfully",
        transactions_count=len(db_transactions),
        transactions=db_transactions
    )


@router.get("/transactions/{user_id}", response_model=List[TransactionResponse])
async def get_transactions(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all transactions for a user"""
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    transactions = await crud.get_user_transactions(db, user_id)
    return transactions
