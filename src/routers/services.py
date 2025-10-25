from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.models import Client, Car, ServiceRecord
from datetime import datetime
from typing import List
from sqlalchemy import select
from src.schemas.service_schemas import ClientCreate, ClientResponse, CarCreate, CarResponse, ServiceRecordCreate, ServiceRecordResponse

router = APIRouter()

# Client Endpoints
@router.post("/api/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreate, db: AsyncSession = Depends(get_db)):
    db_client = Client(**client_data.model_dump())
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client

@router.get("/api/clients", response_model=List[ClientResponse])
async def get_clients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).order_by(Client.name))
    clients = result.scalars().all()
    return clients

@router.get("/api/clients/{client_id}/cars", response_model=List[CarResponse])
async def get_cars_by_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Car).where(Car.client_id == client_id))
    cars = result.scalars().all()
    if not cars:
        raise HTTPException(status_code=404, detail="No cars found for this client")
    return cars

# Car Endpoints
@router.post("/api/cars", response_model=CarResponse, status_code=status.HTTP_201_CREATED)
async def create_car(car_data: CarCreate, db: AsyncSession = Depends(get_db)):
    # Check if client_id exists
    client = await db.get(Client, car_data.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    db_car = Car(**car_data.model_dump())
    db.add(db_car)
    await db.commit()
    await db.refresh(db_car)
    return db_car

@router.get("/api/cars", response_model=List[CarResponse])
async def get_cars(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Car).order_by(Car.brand, Car.model))
    cars = result.scalars().all()
    return cars

@router.get("/api/cars/{car_id}/service_records", response_model=List[ServiceRecordResponse])
async def get_service_records_by_car(car_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceRecord).where(ServiceRecord.car_id == car_id).order_by(ServiceRecord.date.desc()))
    service_records = result.scalars().all()
    if not service_records:
        raise HTTPException(status_code=404, detail="No service records found for this car")
    return service_records

# ServiceRecord Endpoints
@router.post("/api/services", response_model=ServiceRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_service(service_data: ServiceRecordCreate, db: AsyncSession = Depends(get_db)):
    # Check if car_id exists
    car = await db.get(Car, service_data.car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    db_service_record = ServiceRecord(
        car_id=service_data.car_id,
        servico=service_data.servico,
        date=service_data.date.date() if service_data.date else datetime.now().date(),
        valor=service_data.valor,
        observations=service_data.observations
    )
    db.add(db_service_record)
    await db.commit()
    await db.refresh(db_service_record)
    return db_service_record

@router.get("/api/services", response_model=List[ServiceRecordResponse])
async def get_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceRecord).order_by(ServiceRecord.created_at.desc()))
    service_records = result.scalars().all()
    return service_records

@router.get("/api/services/{service_id}", response_model=ServiceRecordResponse)
async def get_service_record(service_id: int, db: AsyncSession = Depends(get_db)):
    service_record = await db.get(ServiceRecord, service_id)
    if not service_record:
        raise HTTPException(status_code=404, detail="Service record not found")
    return service_record

@router.put("/api/services/{service_id}", response_model=ServiceRecordResponse)
async def update_service_record(service_id: int, service_data: ServiceRecordCreate, db: AsyncSession = Depends(get_db)):
    db_service_record = await db.get(ServiceRecord, service_id)
    if not db_service_record:
        raise HTTPException(status_code=404, detail="Service record not found")

    # Check if car_id exists if it's being updated
    if service_data.car_id and service_data.car_id != db_service_record.car_id:
        car = await db.get(Car, service_data.car_id)
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")

    for field, value in service_data.model_dump(exclude_unset=True).items():
        setattr(db_service_record, field, value)

    await db.commit()
    await db.refresh(db_service_record)
    return db_service_record

@router.delete("/api/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_record(service_id: int, db: AsyncSession = Depends(get_db)):
    db_service_record = await db.get(ServiceRecord, service_id)
    if not db_service_record:
        raise HTTPException(status_code=404, detail="Service record not found")

    await db.delete(db_service_record)
    await db.commit()
    return {"message": "Service record deleted successfully"}
