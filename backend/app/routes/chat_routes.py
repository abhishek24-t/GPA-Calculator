"""
Chatbot API route for GPA Assistant AI.
"""

from fastapi import APIRouter, HTTPException, status
from ..schemas import ChatRequest, ChatResponse
from ..ai_agent import process_chat_message

router = APIRouter(prefix="/api", tags=["AI Academic Assistant"])


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(payload: ChatRequest):
    try:
        response = await process_chat_message(
            message=payload.message,
            conversation_id=payload.conversation_id,
            academic_context=payload.academic_context
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing error: {str(e)}"
        )
