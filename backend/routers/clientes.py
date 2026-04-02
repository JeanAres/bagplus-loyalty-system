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
    "/buscar",
    summary="Buscar cliente por nome",
    description="""
    Busca clientes pelo nome (busca parcial, case-insensitive).
    
    **Funcionalidade:**
    - Busca por nome parcial (ex: "joão" encontra "João Silva", "Maria João")
    - Case-insensitive (maiúsculas/minúsculas não importam)
    - Retorna todos os clientes que contêm o termo buscado
    
    **Informações retornadas:**
    - CPF do cliente
    - Nome completo
    - Quantidade de sacolas ativas
    - Status dos benefícios
    
    **Quando usar:**
    - Caixa sabe o nome mas não o CPF
    - Buscar cliente rapidamente
    - Listar clientes com nome similar
    
    **Parâmetro:**
    - nome: Termo de busca (mínimo 3 caracteres)
    
    **Exemplos:**
```
    GET /api/clientes/buscar?nome=joão
    GET /api/clientes/buscar?nome=silva
    GET /api/clientes/buscar?nome=maria
```
    
    **Observação:** 
    - Retorna lista vazia se nenhum cliente corresponder
    - Limite de 20 resultados para performance
    """
)
def buscar_cliente_por_nome(nome: str, db: Session = Depends(get_db)):
    """Busca clientes por nome (parcial)"""
    
    # Validar termo de busca
    if len(nome.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Nome deve ter pelo menos 3 caracteres para busca"
        )
    
    # Buscar clientes (LIKE case-insensitive)
    termo_busca = f"%{nome.strip()}%"
    clientes = db.query(models.Cliente).filter(
        models.Cliente.nome.ilike(termo_busca)
    ).limit(20).all()
    
    # Montar resultado
    resultado = []
    for cliente in clientes:
        # Contar sacolas ativas
        sacolas_ativas = db.query(models.Sacola).filter(
            models.Sacola.cliente_cpf == cliente.cpf,
            models.Sacola.status == models.StatusSacola.ativo
        ).count()
        
        resultado.append({
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "sacolas_ativas": sacolas_ativas,
            "status_beneficios": cliente.status_beneficios.value
        })
    
    return {
        "total_encontrados": len(resultado),
        "termo_buscado": nome.strip(),
        "clientes": resultado
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


@router.get(
    "/{cpf}/historico-completo",
    summary="Histórico completo do cliente",
    description="""
    Retorna timeline completa de TUDO que o cliente fez no sistema.
    
    **Informações consolidadas:**
    
    ** Dados do Cliente:**
    - CPF, nome, data de cadastro
    - Status atual dos benefícios
    
    ** Resumo de Compras:**
    - Total gasto em todas as compras
    - Valor médio por compra
    - Total de usos realizados
    - Primeira e última compra
    
    ** Sacolas:**
    - Sacolas ativas (em uso)
    - Sacolas devolvidas (histórico)
    - Total de sacolas já vinculadas
    
    ** Alertas:**
    - Alertas detectados automaticamente
    - Status de resolução
    - Observações dos alertas resolvidos
    
    ** Suspensões:**
    - Histórico de suspensões (se houver)
    - Motivos de suspensão
    - Datas de suspensão/reativação
    
    ** Timeline:**
    - Eventos ordenados por data (mais recente primeiro)
    - Tipos: cadastro, vinculação, uso, devolução, alerta, suspensão
    
    **Quando usar:**
    - Suporte ao cliente
    - Investigação de fraudes
    - Auditoria de histórico
    - Análise de comportamento
    
    **Parâmetro:**
    - cpf: CPF do cliente (11 dígitos)
    
    **Observação:** Timeline pode ser extensa para clientes antigos
    """
)
def historico_completo_cliente(cpf: str, db: Session = Depends(get_db)):
    """Retorna histórico completo e timeline do cliente"""
    
    # Buscar cliente
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # ========== RESUMO DE COMPRAS ==========
    registros = db.query(models.RegistroUso).join(
        models.Sacola
    ).filter(
        models.Sacola.cliente_cpf == cpf
    ).all()
    
    total_gasto = sum(r.valor_compra for r in registros)
    total_usos = len(registros)
    valor_medio = total_gasto / total_usos if total_usos > 0 else 0
    
    primeira_compra = min([r.data_uso for r in registros]) if registros else None
    ultima_compra = max([r.data_uso for r in registros]) if registros else None
    
    # ========== SACOLAS ==========
    sacolas_ativas = db.query(models.Sacola).filter(
        models.Sacola.cliente_cpf == cpf,
        models.Sacola.status == models.StatusSacola.ativo
    ).all()
    
    sacolas_devolvidas = db.query(models.Sacola).filter(
        models.Sacola.cliente_cpf == cpf,
        models.Sacola.status == models.StatusSacola.devolvido
    ).all()
    
    total_sacolas = len(sacolas_ativas) + len(sacolas_devolvidas)
    
    # ========== ALERTAS ==========
    alertas = db.query(models.Alerta).filter(
        models.Alerta.cliente_cpf == cpf
    ).order_by(models.Alerta.data_deteccao.desc()).all()
    
    alertas_data = []
    for alerta in alertas:
        alertas_data.append({
            "tipo": alerta.tipo.value,
            "gravidade": alerta.gravidade.value,
            "descricao": alerta.descricao,
            "data_deteccao": alerta.data_deteccao,
            "resolvido": alerta.resolvido,
            "observacao": alerta.observacao
        })
    
    # ========== TIMELINE ==========
    timeline = []
    
    # Evento: Cadastro
    timeline.append({
        "tipo": "cadastro",
        "data": cliente.data_cadastro,
        "descricao": f"Cliente {cliente.nome} cadastrado no sistema"
    })
    
    # Eventos: Vinculações de sacolas
    for sacola in sacolas_ativas + sacolas_devolvidas:
        if sacola.data_vinculacao:
            timeline.append({
                "tipo": "vinculacao",
                "data": sacola.data_vinculacao,
                "descricao": f"Sacola {sacola.id} vinculada ao cliente"
            })
    
    # Eventos: Usos
    for registro in registros:
        timeline.append({
            "tipo": "uso",
            "data": registro.data_uso,
            "descricao": f"Compra de R$ {registro.valor_compra:.2f}",
            "valor": registro.valor_compra
        })
    
    # Eventos: Devoluções
    for sacola in sacolas_devolvidas:
        if sacola.data_devolucao:
            timeline.append({
                "tipo": "devolucao",
                "data": sacola.data_devolucao,
                "descricao": f"Sacola {sacola.id} devolvida"
            })
    
    # Eventos: Alertas
    for alerta in alertas:
        timeline.append({
            "tipo": "alerta",
            "data": alerta.data_deteccao,
            "descricao": f"Alerta: {alerta.descricao}",
            "gravidade": alerta.gravidade.value
        })
    
    # Evento: Suspensão (se houver)
    if cliente.data_suspensao:
        timeline.append({
            "tipo": "suspensao",
            "data": cliente.data_suspensao,
            "descricao": f"Cliente suspenso. Motivo: {cliente.motivo_suspensao}"
        })
    
    # Ordenar timeline por data (mais recente primeiro)
    timeline.sort(key=lambda x: x['data'], reverse=True)
    
    # ========== MONTAR RESPONSE ==========
    return {
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "data_cadastro": cliente.data_cadastro,
            "status_beneficios": cliente.status_beneficios.value,
            "motivo_suspensao": cliente.motivo_suspensao,
            "data_suspensao": cliente.data_suspensao
        },
        
        "resumo_compras": {
            "total_gasto": round(total_gasto, 2),
            "valor_medio_compra": round(valor_medio, 2),
            "total_usos": total_usos,
            "primeira_compra": primeira_compra,
            "ultima_compra": ultima_compra
        },
        
        "sacolas": {
            "total_sacolas_vinculadas": total_sacolas,
            "ativas": len(sacolas_ativas),
            "devolvidas": len(sacolas_devolvidas),
            "lista_ativas": [s.id for s in sacolas_ativas],
            "lista_devolvidas": [s.id for s in sacolas_devolvidas]
        },
        
        "alertas": {
            "total": len(alertas),
            "lista": alertas_data
        },
        
        "timeline": timeline
    }

@router.get(
    "/{cpf}/validar",
    summary="Validar se cliente existe",
    description="""
    Verifica se um cliente existe no sistema sem criar cadastro.
    
    **Funcionalidade:**
    - Valida CPF rapidamente
    - Retorna informações básicas se existir
    - Útil antes de vincular sacolas
    
    **Informações retornadas:**
    - existe: true/false
    - Se existe:
      - CPF e nome
      - Status dos benefícios
      - Quantidade de sacolas ativas
      - Motivo de suspensão (se houver)
    
    **Quando usar:**
    - Antes de ativar sacola (verificar se cliente existe)
    - Validação rápida no caixa
    - Verificar status antes de permitir uso
    
    **Parâmetro:**
    - cpf: CPF do cliente (11 dígitos)
    
    **Exemplos:**
```
    GET /api/clientes/12345678900/validar
```
    
    **Diferença de outros endpoints:**
    - GET /api/clientes/{cpf}/sacolas → Retorna sacolas (erro se não existe)
    - GET /api/clientes/{cpf}/validar → Só valida (não dá erro)
    
    **Observação:** 
    - Não cria cliente se não existir
    """
)
def validar_cliente(cpf: str, db: Session = Depends(get_db)):
    """Valida se cliente existe sem criar cadastro"""
    
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    
    if not cliente:
        return {
            "existe": False,
            "cpf": cpf
        }
    
    # Contar sacolas ativas
    sacolas_ativas = db.query(models.Sacola).filter(
        models.Sacola.cliente_cpf == cpf,
        models.Sacola.status == models.StatusSacola.ativo
    ).count()
    
    return {
        "existe": True,
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "status_beneficios": cliente.status_beneficios.value,
            "sacolas_ativas": sacolas_ativas,
            "suspenso": cliente.status_beneficios != models.StatusBeneficios.ativo,
            "motivo_suspensao": cliente.motivo_suspensao if cliente.status_beneficios != models.StatusBeneficios.ativo else None
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