# user-service/config.py
import os
from dataclasses import dataclass

@dataclass
class ServerConfig:
    host: str = '0.0.0.0'
    port: int = 8001

@dataclass
class DatabaseConfig:
    host: str = os.getenv('DATABASE_HOST', 'postgresql-service')
    port: int = int(os.getenv('DATABASE_PORT', '5432'))
    name: str = os.getenv('DATABASE_NAME', 'monitoring_db')
    user: str = os.getenv('DATABASE_USER', 'app_user')
    password: str = os.getenv('DATABASE_PASSWORD', 'password')

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

@dataclass
class CacheConfig:
    host: str = os.getenv('REDIS_HOST', 'redis-service')
    port: int = int(os.getenv('REDIS_PORT', '6379'))
    password: str = os.getenv('REDIS_PASSWORD', '')
    default_ttl: int = 300

class Config:
    def __init__(self):
        self.server = ServerConfig()
        self.database = DatabaseConfig()
        self.cache = CacheConfig()
        if self.cache.password:
            self.REDIS_URL = f"redis://:{self.cache.password}@{self.cache.host}:{self.cache.port}"
        else:
            self.REDIS_URL = f"redis://{self.cache.host}:{self.cache.port}"

config = Config()
