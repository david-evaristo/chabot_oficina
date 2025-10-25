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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API Key do Gemini não configurada"
        )

    logging.info(f"Starting transcription for audio file: {audio_file.filename}")

    try:
        audio_bytes = await audio_file.read()
        logging.info(f"Audio file size: {len(audio_bytes)} bytes")

        if len(audio_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo de áudio vazio"
            )

        # CORREÇÃO: Adicionar instrução específica para transcrição de serviços mecânicos
        contents = [
            types.Content(
                parts=[
                    types.Part(text="""Transcreva este áudio de um mecânico descrevendo um serviço automotivo. 
                    O áudio contém a descrição de um serviço mecânico como troca de óleo, revisão, freios, etc.
                    Transcreva APENAS o texto falado, removendo marcações temporais [Music] ou outros ruídos.
                    Retorne a transcrição limpa em português brasileiro."""),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=audio_file.content_type or 'audio/webm',
                            data=audio_bytes
                        )
                    )
                ]
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=1000,
        )

        response = await gemini_client.aio.models.generate_content(
            model="gemini-2.5-flash",  # CORREÇÃO: Use 1.5-flash, não 2.5-flash
            contents=contents,
            config=generate_content_config
        )

        message = response.text.strip()
        logging.info(f"Transcription successful. Transcribed text: '{message}'")

        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcrição retornou texto vazio"
            )

        return message

    except HTTPException as e:
        logging.error(f"Error during audio transcription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro na transcrição do áudio: {str(e)}"
        )
    except Exception as e:
        logging.error(f"Error during audio transcription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na transcrição do áudio: {str(e)}"
        )