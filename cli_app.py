import asyncio
import json
import os
from contextlib import asynccontextmanager

from src.services.chat_service import ChatService
from src.core.database import get_db, init_db_fastapi, SessionLocal, engine, Base
from src.api_client.gemini_api_client import process_user_message
from src.core.config import Config
from src.core.models import ServiceRecord, Car, Client # Import models to ensure they are registered with Base

async def ask_question(question: str):
    """Sends a question to the chat service and prints the response."""
    async with asynccontextmanager(get_db)() as db:
        gemini_response, error = await process_user_message(question)

        if error:
            print(f"Erro ao processar mensagem com Gemini: {error}")
            return

        if not gemini_response:
            print("Erro: Resposta vazia do Gemini.")
            return

        chat_service = ChatService(db)
        try:
            response = await chat_service.handle_intent(gemini_response)
            print("Resposta do Mech-AI:")
            print(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Erro ao lidar com a intenção: {e}")

async def main():
    print("Bem-vindo ao Mech-AI CLI!")
    print("Inicializando banco de dados...")
    await init_db_fastapi()
    print("Banco de dados inicializado.")
    print("Digite sua pergunta ou 'sair' para encerrar.")

    while True:
        user_input = input("Você: ")
        if user_input.lower() == 'sair':
            break
        await ask_question(user_input)

if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Ensure GEMINI_API_KEY is set
    if not Config.GEMINI_API_KEY:
        print("Erro: GEMINI_API_KEY não configurada. Por favor, defina-a no seu arquivo .env.")
    else:
        asyncio.run(main())