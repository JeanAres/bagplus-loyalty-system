"""
Configuração de Rate Limiting
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def get_user_identifier(request: Request) -> str:
    """
    Identifica o usuário para rate limiting.
    
    Prioridade:
    1. Se autenticado: usa user.id
    2. Se não autenticado: usa IP
    """
    # Tentar pegar usuário autenticado do estado da request
    user = getattr(request.state, "user", None)
    
    if user:
        # Usuário autenticado: limitar por user_id
        return f"user:{user.id}"
    else:
        # Não autenticado: limitar por IP
        return f"ip:{get_remote_address(request)}"


# Inicializar limiter
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=["1000/hour"],  # Limite padrão global
    storage_uri="memory://",  # Armazenar em memória (simples)
)