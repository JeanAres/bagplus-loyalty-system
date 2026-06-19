"""
Utilitário de auditoria - Log automático de ações
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.db import models
import json
from typing import Optional


def registrar_log(
    db: Session,
    usuario: Optional[models.Usuario],
    acao: str,
    # Novos campos (Sprint 10)
    tabela: Optional[str] = None,
    registro_id: Optional[int] = None,
    # Campos legados (mantidos para compatibilidade)
    entidade_tipo: Optional[str] = None,
    entidade_id: Optional[str] = None,
    detalhes: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    # Compatibilidade: entidade_tipo vira tabela se tabela não informada
    tabela_final = tabela or entidade_tipo

    log = models.LogAuditoria(
        usuario_id=usuario.id if usuario else None,
        entidade_id=usuario.entidade_id if usuario else None,
        unidade_id=usuario.unidade_id if usuario else None,
        acao=acao,
        tabela=tabela_final,
        registro_id=int(entidade_id) if entidade_id and entidade_id.isdigit() else None,
        detalhes=json.dumps(detalhes, ensure_ascii=False) if detalhes else None,
        ip=ip_address,
        timestamp=datetime.now()
    )

    db.add(log)
    db.commit()

    return log