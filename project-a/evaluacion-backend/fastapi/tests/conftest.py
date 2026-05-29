import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.core.config import settings
from src.main import app
from src.db.postgres import get_db_session

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
def engine():
    return create_async_engine(settings.database_url, pool_pre_ping=True)

@pytest.fixture
async def db_session(engine):
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    
    yield session
    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest.fixture(autouse=True)
def override_db(db_session):
    async def _override():
        yield db_session

    app.dependency_overrides[get_db_session] = _override
    yield
    app.dependency_overrides.clear()
