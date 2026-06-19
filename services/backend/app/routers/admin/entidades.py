"""
Endpoints administrativos - Gestão de Entidades
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.core.audit import registrar_log
from app.middleware.auth import require_role

router = APIRouter(
    prefix="/api/admin/entidades",
    tags=["Admin - Entidades"]
)


@router.post(
    "/",
    summary="Criar nova entidade",
)
def criar_entidade(
    nome_comercial: str,
    cnpj: str,
    meta_desconto_percentual: float,
    meta_desconto_quantidade_usos: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Cria uma nova entidade (estabelecimento) no sistema.

    **Permissão:** Admin

    **Parâmetros:**
    - nome_comercial: Nome do estabelecimento (ex: Zaffari, Mercadinho João)
    - cnpj: CNPJ único da entidade (14 dígitos, sem formatação)
    - meta_desconto_percentual: Percentual de desconto concedido ao cliente quando atingir a meta de usos (ex: 10.0 = 10%). Deve ser entre 0 e 100.
    - meta_desconto_quantidade_usos: Quantidade de usos necessários para o cliente ganhar o desconto (ex: 10 = a cada 10 usos o cliente ganha o desconto). Deve ser maior que zero.

    **Exemplo de configuração:**
    - meta_desconto_percentual: 10.0
    - meta_desconto_quantidade_usos: 10
    - Resultado: cliente ganha 10% de desconto a cada 10 usos no estabelecimento

    **Observação:** Cada entidade tem sua própria meta independente.
    """

    # Validar nome
    if len(nome_comercial.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Nome comercial deve ter pelo menos 2 caracteres"
        )

    # Validar CNPJ único
    entidade_existe = db.query(models.Entidade).filter(
        models.Entidade.cnpj == cnpj
    ).first()

    if entidade_existe:
        raise HTTPException(
            status_code=400,
            detail=f"CNPJ '{cnpj}' já cadastrado"
        )

    # Validar meta
    if meta_desconto_percentual <= 0 or meta_desconto_percentual > 100:
        raise HTTPException(
            status_code=400,
            detail="Percentual de desconto deve ser entre 0 e 100"
        )

    if meta_desconto_quantidade_usos <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantidade de usos para meta deve ser maior que zero"
        )

    entidade = models.Entidade(
        nome_comercial=nome_comercial.strip(),
        cnpj=cnpj,
        meta_desconto_percentual=meta_desconto_percentual,
        meta_desconto_quantidade_usos=meta_desconto_quantidade_usos,
        ativo=True
    )

    db.add(entidade)
    db.commit()
    db.refresh(entidade)

    registrar_log(
        db=db,
        usuario=current_user,
        acao="criar_entidade",
        entidade_tipo="Entidade",
        entidade_id=str(entidade.id),
        detalhes={
            "nome_comercial": nome_comercial,
            "cnpj": cnpj
        }
    )

    return {
        "sucesso": True,
        "mensagem": f"Entidade '{nome_comercial}' criada com sucesso",
        "entidade": {
            "id": entidade.id,
            "nome_comercial": entidade.nome_comercial,
            "cnpj": entidade.cnpj,
            "meta_desconto_percentual": entidade.meta_desconto_percentual,
            "meta_desconto_quantidade_usos": entidade.meta_desconto_quantidade_usos,
            "ativo": entidade.ativo,
            "data_criacao": entidade.data_criacao
        }
    }


@router.get(
    "/",
    summary="Listar todas as entidades",
)
def listar_entidades(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Lista todas as entidades cadastradas no sistema.

    **Permissão:** Admin
    """

    entidades = db.query(models.Entidade).all()

    return {
        "total": len(entidades),
        "entidades": [
            {
                "id": e.id,
                "nome_comercial": e.nome_comercial,
                "cnpj": e.cnpj,
                "meta_desconto_percentual": e.meta_desconto_percentual,
                "meta_desconto_quantidade_usos": e.meta_desconto_quantidade_usos,
                "ativo": e.ativo,
                "data_criacao": e.data_criacao
            }
            for e in entidades
        ]
    }


@router.get(
    "/{entidade_id}",
    summary="Buscar entidade por ID",
)
def buscar_entidade(
    entidade_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Retorna informações de uma entidade específica.

    **Permissão:** Admin
    """

    entidade = db.query(models.Entidade).filter(models.Entidade.id == entidade_id).first()

    if not entidade:
        raise HTTPException(status_code=404, detail="Entidade não encontrada")

    return {
        "id": entidade.id,
        "nome_comercial": entidade.nome_comercial,
        "cnpj": entidade.cnpj,
        "meta_desconto_percentual": entidade.meta_desconto_percentual,
        "meta_desconto_quantidade_usos": entidade.meta_desconto_quantidade_usos,
        "ativo": entidade.ativo,
        "data_criacao": entidade.data_criacao
    }


@router.get(
    "/{entidade_id}/unidades",
    summary="Listar unidades de uma entidade",
)
def listar_unidades_da_entidade(
    entidade_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Lista todas as unidades (filiais) de uma entidade específica.

    **Permissão:** Admin
    """

    entidade = db.query(models.Entidade).filter(models.Entidade.id == entidade_id).first()

    if not entidade:
        raise HTTPException(status_code=404, detail="Entidade não encontrada")

    unidades = db.query(models.Unidade).filter(
        models.Unidade.entidade_id == entidade_id
    ).all()

    return {
        "entidade": entidade.nome_comercial,
        "total": len(unidades),
        "unidades": [
            {
                "id": u.id,
                "nome": u.nome,
                "endereco": u.endereco,
                "cidade": u.cidade,
                "estado": u.estado,
                "ativo": u.ativo,
                "data_criacao": u.data_criacao
            }
            for u in unidades
        ]
    }


@router.put(
    "/{entidade_id}",
    summary="Editar entidade",
)
def editar_entidade(
    entidade_id: int,
    nome_comercial: str = None,
    meta_desconto_percentual: float = None,
    meta_desconto_quantidade_usos: int = None,
    ativo: bool = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Atualiza informações de uma entidade.

    **Permissão:** Admin

    **Parâmetros opcionais:**
    - nome_comercial: Novo nome
    - meta_desconto_percentual: Novo percentual de desconto
    - meta_desconto_quantidade_usos: Nova quantidade de usos para meta
    - ativo: Ativar/desativar entidade
    """

    entidade = db.query(models.Entidade).filter(models.Entidade.id == entidade_id).first()

    if not entidade:
        raise HTTPException(status_code=404, detail="Entidade não encontrada")

    if all(v is None for v in [nome_comercial, meta_desconto_percentual, meta_desconto_quantidade_usos, ativo]):
        raise HTTPException(
            status_code=400,
            detail="Informe pelo menos um campo para atualizar"
        )

    alteracoes = {}

    if nome_comercial is not None:
        alteracoes["nome_anterior"] = entidade.nome_comercial
        alteracoes["nome_novo"] = nome_comercial
        entidade.nome_comercial = nome_comercial.strip()

    if meta_desconto_percentual is not None:
        if meta_desconto_percentual <= 0 or meta_desconto_percentual > 100:
            raise HTTPException(status_code=400, detail="Percentual deve ser entre 0 e 100")
        alteracoes["meta_percentual_anterior"] = entidade.meta_desconto_percentual
        alteracoes["meta_percentual_nova"] = meta_desconto_percentual
        entidade.meta_desconto_percentual = meta_desconto_percentual

    if meta_desconto_quantidade_usos is not None:
        if meta_desconto_quantidade_usos <= 0:
            raise HTTPException(status_code=400, detail="Quantidade de usos deve ser maior que zero")
        alteracoes["meta_usos_anterior"] = entidade.meta_desconto_quantidade_usos
        alteracoes["meta_usos_nova"] = meta_desconto_quantidade_usos
        entidade.meta_desconto_quantidade_usos = meta_desconto_quantidade_usos

    if ativo is not None:
        alteracoes["ativo_anterior"] = entidade.ativo
        alteracoes["ativo_novo"] = ativo
        entidade.ativo = ativo

    db.commit()
    db.refresh(entidade)

    registrar_log(
        db=db,
        usuario=current_user,
        acao="editar_entidade",
        entidade_tipo="Entidade",
        entidade_id=str(entidade.id),
        detalhes=alteracoes
    )

    return {
        "sucesso": True,
        "mensagem": f"Entidade '{entidade.nome_comercial}' atualizada com sucesso",
        "entidade": {
            "id": entidade.id,
            "nome_comercial": entidade.nome_comercial,
            "cnpj": entidade.cnpj,
            "meta_desconto_percentual": entidade.meta_desconto_percentual,
            "meta_desconto_quantidade_usos": entidade.meta_desconto_quantidade_usos,
            "ativo": entidade.ativo
        }
    }


@router.delete(
    "/{entidade_id}",
    summary="Desativar entidade",
)
def desativar_entidade(
    entidade_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Desativa uma entidade (não deleta, apenas marca como inativa).

    **Permissão:** Admin

    **Observação:** Todas as unidades da entidade continuam no banco.
    """

    entidade = db.query(models.Entidade).filter(models.Entidade.id == entidade_id).first()

    if not entidade:
        raise HTTPException(status_code=404, detail="Entidade não encontrada")

    entidade.ativo = False
    db.commit()

    registrar_log(
        db=db,
        usuario=current_user,
        acao="desativar_entidade",
        entidade_tipo="Entidade",
        entidade_id=str(entidade.id),
        detalhes={"nome_comercial": entidade.nome_comercial}
    )

    return {
        "sucesso": True,
        "mensagem": f"Entidade '{entidade.nome_comercial}' desativada com sucesso"
    }