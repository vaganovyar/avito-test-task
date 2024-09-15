from asyncio import get_event_loop_policy
from types import SimpleNamespace

import pytest
from alembic.command import upgrade
from alembic.config import Config
from httpx import AsyncClient
from mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from tests.utils import make_alembic_config

import tenders.utils as utils_module
from tenders.__main__ import get_app
from tenders.config.utils import get_settings
from tenders.db.connection import SessionManager


@pytest.fixture(name="event_loop", scope="session")
def get_event_loop():
    policy = get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(name="postgres")
def get_postgres() -> str:
    """
     Create temp database for test
    """

    settings = get_settings()
    tmp_url = settings.database_uri_sync

    if not database_exists(tmp_url):
        create_database(tmp_url)

    try:
        yield settings.database_uri
    finally:
        drop_database(tmp_url)


def run_upgrade(connection, cfg):
    cfg.attributes["connection"] = connection
    upgrade(cfg, "head")


async def run_async_upgrade(config: Config, database_uri: str):
    async_engine = create_async_engine(database_uri, echo=True)
    async with async_engine.begin() as conn:
        await conn.run_sync(run_upgrade, config)


@pytest.fixture(name="alembic_config")
def get_alembic_config(postgres) -> Config:
    """
    Создает файл конфигурации для alembic.
    """
    cmd_options = SimpleNamespace(config="bookmarker/db/", name="alembic", pg_url=postgres, raiseerr=False, x=None)
    return make_alembic_config(cmd_options)


@pytest.fixture(name="alembic_engine")
def get_alembic_engine():
    """
    Override this fixture to provide pytest-alembic powered tests with a database handle.
    """
    settings = get_settings()
    return create_async_engine(settings.database_uri_sync, echo=True)


@pytest.fixture(name="migrated_postgres")
async def get_migrated_postgres(postgres, alembic_config: Config):
    """
    Проводит миграции.
    """
    await run_async_upgrade(alembic_config, postgres)


@pytest.fixture(name="client")
async def get_client(migrated_postgres, manager: SessionManager = SessionManager()) -> AsyncClient:
    """
    Returns a client that can be used to interact with the application.
    """
    if migrated_postgres:  # без этой строки не проходит линтер
        pass
    app = get_app()
    manager.refresh()  # без вызова метода изменения конфига внутри фикстуры postgres не подтягиваются в класс
    utils_module.check_website_exist = AsyncMock(return_value=(True, "Status code < 400"))
    yield AsyncClient(app=app, base_url="http://test")


@pytest.fixture(name="engine_async")
async def get_engine_async(postgres) -> AsyncEngine:
    engine = create_async_engine(postgres, future=True)
    yield engine
    await engine.dispose()


@pytest.fixture(name="session_factory_async")
def get_session_factory_async(engine_async) -> sessionmaker:
    return sessionmaker(engine_async, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(name="session")
async def get_session(session_factory_async) -> AsyncSession:
    async with session_factory_async() as async_factory:
        yield async_factory
