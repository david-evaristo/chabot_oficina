import google.generativeai as genai
from config import Config
import asyncio
import functools
import json
import logging

# Configuração do Gemini
if Config.GEMINI_API_KEY:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
else:
    gemini_model = None

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Prompt do sistema para o Gemini
SYSTEM_PROMPT = """
Você é o Mech-AI, um assistente especializado em registrar e pesquisar serviços automotivos.
Sua função é extrair informações de conversas com mecânicos e formatar em registros estruturados ou parâmetros de pesquisa.

Identifique a intenção do usuário:
- Se o usuário deseja registrar um novo serviço, a intenção é "create_service".
- Se o usuário deseja pesquisar por serviços existentes, a intenção é "search_service".

Para a intenção \"create_service\", responda SEMPRE em formato JSON com esta estrutura:\n{\n    \"intent\": \"create_service\",\n    \"data\": {\n        \"client_name\": \"nome do cliente ou null\",\n        \"client_phone\": \"telefone do cliente ou null\",\n        "car_brand": "marca do carro (inferir se apenas o modelo for fornecido e a marca for comum, ex: Palio -> Fiat)",\n        \"car_model\": \"modelo do carro ou null\",\n        \"car_color\": \"cor do carro ou null\",\n        \"car_year\": \"ano do carro (número) ou null\",\n        \"service_description\": \"descrição do serviço\",\        \"service_date\": \"YYYY-MM-DD ou null\",\n        \"service_valor\": \"valor numérico ou null\",\n        \"service_observations\": \"observações ou null\"\n    }\n}\n\nPara a intenção \"search_service\", responda SEMPRE em formato JSON com esta estrutura:\n{\n    \"intent\": \"search_service\",\n    \"search_params\": {\n        \"client_name\": \"nome do cliente ou null\",\n        \"car_brand\": \"marca do carro ou null\",\n        \"car_model\": \"modelo do carro ou null\",\n        \"service_description\": \"descrição do serviço ou null\"\n    }\n}

Se faltar alguma informação, use null como valor.
Seja conciso e objetivo nas respostas.
"""

async def process_user_message(message):
    if not gemini_model:
        return None, "API Key do Gemini não configurada"

    full_prompt = f"{SYSTEM_PROMPT}\n\nMensagem do mecânico: {message}"
    try:
        # Run the synchronous generate_content in a separate thread
        response = await asyncio.to_thread(functools.partial(gemini_model.generate_content, full_prompt))
        response_text = response.text.strip()

        # Clean up markdown formatting if present
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith('```'):
            response_text = response_text[3:-3].strip()
        
        logging.info(f"Gemini raw response: {response_text}")
        
        # Attempt to parse the JSON response
        parsed_response = json.loads(response_text)
        return parsed_response, None
    except Exception as e:
        logging.error(f"Error processing Gemini response: {e}. Raw response: {response_text}")
        return None, str(e)