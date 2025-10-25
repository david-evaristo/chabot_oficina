from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.models import Car

class CarRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_car(self, client_id: int, brand: str, model: str, color: str | None = None, year: int | None = None) -> Car:
        query = select(Car).where(
            Car.client_id == client_id,
            Car.brand.ilike(brand),
            Car.model.ilike(model)
        )
        if color:
            query = query.where(Car.color.ilike(color))
        if year:
            query = query.where(Car.year == year)
        result = await self.db.execute(query)
        car = result.scalars().first()

        if not car:
            car = Car(
                client_id=client_id,
                brand=brand,
                model=model,
                color=color,
                year=year
            )
            self.db.add(car)
            await self.db.flush()
        return car
