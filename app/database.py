from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import load_config

# Настройки подключения к БД
config = load_config()
SQLALCHEMY_DATABASE_URL = config.db.database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)