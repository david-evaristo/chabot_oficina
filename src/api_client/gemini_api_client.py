import logging
from google import genai
from google.genai import types
from src.core.config import Config
from src.schemas.chat_schemas import GeminiResponse
from fastapi import HTTPException, status
from google.api_core.exceptions import GoogleAPIError
from src.utils.prompts import GEMINI_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

class GeminiAPIClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = Config.GEMINI_MODEL

    async def process_user_message(self, message: str):
        full_prompt = GEMINI_CLASSIFICATION_PROMPT.format(message=message)
        
        logger.debug(f"Full prompt sent to Gemini: {full_prompt}")
        try:
            generation_config = types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=GeminiResponse.model_json_schema()
            )
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=generation_config
            )
            
            parsed_response = response.parsed
            logger.info(f"Gemini parsed response: {parsed_response}")
            return parsed_response
        except GoogleAPIError as e:
            logger.error(f"Gemini API error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro na API do Gemini: {str(e)}")
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro de validação: {str(e)}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ocorreu um erro inesperado: {str(e)}")