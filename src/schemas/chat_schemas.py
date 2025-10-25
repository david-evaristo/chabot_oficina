from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, RootModel

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

class CreateServiceSchema(BaseModel):
    intent: Literal["record_service"]
    data: CreateServiceData

class SearchParamsData(BaseModel):
    client_name: Optional[str] = Field(None, alias="client_name")
    car_brand: Optional[str] = Field(None, alias="car_brand")
    car_model: Optional[str] = Field(None, alias="car_model")
    service_description: Optional[str] = Field(None, alias="service_description")

class SearchParamsSchema(BaseModel):
    intent: Literal["search_service"]
    search_params: SearchParamsData

class GeminiResponse(BaseModel):
    intent: Literal["record_service", "search_service"]
    create_service_data: Optional[CreateServiceSchema] = None
    search_params_data: Optional[SearchParamsSchema] = None

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
