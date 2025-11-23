from enum import Enum
from typing import Union

from pydantic_settings import BaseSettings

class EnvConfig(BaseSettings):
    # DB
    db_url:str
    db_sync_url:str
    db_user:str
    db_password:str
    db_host:str
    db_port:str
    db_name:str
    # REDIS
    redis_port:str
    # LOGGING
    log_dir:str
    # ARTIFACTS
    obj_dir:str
    mdl_dir:str
    # API KEYS
    alpha_vantage_api_key:str
    polygon_api_key:str
    news_api_key:str #TODO

    class Config:
        env_file = ".env"

class ConfigTypes(Enum):
    ENV = "env"

def get_config(type:ConfigTypes=ConfigTypes.ENV) -> Union[EnvConfig, None]:
    if type == ConfigTypes.ENV:
        return EnvConfig()
    return None
    