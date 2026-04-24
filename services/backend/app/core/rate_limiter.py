"""
Configuração de rate limiting usando slowapi

Protege endpoints contra abuso e ataques de força bruta.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def get_user_identifier(request: Request) -> str:
    """
    Identifica o usuário para rate limiting.
    
    Usa user_id se autenticado, senão usa IP.
    Isso permite limites diferentes para usuários conhecidos vs anônimos.
    
    Args:
        request: Request object do FastAPI
    
    Returns:
        String identificadora (user_id ou IP)
    """
    # Se usuário autenticado, usar seu ID
    if hasattr(request.state, 'user') and request.state.user:
        return f"user_{request.state.user.id}"
    
    # Caso contrário, usar IP
    return get_remote_address(request)


# Criar instância do limiter
limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri="memory://"  # Armazenamento em memória
)