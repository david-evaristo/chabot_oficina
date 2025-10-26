import logging
from fastapi import UploadFile, HTTPException, status
from google import genai
from google.genai import types
from google.api_core.exceptions import GoogleAPIError

from src.core.config import Config

logger = logging.getLogger(__name__)

class GeminiAudioClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = Config.GEMINI_MODEL

    async def transcribe_audio(self, audio_file: UploadFile) -> str:
        """
        Transcribes the given audio file using the Gemini API.
        """
        logger.info(f"Starting transcription for audio file: {audio_file.filename}")

        try:
            audio_bytes = await audio_file.read()
            logger.info(f"Audio file size: {len(audio_bytes)} bytes")

            if len(audio_bytes) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Arquivo de áudio vazio"
                )

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

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=generate_content_config
            )

            message = response.text.strip()
            logger.info(f"Transcription successful. Transcribed text: '{message}'")

            if not message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Transcrição retornou texto vazio"
                )

            return message

        except HTTPException:
            raise
        except GoogleAPIError as e:
            logger.error(f"Gemini API error during audio transcription: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro na API do Gemini durante transcrição de áudio: {str(e)}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during audio transcription: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ocorreu um erro inesperado durante a transcrição do áudio: {str(e)}"
            )