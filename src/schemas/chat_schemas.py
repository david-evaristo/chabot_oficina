from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    message: str

class CreateServiceData(BaseModel):
    client_name: Optional[str] = Field(None, alias="client_name")
    client_phone: Optional[str] = Field(None, alias="client_phone")
    car_brand: Optional[str] = Field(None, alias="car_brand")
    car_model: Optional[str] = Field(None, alias="car_model")
    car_color: Optional[str] = Field(None, alias="car_color")
    car_year: Optional[int] = Field(None, alias="car_year")
    service_description: str = Field(..., alias="service_description")
    service_date: Optional[str] = Field(None, alias="service_date")
    service_valor: Optional[float] = Field(None, alias="service_valor")
    service_observations: Optional[str] = Field(None, alias="service_observations")

class SearchParamsData(BaseModel):
    client_name: Optional[str] = Field(None, alias="client_name")
    car_brand: Optional[str] = Field(None, alias="car_brand")
    car_model: Optional[str] = Field(None, alias="car_model")
    service_description: Optional[str] = Field(None, alias="service_description")

class GeminiResponse(BaseModel):
    intent: Literal["record_service", "search_service"]
    data: Optional[CreateServiceData] = None
    search_params: Optional[SearchParamsData] = None

# Pydantic Models for Response
class ClientDataResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]

    class Config:
        from_attributes = True

class CarDataResponse(BaseModel):
    id: int
    brand: Optional[str]
    model: str
    color: Optional[str]
    year: Optional[int]
    owner: ClientDataResponse

    class Config:
        from_attributes = True

class ServiceDataResponse(BaseModel):
    id: int
    servico: str
    date: datetime
    valor: Optional[float]
    observations: Optional[str]
    car: CarDataResponse

    class Config:
        from_attributes = True

class ChatResponse(BaseModel):
    success: bool
    message: str
    service_data: Optional[ServiceDataResponse] = None
    service_records: Optional[List[ServiceDataResponse]] = None