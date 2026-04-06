"""
Utilitário de auditoria - Log automático de ações
"""
from sqlalchemy.orm import Session
from datetime import datetime
import models
import json
from typing import Optional


def registrar_log(
    db: Session,
    usuario: Optional[models.Usuario],
    acao: str,
    entidade_tipo: Optional[str] = None,
    entidade_id: Optional[str] = None,
    detalhes: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    """
    Registra uma ação no log de auditoria
    
    Args:
        db: Sessão do banco
        usuario: Usuário que executou a ação (None se sistema)
        acao: Nome da ação (ex: "suspender_cliente")
        entidade_tipo: Tipo de entidade afetada (ex: "Cliente")
        entidade_id: ID da entidade (ex: CPF)
        detalhes: Dicionário com detalhes adicionais
        ip_address: IP do requisitante
    """
    log = models.LogAuditoria(
        usuario_id=usuario.id if usuario else None,
        usuario_username=usuario.username if usuario else "sistema",
        acao=acao,
        entidade_tipo=entidade_tipo,
        entidade_id=entidade_id,
        detalhes=json.dumps(detalhes, ensure_ascii=False) if detalhes else None,
        ip_address=ip_address,
        data_hora=datetime.now()
    )
    
    db.add(log)
    db.commit()
    
    return log