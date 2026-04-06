"""
Endpoints administrativos - Suspensão de clientes
"""
from utils.audit import registrar_log
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from middleware.auth import require_role
from datetime import datetime
import models

router = APIRouter(
    prefix="/api/admin/clientes",
    tags=["Admin - Suspensão"]
)


@router.post(
    "/{cpf}/suspender",
    summary="Suspender cliente",
    description="""
    Suspende temporariamente os benefícios de um cliente.
    
    **O que acontece ao suspender:**
    -  Cliente não pode registrar novos usos de sacolas
    -  Cliente não pode ativar novas sacolas
    -  Sacolas ativas permanecem vinculadas (preservar histórico)
    -  Registra motivo e data da suspensão
    
    **Quando usar:**
    - Fraude detectada (aguardando investigação)
    - Uso indevido confirmado
    - Violação de regras do programa
    - Inadimplência (se aplicável)
    
    **Parâmetros:**
    - cpf: CPF do cliente (11 dígitos)
    - motivo: Motivo da suspensão (mínimo 10 caracteres)
    
    **Observação:** Cliente pode ser reativado posteriormente com /reativar
    
    **Diferença entre suspensão e bloqueio:**
    - Suspensão: Temporária, reversível
    - Bloqueio: Permanente (use com cautela)
    """
)

def suspender_cliente(
    cpf: str, 
    motivo: str, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))

    ):

    """Suspende benefícios do cliente"""
    
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    if cliente.status_beneficios == models.StatusBeneficios.suspenso:
        raise HTTPException(
            status_code=400,
            detail=f"Cliente já está suspenso desde {cliente.data_suspensao}"
        )
    
    if cliente.status_beneficios == models.StatusBeneficios.bloqueado:
        raise HTTPException(
            status_code=400,
            detail="Cliente está bloqueado permanentemente. Não pode ser suspenso."
        )
    
    if not motivo or len(motivo.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Motivo deve ter pelo menos 10 caracteres"
        )
    
    # Suspender
    cliente.status_beneficios = models.StatusBeneficios.suspenso
    cliente.motivo_suspensao = motivo.strip()
    cliente.data_suspensao = datetime.now()
    
    db.commit()
    # Registrar log
    registrar_log(
        db=db,
        usuario=current_user,
        acao="suspender_cliente",
        entidade_tipo="Cliente",
        entidade_id=cpf,
        detalhes={
            "motivo": motivo,
            "status_anterior": "ativo",
            "status_novo": "suspenso"
        }
    )
    db.refresh(cliente)
    
    return {
        "sucesso": True,
        "mensagem": f"Cliente {cliente.nome} suspenso com sucesso",
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "status": cliente.status_beneficios.value,
            "motivo": cliente.motivo_suspensao,
            "data_suspensao": cliente.data_suspensao
        }
    }


@router.post(
    "/{cpf}/reativar",
    summary="Reativar cliente suspenso",
    description="""
    Reativa os benefícios de um cliente anteriormente suspenso.
    
    **O que acontece ao reativar:**
    -  Cliente volta a poder usar sacolas normalmente
    -  Cliente pode ativar novas sacolas
    -  Histórico de suspensão é preservado
    -  Motivo da suspensão é limpo
    
    **Validações:**
    - Cliente deve estar suspenso (não funciona para bloqueados)
    - Não pode reativar cliente que nunca foi suspenso
    
    **Parâmetro:**
    - cpf: CPF do cliente (11 dígitos)
    
    **Observação:** 
    - Clientes bloqueados NÃO podem ser reativados (bloqueio é permanente)
    - Para casos excepcionais de bloqueio indevido, use ferramenta de banco de dados
    
    **Quando usar:**
    - Investigação concluída (sem fraude)
    - Problema resolvido pelo cliente
    - Suspensão foi acidente/erro
    """
)
def reativar_cliente(
    cpf: str, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))

    ):

    """Reativa benefícios do cliente"""
    
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    if cliente.status_beneficios == models.StatusBeneficios.ativo:
        raise HTTPException(
            status_code=400,
            detail="Cliente já está ativo. Não há nada para reativar."
        )
    
    if cliente.status_beneficios == models.StatusBeneficios.bloqueado:
        raise HTTPException(
            status_code=400,
            detail="Cliente está bloqueado permanentemente. Não pode ser reativado via API."
        )
    
    # Reativar
    motivo_anterior = cliente.motivo_suspensao
    data_suspensao_anterior = cliente.data_suspensao
    status_anterior = cliente.status_beneficios.value
    
    cliente.status_beneficios = models.StatusBeneficios.ativo
    cliente.motivo_suspensao = None
    cliente.data_suspensao = None
    
    db.commit()
    # Registrar log
    registrar_log(
        db=db,
        usuario=current_user,
        acao="reativar_cliente",
        entidade_tipo="Cliente",
        entidade_id=cpf,
        detalhes={
            "status_anterior": status_anterior,
            "status_novo": "ativo"
        }
    )
    db.refresh(cliente)
    
    return {
        "sucesso": True,
        "mensagem": f"Cliente {cliente.nome} reativado com sucesso",
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "status": cliente.status_beneficios.value
        },
        "suspensao_anterior": {
            "motivo": motivo_anterior,
            "data": data_suspensao_anterior
        }
    }


@router.get(
    "/suspensos",
    summary="Listar clientes suspensos/bloqueados",
    description="""
    Lista todos os clientes que estão com benefícios suspensos ou bloqueados.
    
    **Informações retornadas:**
    - CPF e nome do cliente
    - Status (suspenso ou bloqueado)
    - Motivo da suspensão/bloqueio
    - Data da suspensão
    - Quantidade de sacolas ativas
    
    **Filtros disponíveis (query params):**
    - Sem filtros: retorna suspensos E bloqueados
    - status=suspenso: apenas suspensos
    - status=bloqueado: apenas bloqueados
    
    **Quando usar:**
    - Revisar casos de suspensão
    - Auditoria de bloqueios
    - Decidir sobre reativações
    
    **Observação:** Ordenado por data de suspensão (mais recente primeiro)
    """
)
def listar_clientes_suspensos(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
    
    ):

    """Lista clientes suspensos ou bloqueados"""
    
    clientes = db.query(models.Cliente).filter(
        models.Cliente.status_beneficios.in_([
            models.StatusBeneficios.suspenso,
            models.StatusBeneficios.bloqueado
        ])
    ).order_by(models.Cliente.data_suspensao.desc()).all()
    
    clientes_data = []
    for cliente in clientes:
        # Contar sacolas ativas
        sacolas_ativas = db.query(models.Sacola).filter(
            models.Sacola.cliente_cpf == cliente.cpf,
            models.Sacola.status == models.StatusSacola.ativo
        ).count()
        
        clientes_data.append({
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "status": cliente.status_beneficios.value,
            "motivo": cliente.motivo_suspensao,
            "data_suspensao": cliente.data_suspensao,
            "sacolas_ativas": sacolas_ativas
        })
    
    return {
        "total": len(clientes_data),
        "clientes": clientes_data
    }