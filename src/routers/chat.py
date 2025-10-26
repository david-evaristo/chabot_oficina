import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.api_client.gemini_audio_client import GeminiAudioClient
from src.services.chat_service import ChatService
from src.api_client.gemini_api_client import GeminiAPIClient
from src.schemas.chat_schemas import ChatMessage, ChatResponse
from src.core.config import Config

router = APIRouter()

logger = logging.getLogger(__name__)

def get_gemini_api_client():
    return GeminiAPIClient(api_key=Config.GEMINI_API_KEY)

def get_gemini_audio_client():
    return GeminiAudioClient(api_key=Config.GEMINI_API_KEY)


async def _process_and_handle_intent(message: str, db: AsyncSession, gemini_client: GeminiAPIClient = Depends(get_gemini_api_client)) -> ChatResponse:
    """
    Helper function to process a message with Gemini and handle the resulting intent.
    This avoids code duplication in the API endpoints.
    """
    if not message:
        logger.warning("Message to process is empty.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A mensagem processada está vazia.")

    gemini_response = await gemini_client.process_user_message(message)
    logger.debug(f"Gemini API raw response: {gemini_response.model_dump_json()}")

    chat_service = ChatService(db)
    return await chat_service.handle_intent(gemini_response)


@router.post("/api/chat/audio", response_model=ChatResponse)
async def chat_audio_api(
        audio: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        gemini_client: GeminiAPIClient = Depends(get_gemini_api_client),
        gemini_audio_client: GeminiAudioClient = Depends(get_gemini_audio_client)
):
    logger.info(f"Received chat audio API request: {audio.filename}")

    try:
        # Verificar se o arquivo foi recebido
        if not audio:
            logger.error("No audio file received")
            raise HTTPException(status_code=400, detail="No audio file received")

        logger.info(f"Audio file details - filename: {audio.filename}, content_type: {audio.content_type}")

        # Transcrever áudio
        transcribed_message = await gemini_audio_client.transcribe_audio(audio)
        logger.info(f"Transcribed message: {transcribed_message}")

        if not transcribed_message:
            logger.error("Transcription returned empty message")
            raise HTTPException(status_code=400, detail="Transcription failed or returned empty message")

        # Processar mensagem
        return await _process_and_handle_intent(transcribed_message, db, gemini_client)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_audio_api: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/api/chat", response_model=ChatResponse)
async def chat_api(chat_message: ChatMessage, db: AsyncSession = Depends(get_db), gemini_client: GeminiAPIClient = Depends(get_gemini_api_client)):
    logger.info(f"Received chat API request with message: {chat_message.message}")
    return await _process_and_handle_intent(chat_message.message, db, gemini_client)