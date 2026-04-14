"""
Utilitários de segurança - Hash de senhas e JWT
"""
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24  # Token válido por 24h em dev

# Contexto de hash (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Gera hash bcrypt da senha"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se senha bate com o hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None,
    expires_hours: Optional[int] = None
) -> str:
    """
    Cria um JWT token
    
    Args:
        data: Dados a codificar (ex: {"sub": "username", "role": "admin"})
        expires_delta: Tempo de expiração customizado (timedelta)
        expires_hours: Tempo de expiração em horas (int) - mais simples
    
    Returns:
        Token JWT assinado
    """
    to_encode = data.copy()
    
    # Prioridade: expires_hours > expires_delta > padrão (24h)
    if expires_hours:
        expire = datetime.utcnow() + timedelta(hours=expires_hours)
    elif expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decodifica e valida um JWT token
    
    Args:
        token: Token JWT a decodificar
    
    Returns:
        Dados do token (payload)
    
    Raises:
        JWTError: Se token inválido ou expirado
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload