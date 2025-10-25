from sqlalchemy import Column, Integer, String, Date, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.core.database import Base # Import Base from the new database.py

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    cars = relationship("Car", back_populates="owner")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }

class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=False)
    color = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("Client", back_populates="cars")
    service_records = relationship("ServiceRecord", back_populates="car")

    def to_dict(self):
        return {
            'id': self.id,
            'brand': self.brand,
            'model': self.model,
            'color': self.color,
            'year': self.year,
            'client_id': self.client_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None
        }

class ServiceRecord(Base):
    __tablename__ = "service_records"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"))
    servico = Column(String(200), nullable=False)
    date = Column(Date, nullable=False)
    valor = Column(Float, nullable=True)
    observations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    active = Column(Boolean, default=True)

    car = relationship("Car", back_populates="service_records")

    def to_dict(self):
        return {
            'id': self.id,
            'car_id': self.car_id,
            'servico': self.servico,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'valor': self.valor,
            'observations': self.observations,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None,
            'active': self.active
        }