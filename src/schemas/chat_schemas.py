from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

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
