from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
import os
from app.models.lead import Base

from sqlalchemy import text

engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False,
    connect_args={"timeout": 30},
    pool_pre_ping=True
)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    # Ensure uploads directory exists
    os.makedirs("./data/uploads", exist_ok=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA journal_mode=WAL"))

async def get_db():
    async with async_session() as session:
        yield session
