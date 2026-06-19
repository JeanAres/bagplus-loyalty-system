"""
Endpoints administrativos - Gerenciamento de lotes
"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.audit import registrar_log
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.middleware.auth import require_role
from datetime import datetime
from app.db import models
import os
import hashlib
import re

router = APIRouter(
    prefix="/api/admin/lotes",
    tags=["Admin - Lotes"]
)


def _parse_lote_codigo(lote_codigo: str):
    """
    Extrai inicio e fim do código do lote.
    Formato esperado: lote_00001-00010
    Retorna: (inicio: int, fim: int)
    """
    match = re.fullmatch(r"lote_(\d{5})-(\d{5})", lote_codigo.strip())
    if not match:
        raise ValueError(
            f"Código de lote inválido: '{lote_codigo}'. Formato esperado: lote_00001-00010"
        )
    return int(match.group(1)), int(match.group(2))


@router.post(
    "/importar",
    summary="Importar lote de sacolas"
)
def importar_lote_csv(
    lote_codigo: str,
    data_fabricacao: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Importa um lote de sacolas usando o código retornado na geração.

    **Parâmetros:**
    - lote_codigo: Código do lote gerado (ex: lote_00001-00010)
    - data_fabricacao: Data de fabricação do lote (formato: YYYY-MM-DD)

    **Observação:** Use exatamente o código retornado pelo endpoint /gerar
    """

    # Validar data
    try:
        datetime.strptime(data_fabricacao, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Data inválida. Use formato YYYY-MM-DD (ex: 2026-03-31)"
        )

    # Extrair inicio e fim do código do lote
    try:
        inicio, fim = _parse_lote_codigo(lote_codigo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if inicio > fim:
        raise HTTPException(status_code=400, detail="Código de lote inválido: início maior que fim")

    quantidade = fim - inicio + 1

    if quantidade > 10000:
        raise HTTPException(
            status_code=400,
            detail="Limite máximo de 10.000 sacolas por lote"
        )

    # Verificar duplicatas
    primeiro_id = f"BAG-{inicio:05d}"
    ultimo_id = f"BAG-{fim:05d}"

    duplicata = db.query(models.Sacola).filter(
        models.Sacola.id.between(primeiro_id, ultimo_id)
    ).first()

    if duplicata:
        raise HTTPException(
            status_code=400,
            detail=f"Lote já foi importado. Sacola {duplicata.id} já existe no banco."
        )

    # Criar lote
    lote = models.Lote(
        data_fabricacao=data_fabricacao,
        quantidade=quantidade,
        inicio=inicio,
        fim=fim
    )
    db.add(lote)
    db.commit()
    db.refresh(lote)

    # Criar sacolas
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="SECRET_KEY não configurada no servidor"
        )

    sacolas_criadas = []

    for numero in range(inicio, fim + 1):
        sacola_id = f"BAG-{numero:05d}"

        texto = f"{sacola_id}{data_fabricacao}{SECRET_KEY}"
        hash_completo = hashlib.sha256(texto.encode()).hexdigest()
        checksum = hash_completo[:6]

        sacola = models.Sacola(
            id=sacola_id,
            qrcode=f"{sacola_id}:{data_fabricacao}:{checksum}",
            data_criacao=data_fabricacao,
            checksum=checksum,
            status=models.StatusSacola.estoque,
            lote_id=lote.id
        )
        db.add(sacola)
        sacolas_criadas.append(sacola_id)

    db.commit()

    registrar_log(
        db=db,
        usuario=current_user,
        acao="importar_lote",
        entidade_tipo="Lote",
        entidade_id=str(lote.id),
        detalhes={
            "lote_codigo": lote_codigo,
            "data_fabricacao": data_fabricacao,
            "quantidade": quantidade,
            "range": f"{primeiro_id} até {ultimo_id}"
        }
    )

    return {
        "sucesso": True,
        "mensagem": "Lote importado com sucesso",
        "lote": {
            "id": lote.id,
            "lote_codigo": lote_codigo,
            "data_fabricacao": lote.data_fabricacao,
            "quantidade": quantidade,
            "range": f"{primeiro_id} até {ultimo_id}"
        },
        "sacolas_criadas": len(sacolas_criadas)
    }


@router.get(
    "/",
    summary="Listar todos os lotes",
)
def listar_lotes(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Lista todos os lotes de sacolas importados no sistema.

    **Informações retornadas para cada lote:**
    - ID do lote
    - Código do lote
    - Data de fabricação e importação
    - Quantidade e range de IDs
    - Distribuição por status
    """

    lotes = db.query(models.Lote).order_by(models.Lote.data_importacao.desc()).all()

    lotes_data = []
    for lote in lotes:
        sacolas_estoque = db.query(models.Sacola).filter(
            models.Sacola.lote_id == lote.id,
            models.Sacola.status == models.StatusSacola.estoque
        ).count()

        sacolas_ativas = db.query(models.Sacola).filter(
            models.Sacola.lote_id == lote.id,
            models.Sacola.status == models.StatusSacola.ativo
        ).count()

        sacolas_devolvidas = db.query(models.Sacola).filter(
            models.Sacola.lote_id == lote.id,
            models.Sacola.status == models.StatusSacola.devolvido
        ).count()

        lotes_data.append({
            "id": lote.id,
            "lote_codigo": f"lote_{lote.inicio:05d}-{lote.fim:05d}",
            "data_fabricacao": lote.data_fabricacao,
            "data_importacao": lote.data_importacao,
            "quantidade": lote.quantidade,
            "range": f"BAG-{lote.inicio:05d} até BAG-{lote.fim:05d}",
            "distribuicao": {
                "estoque": sacolas_estoque,
                "ativas": sacolas_ativas,
                "devolvidas": sacolas_devolvidas
            }
        })

    return {
        "total_lotes": len(lotes_data),
        "lotes": lotes_data
    }


@router.get(
    "/{lote_id}/estatisticas",
    summary="Estatísticas de performance do lote",
)
def estatisticas_lote(
    lote_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Retorna análise completa de performance de um lote específico.

    **Parâmetro:**
    - lote_id: ID do lote (número inteiro)
    """

    lote = db.query(models.Lote).filter(models.Lote.id == lote_id).first()
    if not lote:
        raise HTTPException(status_code=404, detail=f"Lote {lote_id} não encontrado")

    sacolas = db.query(models.Sacola).filter(models.Sacola.lote_id == lote_id).all()

    if not sacolas:
        return {
            "lote": {
                "id": lote_id,
                "lote_codigo": f"lote_{lote.inicio:05d}-{lote.fim:05d}",
                "data_fabricacao": lote.data_fabricacao,
                "data_importacao": lote.data_importacao,
                "quantidade_total": 0
            },
            "distribuicao": {"estoque": 0, "ativas": 0, "devolvidas": 0, "taxa_ativacao": 0, "taxa_devolucao": 0},
            "tempo_uso": {"medio_dias": 0, "baseado_em": 0},
            "performance_financeira": {"valor_total_movimentado": 0, "valor_medio_por_sacola": 0, "total_usos": 0},
            "top_sacolas": []
        }

    total_sacolas = len(sacolas)
    estoque = len([s for s in sacolas if s.status == models.StatusSacola.estoque])
    ativas = len([s for s in sacolas if s.status == models.StatusSacola.ativo])
    devolvidas = len([s for s in sacolas if s.status == models.StatusSacola.devolvido])
    distribuidas = ativas + devolvidas
    taxa_ativacao = (distribuidas / total_sacolas * 100) if total_sacolas > 0 else 0
    taxa_devolucao = (devolvidas / distribuidas * 100) if distribuidas > 0 else 0

    sacolas_dev = [s for s in sacolas if s.status == models.StatusSacola.devolvido
                   and s.data_vinculacao and s.data_devolucao]

    tempo_medio_dias = 0
    if sacolas_dev:
        tempos = [(s.data_devolucao - s.data_vinculacao).days for s in sacolas_dev]
        tempo_medio_dias = sum(tempos) / len(tempos)

    valor_total = 0
    total_usos = 0
    for sacola in sacolas:
        registros = db.query(models.RegistroUso).filter(
            models.RegistroUso.sacola_id == sacola.id
        ).all()
        valor_total += sum(r.valor_compra for r in registros)
        total_usos += len(registros)

    valor_medio_por_sacola = valor_total / distribuidas if distribuidas > 0 else 0

    top_sacolas = []
    for sacola in sorted(sacolas, key=lambda s: s.utilizacoes, reverse=True)[:5]:
        if sacola.utilizacoes > 0:
            cliente = None
            if sacola.cliente_cpf:
                cliente = db.query(models.Cliente).filter(
                    models.Cliente.cpf == sacola.cliente_cpf
                ).first()
            top_sacolas.append({
                "sacola_id": sacola.id,
                "utilizacoes": sacola.utilizacoes,
                "status": sacola.status.value,
                "cliente": {
                    "cpf": sacola.cliente_cpf,
                    "nome": cliente.nome if cliente else "Desconhecido"
                } if sacola.cliente_cpf else None
            })

    return {
        "lote": {
            "id": lote_id,
            "lote_codigo": f"lote_{lote.inicio:05d}-{lote.fim:05d}",
            "data_fabricacao": lote.data_fabricacao,
            "data_importacao": lote.data_importacao,
            "quantidade_total": total_sacolas,
            "range_ids": f"BAG-{lote.inicio:05d} até BAG-{lote.fim:05d}"
        },
        "distribuicao": {
            "estoque": estoque,
            "ativas": ativas,
            "devolvidas": devolvidas,
            "taxa_ativacao": round(taxa_ativacao, 2),
            "taxa_devolucao": round(taxa_devolucao, 2)
        },
        "tempo_uso": {
            "medio_dias": round(tempo_medio_dias, 1),
            "baseado_em": len(sacolas_dev)
        },
        "performance_financeira": {
            "valor_total_movimentado": round(valor_total, 2),
            "valor_medio_por_sacola": round(valor_medio_por_sacola, 2),
            "total_usos": total_usos
        },
        "top_sacolas": top_sacolas
    }