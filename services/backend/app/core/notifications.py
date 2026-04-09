"""
Utilitário para criação automática de notificações
"""
from sqlalchemy.orm import Session
from app.db.models import Notificacao, TipoNotificacao
from datetime import datetime

def criar_notificacao_automatica(
    db: Session,
    cliente_cpf: str,
    tipo: TipoNotificacao,
    titulo: str,
    mensagem: str
) -> Notificacao:
    """
    Cria uma notificação automática para o cliente
    
    Args:
        db: Sessão do banco de dados
        cliente_cpf: CPF do cliente
        tipo: Tipo da notificação
        titulo: Título da notificação
        mensagem: Mensagem da notificação
    
    Returns:
        Notificacao criada
    """
    notificacao = Notificacao(
        cliente_cpf=cliente_cpf,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        lida=False,
        data_criacao=datetime.now()
    )
    
    db.add(notificacao)
    
    return notificacao

def notificar_sacola_proximo_limite(db: Session, cliente_cpf: str, sacola_id: str, utilizacoes: int):
    """Notifica cliente que sacola está próxima do limite"""
    return criar_notificacao_automatica(
        db=db,
        cliente_cpf=cliente_cpf,
        tipo=TipoNotificacao.sacola_proximo_limite,
        titulo=f"Atenção: Sacola {sacola_id} próxima do limite",
        mensagem=f"Sua sacola {sacola_id} já foi utilizada {utilizacoes} vezes e está próxima do limite de 40 usos. "
                 f"Planeje a devolução em breve para receber seu desconto!"
    )

def notificar_sacola_expirada(db: Session, cliente_cpf: str, sacola_id: str):
    """Notifica cliente que sacola atingiu o limite"""
    return criar_notificacao_automatica(
        db=db,
        cliente_cpf=cliente_cpf,
        tipo=TipoNotificacao.sacola_expirada,
        titulo=f"Sacola {sacola_id} atingiu o limite",
        mensagem=f"Sua sacola {sacola_id} atingiu o limite de 40 utilizações. "
                 f"Devolva-a para receber seu desconto e ativar uma nova sacola!"
    )

def notificar_desconto_disponivel(db: Session, cliente_cpf: str, marco: int):
    """Notifica cliente sobre desconto de fidelidade disponível"""
    descontos = {
        10: "R$ 5,00",
        20: "R$ 10,00",
        30: "R$ 15,00",
        40: "R$ 20,00"
    }
    
    desconto = descontos.get(marco, "disponível")
    
    return criar_notificacao_automatica(
        db=db,
        cliente_cpf=cliente_cpf,
        tipo=TipoNotificacao.desconto_disponivel,
        titulo=f" Parabéns! Desconto de {desconto} desbloqueado",
        mensagem=f"Você atingiu {marco} usos de sacola! Utilize seu desconto de {desconto} na próxima compra. "
                 f"Continue usando suas sacolas e acumule ainda mais benefícios!"
    )

def notificar_novo_lote(db: Session, cliente_cpf: str, lote_id: int, quantidade: int):
    """Notifica cliente sobre novo lote importado"""
    return criar_notificacao_automatica(
        db=db,
        cliente_cpf=cliente_cpf,
        tipo=TipoNotificacao.novo_lote,
        titulo="Novas sacolas disponíveis!",
        mensagem=f"Um novo lote de {quantidade} sacolas foi importado. "
                 f"Visite o mercado para ativar sua nova sacola!"
    )

def notificar_suspensao_conta(db: Session, cliente_cpf: str, motivo: str):
    """Notifica cliente sobre suspensão da conta"""
    return criar_notificacao_automatica(
        db=db,
        cliente_cpf=cliente_cpf,
        tipo=TipoNotificacao.suspensao_conta,
        titulo="Conta suspensa",
        mensagem=f"Sua conta foi suspensa. Motivo: {motivo}. "
                 f"Entre em contato com o mercado para mais informações."
    )