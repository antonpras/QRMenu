from pydantic_settings import BaseSettings
from pydantic import AnyUrl

class Settings(BaseSettings):
    JWT_SECRET: str = "dev-secret"
    BASE_PUBLIC_URL: AnyUrl = "https://example.com"
    R2_ENDPOINT: AnyUrl | None = None
    R2_ACCESS_KEY: str | None = None
    R2_SECRET_KEY: str | None = None
    R2_BUCKET: str = "qrmenu-media"
    MIDTRANS_SERVER_KEY: str | None = None
    MIDTRANS_CLIENT_KEY: str | None = None
    DATABASE_URL: str = "sqlite:///./qrmenu.db"
    class Config:
        env_file = ".env"
settings = Settings()
