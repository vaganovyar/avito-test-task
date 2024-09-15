from os import environ

from pydantic_settings import BaseSettings


class DefaultSettings(BaseSettings):
    """
    Default configs for application.

    Usually, we have three environments: for development, testing and production.
    But in this situation, we only have standard settings for local development.
    """

    ENV: str = environ.get("ENV", "local")
    PATH_PREFIX: str = environ.get("PATH_PREFIX", "/api")
    SERVER_ADDRESS: str = environ.get("SERVER_ADDRESS", "0.0.0.0:8080")
    SERVER_ADDRESS = SERVER_ADDRESS.split(":")[0]
    APP_HOST: str = environ.get("APP_HOST", f"http://{SERVER_ADDRESS}")
    APP_PORT: int = int(environ.get("APP_PORT", 8080))

    POSTGRES_CONN: str = environ.get("POSTGRES_CONN", "postgres://postgres:postgres@localhost:5432/postgres")
    POSTGRES_DB: str = environ.get("POSTGRES_DATABASE", "postgres")
    POSTGRES_HOST: str = environ.get("POSTGRES_HOST", "localhost")
    POSTGRES_USER: str = environ.get("POSTGRES_USERNAME", "postgres")
    POSTGRES_PORT: int = int(environ.get("POSTGRES_PORT", "5432")[-4:])
    POSTGRES_PASSWORD: str = environ.get("POSTGRES_PASSWORD", "postgres")
    DB_CONNECT_RETRY: int = environ.get("DB_CONNECT_RETRY", 20)
    DB_POOL_SIZE: int = environ.get("DB_POOL_SIZE", 15)

    # to get a string like this run: "openssl rand -hex 32"
    SECRET_KEY: str = environ.get("SECRET_KEY", "")
    ALGORITHM: str = environ.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

    @property
    def database_settings(self) -> dict:
        """
        Get all settings for connection with database.
        """
        return {
            "database": self.POSTGRES_DB,
            "user": self.POSTGRES_USER,
            "password": self.POSTGRES_PASSWORD,
            "host": self.POSTGRES_HOST,
            "port": self.POSTGRES_PORT,
        }

    @property
    def database_uri(self) -> str:
        """
        Get uri for connection with database.
        """
        return "postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}".format(
            **self.database_settings,
        )

    @property
    def database_uri_sync(self) -> str:
        """
        Get uri for connection with database.
        """
        return "postgresql://{user}:{password}@{host}:{port}/{database}".format(
            **self.database_settings,
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
