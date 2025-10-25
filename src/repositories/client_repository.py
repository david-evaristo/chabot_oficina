from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.models import Client

class ClientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_client(self, name: str, phone: str | None = None) -> Client:
        query = select(Client).where(Client.name.ilike(name))
        if phone:
            query = query.where(Client.phone == phone)
        result = await self.db.execute(query)
        client = result.scalars().first()

        if not client:
            client = Client(name=name, phone=phone)
            self.db.add(client)
            await self.db.flush()
        return client
