from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    # DB
    db_url:str
    db_user:str
    db_password:str
    db_host:str
    db_port:str
    db_name:str
    # LOGGING
    log_dir:str
    # API KEYS
    alpha_vantage_api_key:str
    polygon_api_key:str
    news_api_key:str #TODO
    # AUTHENTICATION
    jwt_secret:str

    class Config:
        env_file = ".env"

def get_config() -> AppConfig:
    return AppConfig()