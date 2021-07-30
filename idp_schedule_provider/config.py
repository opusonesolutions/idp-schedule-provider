import json
import os
from functools import lru_cache
from typing import Dict

from pydantic import BaseSettings


class Settings(BaseSettings):
    jwt_algorithm: str = os.getenv("JWT_ALG", "HS256")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "INSECURE_SECRET_KEY")
    jwt_clients: Dict[str, str] = json.loads(os.getenv("JWT_CLIENTS", '{"gridos": "gridos_pw"}'))


@lru_cache()
def get_settings():
    return Settings()
