"""
Endpoints relacionados a clientes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime
import models

router = APIRouter(
    prefix="/api/clientes",
    tags=["Clientes"]
)


@router.post(
    "/",
    summary="Cadastrar novo cliente",
    description="""
    Cadastra um novo cliente no programa de fidelidade Bag+.
    
    **Quando usar:**
    - Primeiro contato do cliente com o programa
    - Antes de vincular qualquer sacola ao cliente
    
    **Validações aplicadas:**
    - CPF deve ter exatamente 11 dígitos (aceita formatação)
    - Nome deve ter no mínimo 3 caracteres
    - CPF não pode estar duplicado no sistema
    
    **Observação:** Aceita CPF com ou sem formatação (123.456.789-00 ou 12345678900)
    """
)
def criar_cliente(cpf: str, nome: str, db: Session = Depends(get_db)):
    """Cria um novo cliente no sistema"""
    
    # Validar CPF (apenas números)
    cpf_numeros = cpf.replace('.', '').replace('-', '')
    if len(cpf_numeros) != 11 or not cpf_numeros.isdigit():
        raise HTTPException(status_code=400, detail="CPF inválido. Deve conter 11 dígitos")
    
    # Validar nome
    if len(nome.strip()) < 3:
        raise HTTPException(status_code=400, detail="Nome deve ter pelo menos 3 caracteres")
    
    # Verificar se cliente já existe
    cliente_existente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if cliente_existente:
        raise HTTPException(status_code=400, detail="Cliente já cadastrado")
    
    # Criar cliente
    cliente = models.Cliente(cpf=cpf, nome=nome.strip())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    
    return {
        "sucesso": True,
        "mensagem": "Cliente criado com sucesso",
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "data_cadastro": cliente.data_cadastro
        }
    }


@router.get(
    "/",
    summary="Listar todos os clientes",
    description="""
    Lista todos os clientes cadastrados no sistema com informações básicas.
    
    **Retorna:**
    - Total de clientes
    - Lista com CPF, nome, data de cadastro e quantidade de sacolas ativas
    
    **Uso:** Visão geral dos clientes cadastrados
    """
)
def listar_clientes(db: Session = Depends(get_db)):
    """Lista todos os clientes cadastrados"""
    
    clientes = db.query(models.Cliente).all()
    
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
            "data_cadastro": cliente.data_cadastro,
            "sacolas_ativas": sacolas_ativas,
            "status_beneficios": cliente.status_beneficios.value
        })
    
    return {
        "total": len(clientes_data),
        "clientes": clientes_data
    }


@router.get(
    "/{cpf}/sacolas",
    summary="Listar sacolas do cliente",
    description="""
    Lista todas as sacolas ativas vinculadas a um cliente específico.
    
    **Retorna:**
    - Informações do cliente
    - Lista de sacolas ativas com estatísticas de uso
    - Dias de uso de cada sacola
    - Status de cada sacola
    
    **Quando usar:** Ver quais sacolas o cliente possui atualmente
    """
)
def listar_sacolas_cliente(cpf: str, db: Session = Depends(get_db)):
    """Lista todas as sacolas ativas de um cliente"""
    
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    sacolas = db.query(models.Sacola).filter(
        models.Sacola.cliente_cpf == cpf,
        models.Sacola.status == models.StatusSacola.ativo
    ).all()
    
    sacolas_data = []
    for sacola in sacolas:
        if sacola.data_vinculacao:
            dias_uso = (datetime.now() - sacola.data_vinculacao).days
        else:
            dias_uso = 0
            
        sacolas_data.append({
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "dias_de_uso": dias_uso,
            "status": sacola.status.value,
            "data_criacao": sacola.data_criacao
        })
    
    return {
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome
        },
        "total_sacolas": len(sacolas_data),
        "sacolas": sacolas_data
    }


@router.get(
    "/{cpf}/estatisticas",
    summary="Estatísticas do cliente",
    description="""
    Retorna estatísticas consolidadas de compras do cliente.
    
    **Informações retornadas:**
    - Total gasto em todas as compras
    - Valor médio por compra
    - Total de usos realizados
    - Número de sacolas ativas
    
    **Quando usar:** Análise de comportamento do cliente
    
    **Nota:** Considera apenas sacolas ativas do cliente
    """
)
def estatisticas_cliente(cpf: str, db: Session = Depends(get_db)):
    """Retorna estatísticas de compras do cliente"""
    
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Buscar todos os registros de uso das sacolas do cliente
    registros = db.query(models.RegistroUso).join(
        models.Sacola
    ).filter(
        models.Sacola.cliente_cpf == cpf
    ).all()
    
    total_gasto = sum(r.valor_compra for r in registros)
    total_usos = len(registros)
    valor_medio = total_gasto / total_usos if total_usos > 0 else 0
    
    # Contar sacolas ativas
    sacolas_ativas = db.query(models.Sacola).filter(
        models.Sacola.cliente_cpf == cpf,
        models.Sacola.status == models.StatusSacola.ativo
    ).count()
    
    return {
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome
        },
        "estatisticas": {
            "total_gasto": round(total_gasto, 2),
            "valor_medio_compra": round(valor_medio, 2),
            "total_usos": total_usos,
            "sacolas_ativas": sacolas_ativas
        }
    }


@router.delete(
    "/{cpf}",
    summary="Excluir cliente (restritivo)",
    description="""
    Exclui um cliente do sistema com validações restritivas.
    
    **ATENÇÃO - Validações Aplicadas:**
    -  Bloqueia se cliente possui sacolas ativas
    -  Bloqueia se cliente possui sacolas devolvidas (preservar histórico)
    -  Bloqueia se cliente possui alertas registrados
    -  Só permite exclusão de clientes "limpos" (nunca usaram o sistema)
    
    **Objetivo:** Proteger dados históricos e rastreabilidade
    
    **Quando usar:** Cadastro duplicado ou erro de digitação no cadastro inicial
    
    **Não usar para:** Clientes que já utilizaram o sistema (use suspensão)
    """
)
def excluir_cliente(cpf: str, db: Session = Depends(get_db)):
    """Exclui cliente do sistema (apenas se nunca usou)"""
    
    # Buscar cliente
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Verificar se tem sacolas ativas
    sacolas_ativas = db.query(models.Sacola).filter(
        models.Sacola.cliente_cpf == cpf,
        models.Sacola.status == models.StatusSacola.ativo
    ).count()
    
    if sacolas_ativas > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cliente possui {sacolas_ativas} sacolas ativas. Não é possível excluir."
        )
    
    # Verificar se tem sacolas devolvidas (histórico)
    sacolas_devolvidas = db.query(models.Sacola).filter(
        models.Sacola.cliente_cpf == cpf,
        models.Sacola.status == models.StatusSacola.devolvido
    ).count()
    
    if sacolas_devolvidas > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cliente possui histórico de {sacolas_devolvidas} sacolas devolvidas. Não é possível excluir para preservar dados históricos."
        )
    
    # Verificar se tem alertas
    alertas = db.query(models.Alerta).filter(
        models.Alerta.cliente_cpf == cpf
    ).count()
    
    if alertas > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cliente possui {alertas} alertas registrados. Não é possível excluir para preservar dados históricos."
        )
    
    # Se chegou aqui, cliente está "limpo" - pode excluir
    db.delete(cliente)
    db.commit()
    
    return {
        "sucesso": True,
        "mensagem": f"Cliente {cliente.nome} (CPF: {cpf}) excluído com sucesso"
    }