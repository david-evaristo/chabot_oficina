import logging

from fastapi import UploadFile, HTTPException, status
from google import genai
from google.genai import types

from src.core.config import Config

# Configuração do Gemini
gemini_client = None
if Config.GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def transcribe_audio(audio_file: UploadFile) -> str:
    """
    Transcribes the given audio file using the Gemini API.
    """
    if not gemini_client:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="API Key do Gemini não configurada")

    logging.info(f"Starting transcription for audio file: {audio_file.filename}")
    try:
        audio_bytes = await audio_file.read()
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type=audio_file.content_type)
        
        contents = [audio_part, "Por favor, transcreva este áudio."]
        
        async with gemini_client.aio as aclient:
            response = await aclient.models.generate_content(
                model="models/gemini-1.5-pro-latest", # Directly use the model name
                contents=contents
            )
        
        message = response.text
        logging.info(f"Transcription successful. Transcribed text: '{message}'")
        
        if not message:
            logging.warning("Transcription resulted in an empty message.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transcrição resultou em mensagem vazia")
            
        return message

    except Exception as e:
        logging.error(f"Error during audio transcription: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro na transcrição do áudio: {e}")