from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    db_url:str

    class Config:
        env_file = ".env"

_:AppConfig

def get_config() -> AppConfig:
    if not _:
        _ = AppConfig()
        return _
    return _