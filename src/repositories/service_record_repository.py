from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.core.models import ServiceRecord, Car, Client
from datetime import datetime

class ServiceRecordRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_service_record(self, car_id: int, servico: str, date: datetime, valor: float | None = None, observations: str | None = None) -> ServiceRecord:
        record = ServiceRecord(
            car_id=car_id,
            servico=servico,
            date=date,
            valor=valor,
            observations=observations
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def search_service_records(self, client_name: str | None = None, car_brand: str | None = None, car_model: str | None = None, service_description: str | None = None, active: bool = True) -> list[ServiceRecord]:
        query = select(ServiceRecord).distinct().options(selectinload(ServiceRecord.car).selectinload(Car.owner))

        if client_name:
            query = query.join(Car).join(Client).where(Client.name.ilike(f"%{client_name}%"))
        else:
            query = query.join(Car)

        if car_brand:
            query = query.where(Car.brand.ilike(f"%{car_brand}%"))
        if car_model:
            query = query.where(Car.model.ilike(f"%{car_model}%"))
        if service_description:
            query = query.where(ServiceRecord.servico.ilike(f"%{service_description}%"))
        if active:
            query = query.where(ServiceRecord.active == active)

        result = await self.db.execute(query.order_by(ServiceRecord.created_at.desc()))
        return await result.scalars().all()
