from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    upload_dir: str = "uploads"
    output_dir: str = "outputs"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
