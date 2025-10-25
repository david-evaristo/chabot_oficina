import logging
from google import genai
from google.genai import types
from src.core.config import Config
from src.schemas.chat_schemas import GeminiResponse

# Configuração do Gemini
gemini_client = None
if Config.GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def process_user_message(message):
    if not gemini_client:
        return None, "API Key do Gemini não configurada"

    full_prompt = f"Mensagem do mecânico: {message}"
    logging.debug(f"Full prompt sent to Gemini: {full_prompt}")
    try:
        async with gemini_client.aio as aclient:
            response = await aclient.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                    response_json_schema=GeminiResponse.model_json_schema()
                )
            )
        
        parsed_response = response.parsed
        logging.info(f"Gemini parsed response: {parsed_response}")
        return parsed_response, None
    except Exception as e:
        logging.error(f"Error processing Gemini response: {e}")
        return None, str(e)