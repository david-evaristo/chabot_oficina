
import logging
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.service_management import ServiceManagementService
from src.schemas.chat_schemas import ChatResponse, ServiceDataResponse

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
        if not search_result["success"]:
            return ChatResponse(
                success=False,
                message=search_result["message"],
                service_records=[]
            )

        service_records = search_result.get("service_records", [])

        if not service_records:
            return ChatResponse(
                success=True,
                message="Nenhum serviço ativo encontrado com os critérios fornecidos.",
                service_records=[]
            )
        
        if len(service_records) > 1:
            # If multiple records are found, ask for clarification
            formatted_list = self._format_service_records_for_response(service_records)
            return ChatResponse(
                success=True,
                message=f"Encontrei múltiplos serviços ativos. Por favor, especifique a qual você se refere:\n{formatted_list}",
                service_records=[ServiceDataResponse.model_validate(record) for record in service_records]
            )
        else:
            # If only one record is found, return its details
            record = service_records[0]
            formatted_record = ServiceDataResponse.model_validate(record)
            return ChatResponse(
                success=True,
                message=f"✅ Serviço encontrado para {record.car.owner.name} - {record.car.brand} {record.car.model}: {record.servico} em {record.date.strftime('%Y-%m-%d')}. Valor: R${record.valor or 'Não informado'}. Observações: {record.observations or 'Nenhuma'}.",
                service_records=[formatted_record]
            )

    def _format_service_records_for_response(self, records: list) -> str:
        """
        Formats a list of service records into a human-readable string for the chat response.
        """
        formatted_strings = []
        for i, record in enumerate(records):
            client_name = record.car.owner.name if record.car and record.car.owner else "Desconhecido"
            car_info = f"{record.car.brand} {record.car.model}" if record.car else "Carro Desconhecido"
            service_desc = record.servico
            service_date = record.date.strftime('%Y-%m-%d') if record.date else "Data Desconhecida"
            formatted_strings.append(f"{i+1}. Cliente: {client_name}, Carro: {car_info}, Serviço: {service_desc}, Data: {service_date}")
        return "\n".join(formatted_strings)

