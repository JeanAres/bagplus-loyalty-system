"""
Endpoints de autenticação - Login e gestão de tokens
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime
import models
from utils.security import verify_password, create_access_token
from middleware.auth import get_current_user

router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticação"]
)


@router.post(
    "/login",
    summary="Login no sistema",
    description="""
    Autentica usuário e retorna token JWT.
    
    **Credenciais:**
    - username: Nome de usuário
    - password: Senha
    
    **Retorna:**
    - access_token: Token JWT para usar nas requisições
    - token_type: Tipo do token (bearer)
    - expires_in: Tempo de expiração em segundos
    - user: Informações do usuário logado
    
    **Como usar o token:**
    1. Copie o access_token retornado
    2. No Swagger, clique em "Authorize" (cadeado)
    3. Cole o token no campo
    4. Clique em "Authorize"
    5. Agora pode usar endpoints protegidos
    
    **Observação:** Token válido por 24 horas em desenvolvimento
    """
)
def login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Autentica usuário e retorna token JWT"""
    
    # Buscar usuário
    user = db.query(models.Usuario).filter(
        models.Usuario.username == username
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar senha
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar se está ativo
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo. Contate o administrador."
        )
    
    # Atualizar último login
    user.ultimo_login = datetime.now()
    db.commit()
    
    # Criar token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 horas
        "user": {
            "id": user.id,
            "username": user.username,
            "nome": user.nome,
            "role": user.role
        }
    }

@router.get(
    "/me",
    summary="Informações do usuário logado",
    description="""
    Retorna informações do usuário autenticado pelo token.
    
    **Requer:** Token JWT válido
    
    **Retorna:**
    - ID do usuário
    - Username
    - Nome completo
    - Role (permissão)
    - Status ativo
    - Data do último login
    
    **Quando usar:**
    - Verificar se token ainda é válido
    - Obter informações do usuário logado
    - Exibir nome do usuário na interface
    """
)
def get_me(current_user: models.Usuario = Depends(get_current_user)):
    """Retorna informações do usuário logado"""
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "nome": current_user.nome,
        "role": current_user.role.value,
        "ativo": current_user.ativo,
        "data_criacao": current_user.data_criacao,
        "ultimo_login": current_user.ultimo_login
    }


@router.get(
    "/dev-token",
    summary="Token de desenvolvimento (apenas DEV)",
    description="""
    Gera token de desenvolvimento sem necessidade de login.
    
    **ATENÇÃO:** Este endpoint só funciona em ambiente de desenvolvimento.
    
    **Como usar:**
    1. Chamar este endpoint
    2. Copiar o access_token
    3. No Swagger, clicar em "Authorize"
    4. Colar o token
    5. Usar endpoints protegidos
    
    **Observação:** 
    - Token com permissão de ADMIN
    - Válido por 24 horas
    - Desabilitado em produção
    """
)
def get_dev_token(db: Session = Depends(get_db)):
    """Gera token de desenvolvimento (apenas em DEV)"""
    
    import os
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Endpoint disponível apenas em ambiente de desenvolvimento"
        )
    
    # Criar token com permissão admin
    token = create_access_token(
        data={
            "sub": "dev_admin",
            "role": "admin"
        }
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,
        "message": "TOKEN DE DESENVOLVIMENTO - Não use em produção!",
        "user": {
            "username": "dev_admin",
            "nome": "Administrador de Desenvolvimento",
            "role": "admin"
        }
    }