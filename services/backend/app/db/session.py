"""
Database Session Configuration
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base
import os
from dotenv import load_dotenv

load_dotenv()

# URL do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/bagplus.db")

# Criar engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Necessário para SQLite
)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Cria todas as tabelas no banco de dados"""
    Base.metadata.create_all(bind=engine)
    print("✅ Banco de dados inicializado!")


def get_db():
    """Retorna uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()