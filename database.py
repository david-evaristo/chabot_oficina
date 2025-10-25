from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config

DATABASE_URL = Config.DATABASE_URL # Directly use the URL from Config

engine = create_async_engine(DATABASE_URL, echo=True, connect_args={"timeout": 15})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()

async def init_db_fastapi():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)