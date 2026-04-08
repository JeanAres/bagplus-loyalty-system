"""
Routers administrativos do sistema Bag+
Todos os endpoints sob /api/admin
"""
from . import (
    lotes,
    suspensao,
    alertas,
    relatorios,
    sacolas,
    exportar,
    usuarios,
    auditoria
)

__all__ = [
    "lotes",
    "suspensao",
    "alertas",
    "relatorios",
    "sacolas",
    "exportar",
    "usuarios",
    "auditoria"
]