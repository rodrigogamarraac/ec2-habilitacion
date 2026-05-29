import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
load_dotenv()


DB_URL=os.getenv("POSTGRES_URL")
engine = create_async_engine(DB_URL,echo=True)

AsyncSessionLocal=async_sessionmaker(engine,expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
