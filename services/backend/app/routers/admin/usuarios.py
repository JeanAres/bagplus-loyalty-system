"""
Endpoints administrativos - Gestão de usuários
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from datetime import datetime
from app.db import models
from app.core.security import hash_password
from app.core.audit import registrar_log
from app.middleware.auth import require_role

router = APIRouter(
    prefix="/api/admin/usuarios",
    tags=["Admin - Usuários"]
)


@router.post(
    "/",
    summary="Criar novo usuário",
)
def criar_usuario(
    username: str,
    password: str,
    nome: str,
    role: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Cria um novo usuário no sistema (apenas administradores).
    
    **Permissão:** Admin
    
    **Parâmetros:**
    - username: Nome de usuário (único, 3-50 caracteres)
    - password: Senha (mínimo 6 caracteres)
    - nome: Nome completo
    - role: Papel no sistema (admin/gerente/caixa)
    
    **Roles disponíveis:**
    - admin: Acesso total
    - gerente: Relatórios e visualizações
    - caixa: Operações de caixa
    
    **Quando usar:**
    - Cadastrar novo funcionário
    - Criar usuários para diferentes setores
    
    **Observação:** Senha será armazenada com hash bcrypt
    """
    
    # Validar username
    if len(username) < 3 or len(username) > 50:
        raise HTTPException(
            status_code=400,
            detail="Username deve ter entre 3 e 50 caracteres"
        )
    
    # Validar senha
    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Senha deve ter no mínimo 6 caracteres"
        )
    
    # Validar role
    try:
        role_enum = models.UserRole(role)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Role inválida. Use: admin, gerente ou caixa"
        )
    
    # Verificar se username já existe
    usuario_existe = db.query(models.Usuario).filter(
        models.Usuario.username == username
    ).first()
    
    if usuario_existe:
        raise HTTPException(
            status_code=400,
            detail=f"Username '{username}' já está em uso"
        )
    
    # Criar usuário
    usuario = models.Usuario(
        username=username,
        password_hash=hash_password(password),
        nome=nome,
        role=role_enum,
        ativo=True
    )
    
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    
    # Registrar log
    registrar_log(
        db=db,
        usuario=current_user,
        acao="criar_usuario",
        entidade_tipo="Usuario",
        entidade_id=str(usuario.id),
        detalhes={
            "username": username,
            "nome": nome,
            "role": role
        }
    )
    
    return {
        "sucesso": True,
        "mensagem": f"Usuário '{username}' criado com sucesso",
        "usuario": {
            "id": usuario.id,
            "username": usuario.username,
            "nome": usuario.nome,
            "role": usuario.role,
            "ativo": usuario.ativo,
            "data_criacao": usuario.data_criacao
        }
    }


@router.get(
    "/",
    summary="Listar todos os usuários",
)
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Lista todos os usuários cadastrados no sistema.
    
    **Permissão:** Admin ou Gerente
    
    **Retorna:**
    - Total de usuários
    - Lista com ID, username, nome, role, status
    - Data de criação e último login
    
    **Quando usar:**
    - Visualizar equipe cadastrada
    - Verificar usuários ativos/inativos
    """
    
    usuarios = db.query(models.Usuario).all()
    
    usuarios_data = []
    for usuario in usuarios:
        usuarios_data.append({
            "id": usuario.id,
            "username": usuario.username,
            "nome": usuario.nome,
            "role": usuario.role,
            "ativo": usuario.ativo,
            "data_criacao": usuario.data_criacao,
            "ultimo_login": usuario.ultimo_login
        })
    
    return {
        "total": len(usuarios_data),
        "usuarios": usuarios_data
    }


@router.get(
    "/{usuario_id}",
    summary="Buscar usuário por ID",
)
def buscar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Retorna informações de um usuário específico.
    
    **Permissão:** Admin ou Gerente
    
    **Parâmetro:**
    - usuario_id: ID do usuário
    
    **Retorna:**
    - Informações completas do usuário
    - Histórico de último login
    """
    
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {
        "id": usuario.id,
        "username": usuario.username,
        "nome": usuario.nome,
        "role": usuario.role,
        "ativo": usuario.ativo,
        "data_criacao": usuario.data_criacao,
        "ultimo_login": usuario.ultimo_login
    }


@router.put(
    "/{usuario_id}",
    summary="Editar usuário",
)
def editar_usuario(
    usuario_id: int,
    nome: str = None,
    role: str = None,
    ativo: bool = None,
    password: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Atualiza informações de um usuário.
    
    **Permissão:** Admin
    
    **Parâmetros opcionais:**
    - nome: Alterar nome completo
    - role: Alterar permissão (admin/gerente/caixa)
    - ativo: Ativar/desativar usuário
    - password: Alterar senha (mínimo 6 caracteres)
    
    **Quando usar:**
    - Promover usuário (mudar role)
    - Desativar usuário que saiu da empresa
    - Atualizar dados cadastrais
    - Resetar senha
    
    **Observação:** Pelo menos um campo deve ser informado
    """
    
    # Buscar usuário
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Verificar se pelo menos um campo foi informado
    if nome is None and role is None and ativo is None and password is None:
        raise HTTPException(
            status_code=400,
            detail="Informe pelo menos um campo para atualizar"
        )
    
    alteracoes = {}
    
    # Atualizar nome
    if nome is not None:
        alteracoes["nome_anterior"] = usuario.nome
        alteracoes["nome_novo"] = nome
        usuario.nome = nome
    
    # Atualizar role
    if role is not None:
        try:
            role_enum = models.UserRole(role)
            alteracoes["role_anterior"] = usuario.role.value
            alteracoes["role_novo"] = role
            usuario.role = role_enum
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Role inválida. Use: admin, gerente ou caixa"
            )
    
    # Atualizar status
    if ativo is not None:
        alteracoes["ativo_anterior"] = usuario.ativo
        alteracoes["ativo_novo"] = ativo
        usuario.ativo = ativo
    
    # Atualizar senha
    if password is not None:
        if len(password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Senha deve ter no mínimo 6 caracteres"
            )
        alteracoes["senha_alterada"] = True
        usuario.password_hash = hash_password(password)
    
    db.commit()
    db.refresh(usuario)
    
    # Registrar log
    registrar_log(
        db=db,
        usuario=current_user,
        acao="editar_usuario",
        entidade_tipo="Usuario",
        entidade_id=str(usuario.id),
        detalhes={
            "username": usuario.username,
            "alteracoes": alteracoes
        }
    )
    
    return {
        "sucesso": True,
        "mensagem": f"Usuário '{usuario.username}' atualizado com sucesso",
        "usuario": {
            "id": usuario.id,
            "username": usuario.username,
            "nome": usuario.nome,
            "role": usuario.role,
            "ativo": usuario.ativo
        }
    }


@router.delete(
    "/{usuario_id}",
    summary="Desativar usuário",
)
def desativar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Desativa um usuário do sistema (não deleta, apenas marca como inativo).
    
    **Permissão:** Admin
    
    **ATENÇÃO:** Não deleta o usuário, apenas o marca como inativo.
    
    **Parâmetro:**
    - usuario_id: ID do usuário
    
    **Quando usar:**
    - Funcionário saiu da empresa
    - Usuário não deve mais ter acesso
    
    **Observação:** 
    - Histórico e logs são preservados
    - Usuário pode ser reativado depois
    """
    
    # Buscar usuário
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Não pode desativar a si mesmo
    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Você não pode desativar seu próprio usuário"
        )
    
    # Desativar
    usuario.ativo = False
    db.commit()
    
    # Registrar log
    registrar_log(
        db=db,
        usuario=current_user,
        acao="desativar_usuario",
        entidade_tipo="Usuario",
        entidade_id=str(usuario.id),
        detalhes={
            "username": usuario.username,
            "nome": usuario.nome
        }
    )
    
    return {
        "sucesso": True,
        "mensagem": f"Usuário '{usuario.username}' desativado com sucesso"
    }