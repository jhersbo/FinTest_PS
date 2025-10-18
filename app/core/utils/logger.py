import logging
from logging import Logger
from datetime import date

from ..config.config import get_config

CONFIG = get_config()
env_logdir = CONFIG.log_dir
env_logdir = env_logdir if env_logdir is not None else "../logs"

def get_logger(name:str="primary") -> Logger:
    L = logging.getLogger(name=name)
    L.setLevel(logging.INFO)
    # Stream handler
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    stream_handler.setFormatter(formatter)
    # File handler
    file_handler = logging.FileHandler(filename=f"{env_logdir}/{str(date.today()).replace('-', '')}.log")
    file_handler.setFormatter(formatter)

    if not L.hasHandlers():
        L.addHandler(stream_handler)
        L.addHandler(file_handler)

    return L
    
