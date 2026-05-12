"""
Endpoints administrativos - Logs de auditoria
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from datetime import datetime
from app.db import models
from app.middleware.auth import require_role
import json

router = APIRouter(
    prefix="/api/admin/auditoria",
    tags=["Admin - Auditoria"]
)


@router.get(
    "/logs",
    summary="Consultar logs de auditoria",
)
def consultar_logs(
    data_inicio: str = None,
    data_fim: str = None,
    usuario_id: int = None,
    usuario_username: str = None,
    acao: str = None,
    tabela: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Retorna logs de ações administrativas para auditoria.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: todos os logs do sistema
    - Gerente: apenas logs da sua unidade

    **Filtros disponíveis (opcionais):**
    - data_inicio: Data inicial (YYYY-MM-DD)
    - data_fim: Data final (YYYY-MM-DD)
    - usuario_id: Filtrar por ID do usuário
    - usuario_username: Filtrar por username (busca parcial)
    - acao: Tipo de ação (login, suspender_cliente, registrar_uso, etc)
    - tabela: Tabela afetada (Cliente, Sacola, Usuario, Entidade, Unidade)

    **Exemplos:**
    - **Todos os logs:** /api/admin/auditoria/logs
    - **Logs de suspensões:** /api/admin/auditoria/logs?acao=suspender_cliente
    - **Logs de um usuário:** /api/admin/auditoria/logs?usuario_id=1
    - **Logs de março:** /api/admin/auditoria/logs?data_inicio=2026-03-01&data_fim=2026-03-31

    **Observação:** Logs ordenados por data (mais recente primeiro), limite de 100 resultados
    """

    eh_gerente = current_user.role == models.UserRole.gerente

    query = db.query(models.LogAuditoria)

    # Gerente vê apenas logs da sua unidade
    if eh_gerente:
        query = query.filter(
            models.LogAuditoria.unidade_id == current_user.unidade_id
        )

    # Filtrar por período
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(models.LogAuditoria.timestamp >= dt_inicio)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data início inválida. Use formato: YYYY-MM-DD"
            )

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(models.LogAuditoria.timestamp <= dt_fim)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data fim inválida. Use formato: YYYY-MM-DD"
            )

    # Filtrar por usuario_id
    if usuario_id:
        query = query.filter(models.LogAuditoria.usuario_id == usuario_id)

    # Filtrar por username via relacionamento (busca parcial case-insensitive)
    if usuario_username:
        query = query.join(models.Usuario).filter(
            models.Usuario.username.ilike(f"%{usuario_username}%")
        )

    # Filtrar por ação
    if acao:
        query = query.filter(models.LogAuditoria.acao == acao)

    # Filtrar por tabela afetada
    if tabela:
        query = query.filter(models.LogAuditoria.tabela == tabela)

    logs = query.order_by(models.LogAuditoria.timestamp.desc()).limit(100).all()

    logs_data = []
    for log in logs:
        detalhes_parsed = None
        if log.detalhes:
            try:
                detalhes_parsed = json.loads(log.detalhes)
            except Exception:
                detalhes_parsed = log.detalhes

        logs_data.append({
            "id": log.id,
            "usuario": {
                "id": log.usuario_id,
                "username": log.usuario.username if log.usuario else "sistema",
                "nome": log.usuario.nome if log.usuario else "Sistema"
            },
            "acao": log.acao,
            "tabela": log.tabela,
            "registro_id": log.registro_id,
            "entidade_id": log.entidade_id,
            "unidade_id": log.unidade_id,
            "detalhes": detalhes_parsed,
            "ip": log.ip,
            "timestamp": log.timestamp
        })

    return {
        "total": len(logs_data),
        "contexto": {
            "role": current_user.role.value,
            "unidade_id": current_user.unidade_id if eh_gerente else None
        },
        "filtros_aplicados": {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "usuario_id": usuario_id,
            "usuario_username": usuario_username,
            "acao": acao,
            "tabela": tabela
        },
        "logs": logs_data,
        "observacao": "Limitado a 100 resultados mais recentes" if len(logs_data) == 100 else None
    }