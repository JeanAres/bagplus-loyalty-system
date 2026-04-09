"""
Middleware de autenticação - Validação de JWT e permissões
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Optional
from app.db import models
from app.db.session import get_db
from app.core.security import decode_token

# Security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.Usuario:
    """
    Valida token JWT e retorna usuário atual
    
    Raises:
        HTTPException 401: Token inválido ou expirado
        HTTPException 404: Usuário não encontrado
        HTTPException 403: Usuário inativo
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decodificar token
        token = credentials.credentials
        payload = decode_token(token)
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Buscar usuário
    user = db.query(models.Usuario).filter(models.Usuario.username == username).first()
    
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if not user.ativo:
        raise HTTPException(status_code=403, detail="Usuário inativo")
    
    return user


def require_role(allowed_roles: list[str]):
    """
    Decorator para exigir role específica
    
    Usage:
        @router.get("/admin/dashboard")
        def dashboard(user: models.Usuario = Depends(require_role(["admin", "gerente"]))):
            ...
    """
    def role_checker(current_user: models.Usuario = Depends(get_current_user)) -> models.Usuario:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer role: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker