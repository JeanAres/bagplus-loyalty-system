"""
Endpoints de auditoria para o operador de caixa
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from datetime import datetime
from app.db import models
from app.middleware.auth import require_role
import json

router = APIRouter(
    prefix="/api/auditoria",
    tags=["Auditoria"]
)


@router.get(
    "/meu-turno",
    summary="Resumo das ações do caixa no dia atual",
)
def meu_turno(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["caixa"]))
):
    """
    Retorna um resumo das operações realizadas pelo caixa logado no dia de hoje.

    **Permissão:** Caixa

    **Informações retornadas:**
    - Contagem de ativações, registros de uso e devoluções realizadas hoje
    - Últimas 5 ações realizadas, com horário, tipo e detalhes (sacola/cliente/valor)

    **Observação:** Considera apenas ações do próprio usuário logado, a partir da
    meia-noite (00:00) do dia atual.
    """

    inicio_do_dia = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    acoes_consideradas = ["ativar_sacola", "registrar_uso", "devolver_sacola"]

    logs_hoje = db.query(models.LogAuditoria).filter(
        models.LogAuditoria.usuario_id == current_user.id,
        models.LogAuditoria.acao.in_(acoes_consideradas),
        models.LogAuditoria.timestamp >= inicio_do_dia
    ).order_by(models.LogAuditoria.timestamp.desc()).all()

    contagem = {
        "ativar_sacola": 0,
        "registrar_uso": 0,
        "devolver_sacola": 0,
    }

    ultimas_acoes = []

    for log in logs_hoje:
        if log.acao in contagem:
            contagem[log.acao] += 1

        if len(ultimas_acoes) < 5:
            detalhes = None
            if log.detalhes:
                try:
                    detalhes = json.loads(log.detalhes)
                except Exception:
                    detalhes = None

            ultimas_acoes.append({
                "acao": log.acao,
                "timestamp": log.timestamp,
                "sacola_id": detalhes.get("sacola_id") if detalhes else None,
                "cliente_nome": detalhes.get("cliente_nome") if detalhes else None,
                "valor_compra": detalhes.get("valor_compra") if detalhes else None,
                "desconto_concedido": detalhes.get("desconto_concedido") if detalhes else None,
            })

    return {
        "data": inicio_do_dia.date(),
        "usuario": {
            "id": current_user.id,
            "nome": current_user.nome,
            "username": current_user.username
        },
        "resumo": {
            "ativacoes": contagem["ativar_sacola"],
            "usos_registrados": contagem["registrar_uso"],
            "devolucoes": contagem["devolver_sacola"],
            "total_operacoes": sum(contagem.values())
        },
        "ultimas_acoes": ultimas_acoes
    }