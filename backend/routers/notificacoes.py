"""
Router público de notificações para clientes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Notificacao, Cliente, TipoNotificacao
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/notificacoes", tags=["Notificações"])

@router.post("", summary="Criar Notificação")
def criar_notificacao(
    cliente_cpf: str = Query(..., description="CPF do cliente"),
    tipo: TipoNotificacao = Query(..., description="Tipo da notificação"),
    titulo: str = Query(..., min_length=5, description="Título da notificação"),
    mensagem: str = Query(..., min_length=10, description="Mensagem da notificação"),
    db: Session = Depends(get_db)
):
    """
    Cria uma nova notificação para o cliente
    
    **Tipos disponíveis:**
    - sacola_proximo_limite: Sacola próxima de expirar
    - sacola_expirada: Sacola atingiu limite máximo
    - desconto_disponivel: Desconto de fidelidade disponível
    - novo_lote: Novo lote importado
    - suspensao_conta: Conta suspensa
    """
    # Verificar se cliente existe
    cliente = db.query(Cliente).filter(Cliente.cpf == cliente_cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Criar notificação
    notificacao = Notificacao(
        cliente_cpf=cliente_cpf,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        lida=False,
        data_criacao=datetime.now()
    )
    
    db.add(notificacao)
    db.commit()
    db.refresh(notificacao)
    
    return {
        "message": "Notificação criada com sucesso",
        "notificacao": {
            "id": notificacao.id,
            "tipo": notificacao.tipo.value,
            "titulo": notificacao.titulo,
            "mensagem": notificacao.mensagem,
            "lida": notificacao.lida,
            "data_criacao": notificacao.data_criacao.isoformat()
        }
    }

@router.get("/{cpf}", summary="Listar Notificações do Cliente")
def listar_notificacoes_cliente(
    cpf: str,
    apenas_nao_lidas: bool = Query(False, description="Filtrar apenas não lidas"),
    db: Session = Depends(get_db)
):
    """
    Lista todas as notificações de um cliente
    
    **Filtros opcionais:**
    - apenas_nao_lidas: Se True, retorna apenas não lidas
    """
    # Verificar se cliente existe
    cliente = db.query(Cliente).filter(Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Buscar notificações
    query = db.query(Notificacao).filter(Notificacao.cliente_cpf == cpf)
    
    if apenas_nao_lidas:
        query = query.filter(Notificacao.lida == False)
    
    notificacoes = query.order_by(Notificacao.data_criacao.desc()).all()
    
    # Contar não lidas
    total_nao_lidas = db.query(Notificacao).filter(
        Notificacao.cliente_cpf == cpf,
        Notificacao.lida == False
    ).count()
    
    return {
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome
        },
        "total_notificacoes": len(notificacoes),
        "total_nao_lidas": total_nao_lidas,
        "notificacoes": [
            {
                "id": n.id,
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

@router.put("/{notificacao_id}/ler", summary="Marcar Notificação como Lida")
def marcar_como_lida(
    notificacao_id: int,
    db: Session = Depends(get_db)
):
    """
    Marca uma notificação como lida
    """
    notificacao = db.query(Notificacao).filter(Notificacao.id == notificacao_id).first()
    
    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    if notificacao.lida:
        return {
            "message": "Notificação já estava marcada como lida",
            "notificacao": {
                "id": notificacao.id,
                "lida": True,
                "data_leitura": notificacao.data_leitura.isoformat()
            }
        }
    
    # Marcar como lida
    notificacao.lida = True
    notificacao.data_leitura = datetime.now()
    
    db.commit()
    db.refresh(notificacao)
    
    return {
        "message": "Notificação marcada como lida",
        "notificacao": {
            "id": notificacao.id,
            "titulo": notificacao.titulo,
            "lida": True,
            "data_leitura": notificacao.data_leitura.isoformat()
        }
    }

@router.delete("/{notificacao_id}", summary="Remover Notificação")
def remover_notificacao(
    notificacao_id: int,
    db: Session = Depends(get_db)
):
    """
    Remove uma notificação permanentemente
    """
    notificacao = db.query(Notificacao).filter(Notificacao.id == notificacao_id).first()
    
    if not notificacao:
        raise HTTPException(status_code=404, detail="Notificação não encontrada")
    
    # Guardar info antes de deletar
    titulo = notificacao.titulo
    cliente_cpf = notificacao.cliente_cpf
    
    db.delete(notificacao)
    db.commit()
    
    return {
        "message": "Notificação removida com sucesso",
        "notificacao_removida": {
            "id": notificacao_id,
            "titulo": titulo,
            "cliente_cpf": cliente_cpf
        }
    }