
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.api_client.gemini_audio_client import transcribe_audio
from src.services.chat_service import ChatService
from src.api_client.gemini_api_client import process_user_message
from src.schemas.chat_schemas import ChatMessage, ChatResponse

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def _process_and_handle_intent(message: str, db: AsyncSession) -> ChatResponse:
    """
    Helper function to process a message with Gemini and handle the resulting intent.
    This avoids code duplication in the API endpoints.
    """
    if not message:
        logging.warning("Message to process is empty.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A mensagem processada está vazia.")

    gemini_response, error = await process_user_message(message)
    logging.debug(f"Gemini API raw response: {json.dumps(gemini_response)}")

    if error:
        logging.error(f"Gemini API error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error)

    chat_service = ChatService(db)
    return await chat_service.handle_intent(gemini_response)

@router.post("/api/chat/audio", response_model=ChatResponse)
async def chat_audio_api(db: AsyncSession = Depends(get_db), audio_file: UploadFile = File(...)):
    logging.info(f"Received chat audio API request: {audio_file.filename}")
    
    transcribed_message = await transcribe_audio(audio_file)
    
    return await _process_and_handle_intent(transcribed_message, db)

@router.post("/api/chat", response_model=ChatResponse)
async def chat_api(chat_message: ChatMessage, db: AsyncSession = Depends(get_db)):
    logging.info(f"Received chat API request with message: {chat_message.message}")
    return await _process_and_handle_intent(chat_message.message, db)

