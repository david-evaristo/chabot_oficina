from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

# Pydantic Models for Client
class ClientCreate(BaseModel):
    name: str
    phone: Optional[str] = None

class ClientResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]

    class Config:
        from_attributes = True

# Pydantic Models for Car
class CarCreate(BaseModel):
    brand: str
    model: str
    color: Optional[str] = None
    year: Optional[int] = None
    client_id: int

class CarResponse(BaseModel):
    id: int
    brand: str
    model: str
    color: Optional[str]
    year: Optional[int]
    client_id: int

    class Config:
        from_attributes = True

# Pydantic Models for ServiceRecord
class ServiceRecordCreate(BaseModel):
    car_id: int
    servico: str
    date: Optional[datetime] = None
    valor: Optional[float] = None
    observations: Optional[str] = None

class ServiceRecordResponse(BaseModel):
    id: int
    car_id: int
    servico: str
    date: datetime
    valor: Optional[float]
    observations: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
