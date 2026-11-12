from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL
from sqlalchemy.orm import DeclarativeBase

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

class Base(DeclarativeBase):
    """Base declarativa compartida por todos los modelos."""
    
Session = sessionmaker(bind=engine)
