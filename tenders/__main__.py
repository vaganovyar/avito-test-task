from alembic.config import Config
from alembic import command
from fastapi import FastAPI
from fastapi_pagination import add_pagination
from uvicorn import run

from tenders.config import DefaultSettings, get_settings
from tenders.endpoints import list_of_routes
from tenders.utils.common import get_hostname


def run_migrations(script_location: str, dsn: str):
    alembic_cfg = Config("tenders/db/alembic.ini")
    alembic_cfg.set_main_option("script_location", script_location)
    alembic_cfg.set_main_option("sqlalchemy.url", dsn)
    command.upgrade(alembic_cfg, "head")


def bind_routes(application: FastAPI, setting: DefaultSettings) -> None:
    """
    Bind all routes to application.
    """
    for route in list_of_routes:
        application.include_router(route, prefix=setting.PATH_PREFIX)


def get_app() -> FastAPI:
    """
    Creates application and all dependable objects.
    """
    description = "tender service"

    tags_metadata = [
        {
            "name": "Application Health",
            "description": "API health check",
        },
        {
            "name": "Tenders",
            "description": "Tenders information",
        },
        {
            "name": "Bids",
            "description": "Bids information",
        },
    ]

    application = FastAPI(
        title="tenders",
        description=description,
        docs_url="/swagger",
        openapi_url="/openapi",
        version="0.1.0",
        openapi_tags=tags_metadata,
    )
    settings = get_settings()
    bind_routes(application, settings)
    add_pagination(application)
    application.state.settings = settings

    return application


app = get_app()

if __name__ == "__main__":
    settings_for_application = get_settings()
    run_migrations("tenders/db/migrator", settings_for_application.database_uri_sync)
    run(
        "tenders.__main__:app",
        host=get_hostname(settings_for_application.APP_HOST),
        port=settings_for_application.APP_PORT,
        reload=True,
        reload_dirs=["tenders", "tests"],
        log_level="debug",
    )
