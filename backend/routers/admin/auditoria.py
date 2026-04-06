"""
Endpoints administrativos - Logs de auditoria
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime
import models
from middleware.auth import require_role
import json

router = APIRouter(
    prefix="/api/admin/auditoria",
    tags=["Admin - Auditoria"]
)


@router.get(
    "/logs",
    summary="Consultar logs de auditoria",
    description="""
    Retorna logs de ações administrativas para auditoria.
    
    **Permissão:** Admin ou Gerente
    
    **Filtros disponíveis (opcionais):**
    - data_inicio: Data inicial (YYYY-MM-DD)
    - data_fim: Data final (YYYY-MM-DD)
    - usuario_id: Filtrar por usuário específico
    - acao: Tipo de ação (suspender_cliente, transferir_sacola, etc)
    - entidade_tipo: Tipo de entidade (Cliente, Sacola, Usuario)
    
    **Informações retornadas:**
    - ID do log
    - Usuário que executou (username e nome)
    - Ação realizada
    - Entidade afetada (tipo e ID)
    - Detalhes da ação (JSON)
    - IP de origem
    - Data e hora
    
    **Exemplos:**

# Todos os logs
GET /api/admin/auditoria/logs

# Logs de suspensões
GET /api/admin/auditoria/logs?acao=suspender_cliente

# Logs de um usuário específico
GET /api/admin/auditoria/logs?usuario_id=1

# Logs de março
GET /api/admin/auditoria/logs?data_inicio=2026-03-01&data_fim=2026-03-31

**Quando usar:**
    - Auditoria de segurança
    - Investigação de ações
    - Compliance e conformidade
    - Rastreamento de alterações
    
    **Observação:** 
    - Logs ordenados por data (mais recente primeiro)
    - Limite de 100 resultados por consulta
    """
)
def consultar_logs(
    data_inicio: str = None,
    data_fim: str = None,
    usuario_id: int = None,
    acao: str = None,
    entidade_tipo: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Consulta logs de auditoria com filtros"""
    
    # Query base
    query = db.query(models.LogAuditoria)
    
    # Filtrar por período
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(models.LogAuditoria.data_hora >= dt_inicio)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data início inválida. Use formato: YYYY-MM-DD"
            )
    
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(models.LogAuditoria.data_hora <= dt_fim)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data fim inválida. Use formato: YYYY-MM-DD"
            )
    
    # Filtrar por usuário
    if usuario_id:
        query = query.filter(models.LogAuditoria.usuario_id == usuario_id)
    
    # Filtrar por ação
    if acao:
        query = query.filter(models.LogAuditoria.acao == acao)
    
    # Filtrar por tipo de entidade
    if entidade_tipo:
        query = query.filter(models.LogAuditoria.entidade_tipo == entidade_tipo)
    
    # Executar query (limitar a 100 resultados)
    logs = query.order_by(models.LogAuditoria.data_hora.desc()).limit(100).all()
    
    # Montar response
    logs_data = []
    for log in logs:
        # Buscar usuário
        usuario = None
        if log.usuario_id:
            usuario = db.query(models.Usuario).filter(
                models.Usuario.id == log.usuario_id
            ).first()
        
        # Parse detalhes JSON
        detalhes_parsed = None
        if log.detalhes:
            try:
                detalhes_parsed = json.loads(log.detalhes)
            except:
                detalhes_parsed = log.detalhes
        
        logs_data.append({
            "id": log.id,
            "usuario": {
                "id": log.usuario_id,
                "username": log.usuario_username,
                "nome": usuario.nome if usuario else "Sistema"
            },
            "acao": log.acao,
            "entidade": {
                "tipo": log.entidade_tipo,
                "id": log.entidade_id
            },
            "detalhes": detalhes_parsed,
            "ip_address": log.ip_address,
            "data_hora": log.data_hora
        })
    
    return {
        "total": len(logs_data),
        "filtros_aplicados": {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "usuario_id": usuario_id,
            "acao": acao,
            "entidade_tipo": entidade_tipo
        },
        "logs": logs_data,
        "observacao": "Limitado a 100 resultados mais recentes" if len(logs_data) == 100 else None
    }