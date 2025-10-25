import json
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.services.service_management import ServiceManagementService
from src.api_client.gemini_api_client import process_user_message
from src.schemas.chat_schemas import ChatMessage, ClientDataResponse, CarDataResponse, ServiceDataResponse, ChatResponse

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@router.post("/api/chat", response_model=ChatResponse)
async def chat_api(chat_message: ChatMessage, db: AsyncSession = Depends(get_db)):
    message = chat_message.message
    logging.debug(f"Received raw chat message: {chat_message.model_dump_json()}")
    logging.info(f"Received chat API request with message: {message}")

    if not message:
        logging.warning("Received empty message in chat API request.")
        logging.debug("Raising HTTPException for empty message.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mensagem vazia")

    gemini_response, error = await process_user_message(message)
    logging.debug(f"Gemini API raw response: {json.dumps(gemini_response)}")

    if error:
        logging.error(f"Gemini API error: {error}")
        logging.debug(f"Raising HTTPException for Gemini API error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error)

    try:
        intent = gemini_response.get('intent')
        logging.info(f"Gemini detected intent: {intent}")

        service_manager = ServiceManagementService(db)

        if intent == 'create_service':
            data = gemini_response.get('data')
            if not data:
                logging.debug("Raising HTTPException for missing data in create_service intent.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={'error': 'Dados ausentes para criação de serviço.'}
                )
            
            service_result = await service_manager.create_service_record(data)

            if not service_result["success"]:
                raise HTTPException(
                    status_code=service_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                    detail={'error': service_result["message"]}
                )

            response = ChatResponse(
                success=True,
                client_data=ClientDataResponse.model_validate(service_result["client"]),
                car_data=CarDataResponse.model_validate(service_result["car"]),
                service_data=ServiceDataResponse.model_validate(service_result["service_record"]),
                message=service_result["message"]
            )
            logging.debug(f"Returning chat response: {response.model_dump_json()}")
            return response

        elif intent == 'search_service':
            search_params = gemini_response.get('search_params')
            if not search_params:
                logging.debug("Raising HTTPException for missing search parameters in search_service intent.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={'error': 'Parâmetros de pesquisa ausentes.'}
                )

            search_result = await service_manager.search_service_records(search_params)

            if not search_result["success"]:
                raise HTTPException(
                    status_code=search_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                    detail={'error': search_result["message"]}
                )
            
            formatted_records = []
            if "service_records" in search_result:
                for record in search_result["service_records"]:
                    formatted_records.append(ServiceDataResponse.model_validate(record))

            response = ChatResponse(
                success=True,
                message=search_result["message"],
                service_records=formatted_records
            )
            logging.debug(f"Returning chat response: {response.model_dump_json()}")
            return response
        else:
            logging.debug(f"Raising HTTPException for unknown intent: {intent}.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={'error': f'Intenção desconhecida: {intent}.'}
            )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        logging.debug(f"Raising HTTPException for unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': f'Ocorreu um erro inesperado: {str(e)}'}
        )