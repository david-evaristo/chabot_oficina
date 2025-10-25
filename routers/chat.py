from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Client, Car, ServiceRecord
from utils.gemini_service import process_user_message
from datetime import datetime
import json
import logging
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import selectinload

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ChatMessage(BaseModel):
    message: str

# Pydantic Models for Response
class ClientDataResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]

    class Config:
        from_attributes = True

class CarDataResponse(BaseModel):
    id: int
    brand: str
    model: str
    color: Optional[str]
    year: Optional[int]
    client_id: int

    class Config:
        from_attributes = True

class ServiceDataResponse(BaseModel):
    id: int
    car_id: int
    servico: str
    date: datetime
    valor: Optional[float]
    observations: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    success: bool
    client_data: Optional[ClientDataResponse] = None
    car_data: Optional[CarDataResponse] = None
    service_data: Optional[ServiceDataResponse] = None
    message: str
    service_records: Optional[List[ServiceDataResponse]] = None

@router.post("/api/chat", response_model=ChatResponse)
async def chat_api(chat_message: ChatMessage, db: AsyncSession = Depends(get_db)):
    message = chat_message.message
    logging.info(f"Received chat API request with message: {message}")

    if not message:
        logging.warning("Received empty message in chat API request.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mensagem vazia")

    gemini_response, error = await process_user_message(message)

    if error:
        logging.error(f"Gemini API error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error)

    try:
        intent = gemini_response.get('intent')
        logging.info(f"Gemini detected intent: {intent}")

        if intent == 'create_service':
            data = gemini_response.get('data')
            if not data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={'error': 'Dados ausentes para criação de serviço.'}
                )

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

            if not client_name or not car_brand or not car_model or not service_description:
                logging.warning(f"Insufficient information for service creation: {data}")
                return ChatResponse(
                    success=False,
                    message="Por favor, forneça nome do cliente, marca, modelo do carro e descrição do serviço."
                )

            # 1. Handle Client
            client = None
            if client_name:
                client_query = select(Client).where(Client.name.ilike(client_name))
                if client_phone:
                    client_query = client_query.where(Client.phone == client_phone)
                client_result = await db.execute(client_query)
                client = client_result.scalars().first()

            if not client:
                client = Client(name=client_name, phone=client_phone)
                db.add(client)
                await db.flush() # Ensure client.id is populated
                logging.info(f"Prepared to create new client: {client_name}")
            else:
                logging.info(f"Found existing client: {client.to_dict()}")

            # 2. Handle Car
            car = None
            if client and car_brand and car_model:
                car_query = select(Car).where(
                    Car.client_id == client.id,
                    Car.brand.ilike(car_brand),
                    Car.model.ilike(car_model)
                )
                if car_color:
                    car_query = car_query.where(Car.color.ilike(car_color))
                if car_year:
                    car_query = car_query.where(Car.year == car_year)
                car_result = await db.execute(car_query)
                car = car_result.scalars().first()

            if not car:
                car = Car(
                    client_id=client.id,
                    brand=car_brand,
                    model=car_model,
                    color=car_color,
                    year=car_year
                )
                db.add(car)
                await db.flush() # Ensure car.id is populated
                logging.info(f"Prepared to create new car for client {client.name}: {car_brand} {car_model}")
            else:
                logging.info(f"Found existing car: {car.to_dict()}")

            # 3. Handle ServiceRecord
            service_date = None
            if service_date_str:
                try:
                    service_date = datetime.strptime(service_date_str, '%Y-%m-%d').date()
                except ValueError:
                    logging.warning(f"Could not parse date '{service_date_str}'. Using current date.")
                    pass

            record = ServiceRecord(
                car_id=car.id,
                servico=service_description,
                date=service_date or datetime.now().date(),
                valor=service_valor,
                observations=service_observations
            )

            db.add(record)

            await db.commit()
            await db.refresh(client)
            await db.refresh(car)
            await db.refresh(record)
            logging.info(f"Successfully added new service record: {record.to_dict()}")

            return ChatResponse(
                success=True,
                client_data=ClientDataResponse.model_validate(client),
                car_data=CarDataResponse.model_validate(car),
                service_data=ServiceDataResponse.model_validate(record),
                message=f'Serviço registrado com sucesso para {client.name} - {car.brand} {car.model}'
            )

        elif intent == 'search_service':
            search_params = gemini_response.get('search_params')
            if not search_params:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={'error': 'Parâmetros de pesquisa ausentes.'}
                )

            client_name = search_params.get('client_name')
            car_brand = search_params.get('car_brand')
            car_model = search_params.get('car_model')
            service_description = search_params.get('service_description')

            query = select(ServiceRecord).options(selectinload(ServiceRecord.car).selectinload(Car.owner))

            # Join Car and Client tables once if client_name is provided, otherwise just Car
            if client_name:
                query = query.join(Car).join(Client).where(Client.name.ilike(f"%{client_name}%"))
            else:
                query = query.join(Car) # Join Car table if not already joined via client_name

            if car_brand:
                query = query.where(Car.brand.ilike(f"%{car_brand}%"))
            if car_model:
                query = query.where(Car.model.ilike(f"%{car_model}%"))
            if service_description:
                query = query.where(ServiceRecord.servico.ilike(f"%{service_description}%"))

            if not client_name and not car_brand and not car_model and not service_description:
                return ChatResponse(
                    success=False,
                    message="Por favor, forneça nome do cliente, marca, modelo do carro ou descrição do serviço para a pesquisa."
                )

            result = await db.execute(query.order_by(ServiceRecord.created_at.desc()))
            service_records = result.scalars().all()

            if service_records:
                formatted_records = []
                for record in service_records:
                    client_info = record.car.owner.name if record.car and record.car.owner else 'N/A'
                    car_info = f"{record.car.brand} {record.car.model}" if record.car else 'N/A'
                    formatted_records.append(ServiceDataResponse.model_validate(record))

                response_message = "✅ Serviços encontrados:\n"
                for record in service_records:
                    response_message += (
                        f"--- Detalhes do Serviço ---\n"
                        f"👤 Cliente: {record.car.owner.name if record.car and record.car.owner else 'N/A'}\n"
                        f"🚗 Carro: {record.car.brand} {record.car.model} ({record.car.color or 'N/A'}, {record.car.year or 'N/A'})\n"
                        f"🛠️ Serviço: {record.servico}\n"
                        f"📅 Data: {record.date.strftime('%Y-%m-%d') or 'N/A'}\n"
                        f"💰 Valor: {record.valor or 'N/A'}\n"
                        f"---------------------------\n"
                    )
                return ChatResponse(
                    success=True,
                    message=response_message,
                    service_records=formatted_records
                )
            else:
                return ChatResponse(
                    success=False,
                    message="Nenhum serviço encontrado com os critérios fornecidos."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={'error': f'Intenção desconhecida: {intent}.'}
            )

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'error': f'Ocorreu um erro inesperado: {str(e)}'}
        )