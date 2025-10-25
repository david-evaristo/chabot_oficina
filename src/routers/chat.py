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
async def chat_audio_api(
        audio: UploadFile = File(...),
        db: AsyncSession = Depends(get_db)
):
    logging.info(f"Received chat audio API request: {audio.filename}")

    try:
        # Verificar se o arquivo foi recebido
        if not audio:
            logging.error("No audio file received")
            raise HTTPException(status_code=400, detail="No audio file received")

        logging.info(f"Audio file details - filename: {audio.filename}, content_type: {audio.content_type}")

        # Transcrever áudio
        transcribed_message = await transcribe_audio(audio)
        logging.info(f"Transcribed message: {transcribed_message}")

        if not transcribed_message:
            logging.error("Transcription returned empty message")
            raise HTTPException(status_code=400, detail="Transcription failed or returned empty message")

        # Processar mensagem
        return await _process_and_handle_intent(transcribed_message, db)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in chat_audio_api: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/api/chat", response_model=ChatResponse)
async def chat_api(chat_message: ChatMessage, db: AsyncSession = Depends(get_db)):
    logging.info(f"Received chat API request with message: {chat_message.message}")
    return await _process_and_handle_intent(chat_message.message, db)