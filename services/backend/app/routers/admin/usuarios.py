"""
Endpoints administrativos - Gestão de usuários
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
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
    role: models.UserRole,
    entidade_id: int = None,
    unidade_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Cria um novo usuário no sistema.

    **Permissão:** Admin ou Gerente

    **Parâmetros:**
    - username: Nome de usuário (único, 3-50 caracteres)
    - password: Senha (mínimo 6 caracteres)
    - nome: Nome completo
    - role: Papel no sistema (admin/gerente/caixa)
    - entidade_id: ID da entidade (obrigatório para gerente e caixa quando criado por admin)
    - unidade_id: ID da unidade (obrigatório para gerente e caixa quando criado por admin)

    **Regras por role do criador:**
    - Admin: pode criar qualquer role, informando entidade_id e unidade_id para gerente/caixa
    - Gerente: só pode criar caixas, automaticamente vinculados à sua própria unidade

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

    # Gerente só pode criar caixas para sua própria unidade
    if current_user.role == models.UserRole.gerente:
        if role != models.UserRole.caixa:
            raise HTTPException(
                status_code=403,
                detail="Gerente só pode criar usuários com role 'caixa'"
            )
        # Força entidade e unidade do próprio gerente
        entidade_id = current_user.entidade_id
        unidade_id = current_user.unidade_id

    # Admin: gerente e caixa precisam de entidade e unidade
    if current_user.role == models.UserRole.admin:
        if role in [models.UserRole.gerente, models.UserRole.caixa]:
            if entidade_id is None or unidade_id is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Role '{role.value}' requer entidade_id e unidade_id"
                )

            # Validar se entidade existe e está ativa
            entidade = db.query(models.Entidade).filter(
                models.Entidade.id == entidade_id,
                models.Entidade.ativo == True
            ).first()

            if not entidade:
                raise HTTPException(
                    status_code=404,
                    detail=f"Entidade {entidade_id} não encontrada ou inativa"
                )

            # Validar se unidade existe, está ativa e pertence à entidade
            unidade = db.query(models.Unidade).filter(
                models.Unidade.id == unidade_id,
                models.Unidade.entidade_id == entidade_id,
                models.Unidade.ativo == True
            ).first()

            if not unidade:
                raise HTTPException(
                    status_code=404,
                    detail=f"Unidade {unidade_id} não encontrada, inativa ou não pertence à entidade {entidade_id}"
                )

        # Admin não deve ter entidade/unidade
        if role == models.UserRole.admin:
            entidade_id = None
            unidade_id = None

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
        role=role,
        entidade_id=entidade_id,
        unidade_id=unidade_id,
        ativo=True
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    registrar_log(
        db=db,
        usuario=current_user,
        acao="criar_usuario",
        entidade_tipo="Usuario",
        entidade_id=str(usuario.id),
        detalhes={
            "username": username,
            "nome": nome,
            "role": role.value,
            "entidade_id": entidade_id,
            "unidade_id": unidade_id
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
            "entidade_id": usuario.entidade_id,
            "unidade_id": usuario.unidade_id,
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
    Lista usuários do sistema.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: lista todos os usuários
    - Gerente: lista apenas usuários da sua unidade

    **Retorna:**
    - Total de usuários
    - Lista com ID, username, nome, role, entidade, unidade e status
    """

    query = db.query(models.Usuario)

    # Gerente vê apenas usuários da sua unidade
    if current_user.role == models.UserRole.gerente:
        query = query.filter(
            models.Usuario.unidade_id == current_user.unidade_id
        )

    usuarios = query.all()

    usuarios_data = []
    for usuario in usuarios:
        usuarios_data.append({
            "id": usuario.id,
            "username": usuario.username,
            "nome": usuario.nome,
            "role": usuario.role,
            "entidade_id": usuario.entidade_id,
            "unidade_id": usuario.unidade_id,
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

    **Comportamento por role:**
    - Admin: pode buscar qualquer usuário
    - Gerente: pode buscar apenas usuários da sua unidade

    **Parâmetro:**
    - usuario_id: ID do usuário
    """

    query = db.query(models.Usuario).filter(models.Usuario.id == usuario_id)

    # Gerente só pode ver usuários da sua unidade
    if current_user.role == models.UserRole.gerente:
        query = query.filter(
            models.Usuario.unidade_id == current_user.unidade_id
        )

    usuario = query.first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "id": usuario.id,
        "username": usuario.username,
        "nome": usuario.nome,
        "role": usuario.role,
        "entidade_id": usuario.entidade_id,
        "unidade_id": usuario.unidade_id,
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
    role: models.UserRole = None,
    ativo: bool = None,
    password: str = None,
    entidade_id: int = None,
    unidade_id: int = None,
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
    - entidade_id: Vincular a outra entidade
    - unidade_id: Vincular a outra unidade

    **Observação:** Pelo menos um campo deve ser informado
    """

    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if all(v is None for v in [nome, role, ativo, password, entidade_id, unidade_id]):
        raise HTTPException(
            status_code=400,
            detail="Informe pelo menos um campo para atualizar"
        )

    alteracoes = {}

    if nome is not None:
        alteracoes["nome_anterior"] = usuario.nome
        alteracoes["nome_novo"] = nome
        usuario.nome = nome

    if role is not None:
        alteracoes["role_anterior"] = usuario.role.value
        alteracoes["role_novo"] = role.value
        usuario.role = role

        # Se virou admin, limpa entidade e unidade
        if role == models.UserRole.admin:
            usuario.entidade_id = None
            usuario.unidade_id = None
            alteracoes["entidade_unidade_removidas"] = True

    if ativo is not None:
        alteracoes["ativo_anterior"] = usuario.ativo
        alteracoes["ativo_novo"] = ativo
        usuario.ativo = ativo

    if password is not None:
        if len(password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Senha deve ter no mínimo 6 caracteres"
            )
        alteracoes["senha_alterada"] = True
        usuario.password_hash = hash_password(password)

    if entidade_id is not None:
        entidade = db.query(models.Entidade).filter(
            models.Entidade.id == entidade_id,
            models.Entidade.ativo == True
        ).first()
        if not entidade:
            raise HTTPException(
                status_code=404,
                detail=f"Entidade {entidade_id} não encontrada ou inativa"
            )
        alteracoes["entidade_id_anterior"] = usuario.entidade_id
        alteracoes["entidade_id_nova"] = entidade_id
        usuario.entidade_id = entidade_id

    if unidade_id is not None:
        entidade_ref = entidade_id or usuario.entidade_id
        unidade = db.query(models.Unidade).filter(
            models.Unidade.id == unidade_id,
            models.Unidade.entidade_id == entidade_ref,
            models.Unidade.ativo == True
        ).first()
        if not unidade:
            raise HTTPException(
                status_code=404,
                detail=f"Unidade {unidade_id} não encontrada, inativa ou não pertence à entidade informada"
            )
        alteracoes["unidade_id_anterior"] = usuario.unidade_id
        alteracoes["unidade_id_nova"] = unidade_id
        usuario.unidade_id = unidade_id

    db.commit()
    db.refresh(usuario)

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
            "entidade_id": usuario.entidade_id,
            "unidade_id": usuario.unidade_id,
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

    **Observação:**
    - Histórico e logs são preservados
    - Usuário pode ser reativado depois
    """

    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Você não pode desativar seu próprio usuário"
        )

    usuario.ativo = False
    db.commit()

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