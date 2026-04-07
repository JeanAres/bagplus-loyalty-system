"""
Router administrativo de notificações
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Notificacao, Cliente, Usuario, TipoNotificacao
from middleware.auth import get_current_user, require_role
from utils.audit import registrar_log
from datetime import datetime
from typing import Optional
import json

router = APIRouter(prefix="/api/admin/notificacoes", tags=["Admin - Notificações"])

@router.get("", summary="Listar Todas Notificações (Admin)")
def listar_todas_notificacoes(
    tipo: Optional[TipoNotificacao] = Query(None, description="Filtrar por tipo"),
    apenas_nao_lidas: bool = Query(False, description="Apenas não lidas"),
    cliente_cpf: Optional[str] = Query(None, description="Filtrar por CPF do cliente"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Lista todas as notificações do sistema com filtros
    
    **Permissão:** Admin + Gerente
    
    **Filtros opcionais:**
    - tipo: Filtrar por tipo específico
    - apenas_nao_lidas: Apenas não lidas
    - cliente_cpf: Filtrar por cliente específico
    - limit: Limite de resultados (1-1000)
    """
    query = db.query(Notificacao)
    
    # Aplicar filtros
    if tipo:
        query = query.filter(Notificacao.tipo == tipo)
    
    if apenas_nao_lidas:
        query = query.filter(Notificacao.lida == False)
    
    if cliente_cpf:
        # Verificar se cliente existe
        cliente = db.query(Cliente).filter(Cliente.cpf == cliente_cpf).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        query = query.filter(Notificacao.cliente_cpf == cliente_cpf)
    
    # Buscar notificações
    notificacoes = query.order_by(Notificacao.data_criacao.desc()).limit(limit).all()
    
    # Estatísticas gerais
    total_notificacoes = db.query(Notificacao).count()
    total_nao_lidas = db.query(Notificacao).filter(Notificacao.lida == False).count()
    
    # Estatísticas por tipo
    stats_por_tipo = {}
    for tipo_enum in TipoNotificacao:
        count = db.query(Notificacao).filter(Notificacao.tipo == tipo_enum).count()
        stats_por_tipo[tipo_enum.value] = count
    
    return {
        "estatisticas": {
            "total_notificacoes": total_notificacoes,
            "total_nao_lidas": total_nao_lidas,
            "por_tipo": stats_por_tipo
        },
        "filtros_aplicados": {
            "tipo": tipo.value if tipo else None,
            "apenas_nao_lidas": apenas_nao_lidas,
            "cliente_cpf": cliente_cpf,
            "limit": limit
        },
        "resultados": len(notificacoes),
        "notificacoes": [
            {
                "id": n.id,
                "cliente": {
                    "cpf": n.cliente_cpf,
                    "nome": n.cliente.nome if n.cliente else None
                },
                "tipo": n.tipo.value,
                "titulo": n.titulo,
                "mensagem": n.mensagem,
                "lida": n.lida,
                "data_criacao": n.data_criacao.isoformat(),
                "data_leitura": n.data_leitura.isoformat() if n.data_leitura else None
            }
            for n in notificacoes
        ]
    }

@router.post("/broadcast", summary="Enviar Notificação em Massa")
def enviar_notificacao_massa(
    tipo: TipoNotificacao = Query(..., description="Tipo da notificação"),
    titulo: str = Query(..., min_length=5, description="Título da notificação"),
    mensagem: str = Query(..., min_length=10, description="Mensagem da notificação"),
    apenas_ativos: bool = Query(True, description="Enviar apenas para clientes ativos"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin"]))
):
    """
    Envia uma notificação para múltiplos clientes
    
    **Permissão:** Admin apenas
    
    **Uso:** Notificações de sistema (novo lote importado, manutenção, etc)
    """
    from models import StatusBeneficios
    
    # Buscar clientes elegíveis
    query = db.query(Cliente)
    
    if apenas_ativos:
        query = query.filter(Cliente.status_beneficios == StatusBeneficios.ativo)
    
    clientes = query.all()
    
    if not clientes:
        raise HTTPException(status_code=404, detail="Nenhum cliente encontrado com os critérios especificados")
    
    # Criar notificações
    notificacoes_criadas = []
    for cliente in clientes:
        notificacao = Notificacao(
            cliente_cpf=cliente.cpf,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            lida=False,
            data_criacao=datetime.now()
        )
        db.add(notificacao)
        notificacoes_criadas.append(notificacao)
    
    db.commit()
    
    # LOG DE AUDITORIA
    registrar_log(
        db=db,
        usuario_id=current_user.id,
        usuario_username=current_user.username,
        acao="broadcast_notificacao",
        entidade_tipo="Notificacao",
        entidade_id="broadcast",
        detalhes=json.dumps({
            "tipo": tipo.value,
            "titulo": titulo,
            "mensagem": mensagem,
            "apenas_ativos": apenas_ativos,
            "clientes_notificados": len(clientes)
        }, ensure_ascii=False)
    )
    
    return {
        "message": f"Notificação enviada para {len(clientes)} clientes",
        "detalhes": {
            "tipo": tipo.value,
            "titulo": titulo,
            "apenas_ativos": apenas_ativos,
            "clientes_notificados": len(clientes)
        }
    }

@router.delete("/limpar-lidas", summary="Limpar Notificações Lidas Antigas")
def limpar_notificacoes_lidas(
    dias: int = Query(30, ge=1, description="Remover notificações lidas há mais de X dias"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(["admin"]))
):
    """
    Remove notificações lidas com mais de X dias
    
    **Permissão:** Admin apenas
    
    **Uso:** Limpeza de banco de dados
    """
    from datetime import timedelta
    
    data_limite = datetime.now() - timedelta(days=dias)
    
    # Buscar notificações antigas lidas
    notificacoes_antigas = db.query(Notificacao).filter(
        Notificacao.lida == True,
        Notificacao.data_leitura < data_limite
    ).all()
    
    total_removidas = len(notificacoes_antigas)
    
    # Remover
    for notificacao in notificacoes_antigas:
        db.delete(notificacao)
    
    db.commit()
    
    # LOG DE AUDITORIA
    registrar_log(
        db=db,
        usuario_id=current_user.id,
        usuario_username=current_user.username,
        acao="limpar_notificacoes_antigas",
        entidade_tipo="Notificacao",
        entidade_id="limpeza",
        detalhes=json.dumps({
            "criterio_dias": dias,
            "data_limite": data_limite.isoformat(),
            "total_removidas": total_removidas
        }, ensure_ascii=False)
    )
    
    return {
        "message": f"Limpeza concluída: {total_removidas} notificações removidas",
        "detalhes": {
            "criterio": f"Lidas há mais de {dias} dias",
            "data_limite": data_limite.isoformat(),
            "total_removidas": total_removidas
        }
    }