from dataclasses import dataclass
from environs import Env
import re

@dataclass
class DatabaseConfig:
    database_url: str

    def __post_init__(self):
        # Проверяем корректность URL базы данных
        if not self.database_url:
            raise ValueError("DATABASE_URL cannot be empty")

        # Убеждаемся, что используется правильный диалект
        if not any(dialect in self.database_url for dialect in ['postgresql', 'sqlite', 'mysql']):
            raise ValueError(f"Invalid database URL format: {self.database_url}")

@dataclass
class Config:
    db: DatabaseConfig
    debug: bool

def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)

    database_url = env("DATABASE_URL")

    # Дополнительная обработка URL если нужно
    if database_url.startswith('postgres://'):
        # Заменяем устаревший формат postgres:// на postgresql://
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    return Config(
        db=DatabaseConfig(database_url=database_url),
        debug=env.bool("DEBUG", default=False)
    )