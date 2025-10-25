
import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.service_management import ServiceManagementService
from src.schemas.chat_schemas import ChatResponse, ClientDataResponse, CarDataResponse, ServiceDataResponse

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.service_manager = ServiceManagementService(self.db)

    async def handle_intent(self, gemini_response: dict) -> ChatResponse:
        """
        Processes the Gemini response and routes to the correct service based on intent.
        """
        intent = gemini_response.get('intent')
        logging.info(f"Handling intent: {intent}")

        try:
            # Aceitar variações do intent de criação de serviço
            if intent in ('record_service', 'create_service', 'create_service_record', 'register_service'):
                return await self._handle_create_service(gemini_response)
            elif intent in ('search_service', 'search'):
                return await self._handle_search_service(gemini_response)
            else:
                logging.debug(f"Raising HTTPException for unknown intent: {intent}.")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={'error': f'Intenção desconhecida: {intent}.'}
                )
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred while handling intent '{intent}': {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={'error': f'Ocorreu um erro inesperado ao processar a intenção: {str(e)}'}
            )

    async def _handle_create_service(self, gemini_response: dict) -> ChatResponse:
        data = gemini_response.get('data')
        if not data:
            logging.debug("Raising HTTPException for missing data in create_service intent.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={'error': 'Dados ausentes para criação de serviço.'}
            )
        
        service_result = await self.service_manager.create_service_record(data)

        if not service_result["success"]:
            raise HTTPException(
                status_code=service_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail={'error': service_result["message"]}
            )

        return ChatResponse(
            success=True,
            client_data=ClientDataResponse.model_validate(service_result["client"]),
            car_data=CarDataResponse.model_validate(service_result["car"]),
            service_data=ServiceDataResponse.model_validate(service_result["service_record"]),
            message=service_result["message"]
        )

    async def _handle_search_service(self, gemini_response: dict) -> ChatResponse:
        search_params = gemini_response.get('search_params')
        if not search_params:
            logging.debug("Raising HTTPException for missing search parameters in search_service intent.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={'error': 'Parâmetros de pesquisa ausentes.'}
            )

        search_result = await self.service_manager.search_service_records(search_params)

        if not search_result["success"]:
            raise HTTPException(
                status_code=search_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail={'error': search_result["message"]}
            )
        
        formatted_records = []
        if "service_records" in search_result:
            for record in search_result["service_records"]:
                formatted_records.append(ServiceDataResponse.model_validate(record))

        return ChatResponse(
            success=True,
            message=search_result["message"],
            service_records=formatted_records
        )

