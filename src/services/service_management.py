import logging
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.car_repository import CarRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.service_record_repository import ServiceRecordRepository

logger = logging.getLogger(__name__)

class ServiceManagementService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client_repo = ClientRepository(db)
        self.car_repo = CarRepository(db)
        self.service_repo = ServiceRecordRepository(db)

    async def create_service_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        client_name = data.get('client_name')
        client_phone = data.get('client_phone')
        car_brand = data.get('car_brand')
        car_model = data.get('car_model')
        car_color = data.get('car_color')
        car_year = data.get('car_year')
        service_description = data.get('service_description')
        service_date_str = data.get('service_date')
        service_valor = data.get('service_valor')
        service_observations = data.get('service_observations')

        if not client_name or not car_model or not service_description:
            return {"success": False, "message": "Por favor, forneça nome do cliente, modelo do carro e descrição do serviço.", "status_code": 400}

        client = await self.client_repo.get_or_create_client(name=client_name, phone=client_phone)
        logger.info(f"Client handled: {client.name}")

        car = await self.car_repo.get_or_create_car(
            client_id=client.id,
            brand=car_brand,
            model=car_model,
            color=car_color,
            year=car_year
        )
        logger.info(f"Car handled: {car.brand} {car.model}")

        service_date = None
        if service_date_str:
            try:
                service_date = datetime.strptime(service_date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Could not parse date '{service_date_str}'. Using current date.")
                pass
        
        record = await self.service_repo.create_service_record(
            car_id=car.id,
            servico=service_description,
            date=service_date or datetime.now().date(),
            valor=service_valor,
            observations=service_observations
        )
        logger.info(f"Service record created: {record.servico}")

        await self.db.commit()
        await self.db.refresh(client)
        await self.db.refresh(car)
        await self.db.refresh(record)

        return {
            "success": True,
            "client": client,
            "car": car,
            "service_record": record,
            "message": f'Serviço registrado com sucesso para {client.name} - {car.brand} {car.model}'
        }

    async def search_service_records(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        client_name = search_params.get('client_name')
        car_brand = search_params.get('car_brand')
        car_model = search_params.get('car_model')
        service_description = search_params.get('service_description')

        if not client_name and not car_brand and not car_model and not service_description:
            return {"success": False, "message": "Por favor, forneça nome do cliente, marca, modelo do carro ou descrição do serviço para a pesquisa.", "status_code": 400}

        service_records = await self.service_repo.search_service_records(
            client_name=client_name,
            car_brand=car_brand,
            car_model=car_model,
            service_description=service_description,
            active=True
        )

        if service_records:
            response_message = "✅ Serviços encontrados:"
            return {"success": True, "message": response_message, "service_records": service_records}
        else:
            return {"success": False, "message": "Nenhum serviço encontrado com os critérios fornecidos.", "status_code": 200}
