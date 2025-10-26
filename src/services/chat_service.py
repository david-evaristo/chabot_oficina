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
        intent = gemini_response.intent
        logging.info(f"Handling intent: {intent}")

        try:
            # Aceitar variações do intent de criação de serviço
            if intent in ('record_service', 'create_service', 'create_service_record', 'register_service'):
                return await self._handle_create_service(gemini_response)
            elif intent in ('search_service', 'search'):
                return await self._handle_search_service(gemini_response)
            elif intent == 'list_active_services':
                return await self._handle_list_active_services()
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
        data = gemini_response.data
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

        service_record = ServiceDataResponse.model_validate(service_result["service_record"])
        formatted_message = (
            "✅ **Detalhes do Serviço Registrado:**\n"
            f"    **Cliente:** {service_record.car.owner.name if service_record.car and service_record.car.owner else 'Não informado'}\n"
            f"    **Veículo:** {service_record.car.brand if service_record.car else 'Não informado'} {service_record.car.model if service_record.car else ''} ({service_record.car.year if service_record.car else 'Não informado'})\n"
            f"    **Serviço:** {service_record.servico}\n"
            f"    **Data:** {service_record.date.strftime('%Y-%m-%d') if service_record.date else 'Não informada'}\n"
            f"    **Custo:** R$ {service_record.valor if service_record.valor is not None else 'Não informado'}\n"
            f"    **Observações:** {service_record.observations if service_record.observations else 'Nenhuma'}"
        )
        return ChatResponse(
            success=True,
            service_data=service_record,
            message=formatted_message
        )

    async def _handle_search_service(self, gemini_response: dict) -> ChatResponse:
        search_params = gemini_response.search_params

        # If search_params are missing, assume the intent is to list all active services
        if not search_params:
            logging.info("No search parameters provided, listing all active services.")
            return await self._handle_list_active_services()

        search_result = await self.service_manager.search_service_records(search_params)

        if not search_result["success"]:
            raise HTTPException(
                status_code=search_result.get("status_code", status.HTTP_400_BAD_REQUEST),
                detail={'error': search_result["message"]}
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
            logging.debug(f"\n\nLista de serviços encontrados: {formatted_list}")
            message_ = f"Encontrei múltiplos serviços ativos. Por favor, especifique a qual você se refere\n{formatted_list}"
            logging.debug(f"\n\nmessage encontrados: {message_}")
            return ChatResponse(
                success=True,
                message=message_,
                service_records=[ServiceDataResponse.model_validate(record) for record in service_records]
            )
        else:
            # If only one record is found, return its details
            record = service_records[0]
            formatted_record = ServiceDataResponse.model_validate(record)
            formatted_message = (
                "✅ **Detalhes do Serviço Encontrado:**\n"
                f"    **Cliente:** {record.car.owner.name if record.car and record.car.owner else 'Não informado'}\n"
                f"    **Veículo:** {record.car.brand if record.car else 'Não informado'} {record.car.model if record.car else ''} ({record.car.year if record.car else 'Não informado'})\n"
                f"    **Serviço:** {record.servico}\n"
                f"    **Data:** {record.date.strftime('%Y-%m-%d') if record.date else 'Não informada'}\n"
                f"    **Custo:** R$ {record.valor if record.valor is not None else 'Não informado'}\n"
                f"    **Observações:** {record.observations if record.observations else 'Nenhuma'}"
            )
            return ChatResponse(
                success=True,
                message=formatted_message,
                service_records=[formatted_record]
            )

    async def _handle_list_active_services(self) -> ChatResponse:
        search_result = await self.service_manager.search_service_records(search_params={})

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
                message="Nenhum serviço ativo encontrado.",
                service_records=[]
            )

        formatted_list = self._format_service_records_for_response(service_records)
        return ChatResponse(
            success=True,
            message=f"✅ **Serviços ativos:**\n{formatted_list}",
            service_records=[ServiceDataResponse.model_validate(record) for record in service_records]
        )

    def _format_service_records_for_response(self, records: list) -> str:
        """
        Formats a list of service records into a human-readable string for the chat response.
        """
        formatted_strings = []
        for record in records:
            client_name = record.car.owner.name if record.car and record.car.owner else "Desconhecido"
            car_info = f"{record.car.brand or ''} {record.car.model or ''}".strip() or "Carro Desconhecido"
            service_date = record.date.strftime('%Y-%m-%d') if record.date else "Data Desconhecida"

            formatted_strings.append(
                f"**Cliente:** {client_name}\n"
                f"&emsp;**Carro:** {car_info}\n"
                f"&emsp;**Serviço:** {record.servico}\n"
                f"&emsp;**Data:** {service_date}\n"
                "───────────────────"
            )
        return "\n".join(formatted_strings)