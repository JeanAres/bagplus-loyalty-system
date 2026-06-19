"""
Endpoints administrativos - Gestão de Unidades (filiais)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.core.audit import registrar_log
from app.middleware.auth import require_role

router = APIRouter(
    prefix="/api/admin/unidades",
    tags=["Admin - Unidades"]
)


@router.post(
    "/",
    summary="Criar nova unidade",
)
def criar_unidade(
    entidade_id: int,
    nome: str,
    endereco: str = None,
    cidade: str = None,
    estado: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Cria uma nova unidade (filial) vinculada a uma entidade.

    **Permissão:** Admin

    **Parâmetros:**
    - entidade_id: ID da entidade pai
    - nome: Nome da unidade (ex: Iguatemi, Cavalhada)
    - endereco: Endereço físico (opcional)
    - cidade: Cidade (opcional)
    - estado: Estado (opcional)
    """

    # Verificar se entidade existe e está ativa
    entidade = db.query(models.Entidade).filter(
        models.Entidade.id == entidade_id,
        models.Entidade.ativo == True
    ).first()

    if not entidade:
        raise HTTPException(status_code=404, detail="Entidade não encontrada ou inativa")

    if len(nome.strip()) < 2:
        raise HTTPException(status_code=400, detail="Nome deve ter pelo menos 2 caracteres")

    unidade = models.Unidade(
        entidade_id=entidade_id,
        nome=nome.strip(),
        endereco=endereco,
        cidade=cidade,
        estado=estado,
        ativo=True
    )

    db.add(unidade)
    db.commit()
    db.refresh(unidade)

    registrar_log(
        db=db,
        usuario=current_user,
        acao="criar_unidade",
        entidade_tipo="Unidade",
        entidade_id=str(unidade.id),
        detalhes={
            "nome": nome,
            "entidade_id": entidade_id,
            "entidade_nome": entidade.nome_comercial
        }
    )

    return {
        "sucesso": True,
        "mensagem": f"Unidade '{nome}' criada com sucesso",
        "unidade": {
            "id": unidade.id,
            "nome": unidade.nome,
            "entidade_id": unidade.entidade_id,
            "entidade_nome": entidade.nome_comercial,
            "endereco": unidade.endereco,
            "cidade": unidade.cidade,
            "estado": unidade.estado,
            "ativo": unidade.ativo,
            "data_criacao": unidade.data_criacao
        }
    }

@router.get(
    "/",
    summary="Listar todas as unidades",
)
def listar_unidades(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Lista todas as unidades cadastradas no sistema.

    **Permissão:** Admin

    **Retorna:**
    - Total de unidades
    - Lista com ID, nome, entidade vinculada, endereço e status
    """

    unidades = db.query(models.Unidade).all()

    return {
        "total": len(unidades),
        "unidades": [
            {
                "id": u.id,
                "nome": u.nome,
                "entidade_id": u.entidade_id,
                "entidade_nome": u.entidade.nome_comercial,
                "endereco": u.endereco,
                "cidade": u.cidade,
                "estado": u.estado,
                "ativo": u.ativo,
                "data_criacao": u.data_criacao
            }
            for u in unidades
        ]
    }

@router.get(
    "/{unidade_id}",
    summary="Buscar unidade por ID",
)
def buscar_unidade(
    unidade_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Retorna informações de uma unidade específica.

    **Permissão:** Admin
    """

    unidade = db.query(models.Unidade).filter(models.Unidade.id == unidade_id).first()

    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")

    return {
        "id": unidade.id,
        "nome": unidade.nome,
        "entidade_id": unidade.entidade_id,
        "entidade_nome": unidade.entidade.nome_comercial,
        "endereco": unidade.endereco,
        "cidade": unidade.cidade,
        "estado": unidade.estado,
        "ativo": unidade.ativo,
        "data_criacao": unidade.data_criacao
    }


@router.put(
    "/{unidade_id}",
    summary="Editar unidade",
)
def editar_unidade(
    unidade_id: int,
    nome: str = None,
    endereco: str = None,
    cidade: str = None,
    estado: str = None,
    ativo: bool = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Atualiza informações de uma unidade.

    **Permissão:** Admin
    """

    unidade = db.query(models.Unidade).filter(models.Unidade.id == unidade_id).first()

    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")

    if all(v is None for v in [nome, endereco, cidade, estado, ativo]):
        raise HTTPException(status_code=400, detail="Informe pelo menos um campo para atualizar")

    alteracoes = {}

    if nome is not None:
        alteracoes["nome_anterior"] = unidade.nome
        alteracoes["nome_novo"] = nome
        unidade.nome = nome.strip()

    if endereco is not None:
        unidade.endereco = endereco
        alteracoes["endereco"] = endereco

    if cidade is not None:
        unidade.cidade = cidade
        alteracoes["cidade"] = cidade

    if estado is not None:
        unidade.estado = estado
        alteracoes["estado"] = estado

    if ativo is not None:
        alteracoes["ativo_anterior"] = unidade.ativo
        alteracoes["ativo_novo"] = ativo
        unidade.ativo = ativo

    db.commit()
    db.refresh(unidade)

    registrar_log(
        db=db,
        usuario=current_user,
        acao="editar_unidade",
        entidade_tipo="Unidade",
        entidade_id=str(unidade.id),
        detalhes=alteracoes
    )

    return {
        "sucesso": True,
        "mensagem": f"Unidade '{unidade.nome}' atualizada com sucesso",
        "unidade": {
            "id": unidade.id,
            "nome": unidade.nome,
            "entidade_id": unidade.entidade_id,
            "endereco": unidade.endereco,
            "cidade": unidade.cidade,
            "estado": unidade.estado,
            "ativo": unidade.ativo
        }
    }


@router.delete(
    "/{unidade_id}",
    summary="Desativar unidade",
)
def desativar_unidade(
    unidade_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Desativa uma unidade (não deleta, apenas marca como inativa).

    **Permissão:** Admin
    """

    unidade = db.query(models.Unidade).filter(models.Unidade.id == unidade_id).first()

    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")

    unidade.ativo = False
    db.commit()

    registrar_log(
        db=db,
        usuario=current_user,
        acao="desativar_unidade",
        entidade_tipo="Unidade",
        entidade_id=str(unidade.id),
        detalhes={"nome": unidade.nome, "entidade_id": unidade.entidade_id}
    )

    return {
        "sucesso": True,
        "mensagem": f"Unidade '{unidade.nome}' desativada com sucesso"
    }