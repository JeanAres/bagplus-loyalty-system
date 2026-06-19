"""
Endpoints relacionados a clientes
"""
from app.core.validators import sanitize_string, validar_cpf_formato, validar_nome
from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import require_role
from sqlalchemy.orm import Session
from app.db.session import get_db
from datetime import datetime
from app.db import models

router = APIRouter(
    prefix="/api/clientes",
    tags=["Clientes"]
)


@router.post(
    "/",
    summary="Cadastrar novo cliente",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def criar_cliente(cpf: str, nome: str, telefone: str = None, db: Session = Depends(get_db)):
    """
    Cadastra um novo cliente no programa de fidelidade Bag+.
    
    **Quando usar:**
    - Primeiro contato do cliente com o programa
    - Antes de vincular qualquer sacola ao cliente
    
    **Validações aplicadas:**
    - CPF deve ter exatamente 11 dígitos (aceita formatação)
    - Nome deve ter no mínimo 3 caracteres
    - CPF não pode estar duplicado no sistema
    - Telefone: 10 dígitos (fixo) ou 11 dígitos (celular)
    
    **Observação:** Aceita CPF com ou sem formatação (123.456.789-00 ou 12345678900)
    """
    
    # Validar e sanitizar CPF
    cpf_validado = validar_cpf_formato(cpf)
    
    # Validar e sanitizar nome
    nome_validado = validar_nome(nome)
    
    # Validar e sanitizar telefone
    telefone_validado = None
    if telefone:
        telefone_limpo = ''.join(filter(str.isdigit, telefone))
        if len(telefone_limpo) not in (10, 11):
            raise HTTPException(
                status_code=400,
                detail="Telefone inválido. Use 10 dígitos (fixo) ou 11 dígitos (celular)"
            )
        telefone_validado = telefone_limpo
    
    # Verificar se cliente já existe
    cliente_existente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_validado).first()
    if cliente_existente:
        raise HTTPException(status_code=400, detail="Cliente já cadastrado")
    
    # Criar cliente
    cliente = models.Cliente(cpf=cpf_validado, nome=nome_validado, telefone=telefone_validado)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    
    return {
        "sucesso": True,
        "mensagem": "Cliente criado com sucesso",
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "telefone": cliente.telefone,
            "data_cadastro": cliente.data_cadastro
        }
    }

@router.get(
    "/",
    summary="Listar todos os clientes",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def listar_clientes(db: Session = Depends(get_db)):
    """
    Lista todos os clientes cadastrados no sistema com informações básicas.
    
    **Retorna:**
    - Total de clientes
    - Lista com CPF, nome, data de cadastro e quantidade de sacolas ativas
    
    **Uso:** Visão geral dos clientes cadastrados
    """
    
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
            "telefone": cliente.telefone,
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
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def buscar_cliente_por_nome(nome: str, db: Session = Depends(get_db)):
    """
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

    GET /api/clientes/buscar?nome=joão
    GET /api/clientes/buscar?nome=silva
    GET /api/clientes/buscar?nome=maria
    
    **Observação:** 
    - Retorna lista vazia se nenhum cliente corresponder
    - Limite de 20 resultados para performance
    """
    
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
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def listar_sacolas_cliente(cpf: str, db: Session = Depends(get_db)):
    """
    Lista todas as sacolas ativas vinculadas a um cliente específico.
    
    **Retorna:**
    - Informações do cliente
    - Lista de sacolas ativas com estatísticas de uso
    - Dias de uso de cada sacola
    - Status de cada sacola
    
    **Quando usar:** Ver quais sacolas o cliente possui atualmente
    """
    
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
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def estatisticas_cliente(cpf: str, db: Session = Depends(get_db)):
    """
    Retorna estatísticas consolidadas de compras do cliente.
    
    **Informações retornadas:**
    - Total gasto em todas as compras
    - Valor médio por compra
    - Total de usos realizados
    - Número de sacolas ativas
    
    **Quando usar:** Análise de comportamento do cliente
    
    **Nota:** Considera apenas sacolas ativas do cliente
    """
    
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
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def historico_completo_cliente(cpf: str, db: Session = Depends(get_db)):
    """
    Retorna timeline completa de TUDO que o cliente fez no sistema.
    
    **Informações consolidadas:**
    
    **Dados do Cliente:**
    - CPF, nome, data de cadastro
    - Status atual dos benefícios
    
    **Resumo de Compras:**
    - Total gasto em todas as compras
    - Valor médio por compra
    - Total de usos realizados
    - Primeira e última compra
    
    **Sacolas:**
    - Sacolas ativas (em uso)
    - Sacolas devolvidas (histórico)
    - Total de sacolas já vinculadas
    
    **Alertas:**
    - Alertas detectados automaticamente
    - Status de resolução
    - Observações dos alertas resolvidos
    
    **Suspensões:**
    - Histórico de suspensões (se houver)
    - Motivos de suspensão
    - Datas de suspensão/reativação
    
    **Timeline:**
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
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def validar_cliente(cpf: str, db: Session = Depends(get_db)):
    """
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

    GET /api/clientes/12345678900/validar
    
    **Diferença de outros endpoints:**
    - GET /api/clientes/{cpf}/sacolas → Retorna sacolas (erro se não existe)
    - GET /api/clientes/{cpf}/validar → Só valida (não dá erro)
    
    **Observação:** 
    - Não cria cliente se não existir
    """
    
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
            "telefone": cliente.telefone,
            "data_cadastro": cliente.data_cadastro,
            "status_beneficios": cliente.status_beneficios.value,
            "sacolas_ativas": sacolas_ativas,
            "suspenso": cliente.status_beneficios != models.StatusBeneficios.ativo,
            "motivo_suspensao": cliente.motivo_suspensao if cliente.status_beneficios != models.StatusBeneficios.ativo else None
        }
    }
   
@router.post(
    "/validar-cpf", 
    summary="Validar CPF",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def validar_cpf_endpoint(cpf: str):
    """
    Valida se um CPF é válido (formato e dígitos verificadores).
    
    - **cpf**: CPF com 11 dígitos (apenas números)
    
    **Retorna:**
    - valido: true/false
    - mensagem: Descrição do resultado
    
    **Quando usar:**
    - Antes de cadastrar cliente (validar CPF digitado)
    - Validação em formulários
    - Verificação de dados
    
    **Exemplos de CPF válido:**
    - 12345678909
    - 11144477735
    
    **Exemplos de CPF inválido:**
    - 11111111111 (todos dígitos iguais)
    - 12345678900 (dígitos verificadores incorretos)
    """
    from validate_docbr import CPF
    
    # Validar comprimento
    if len(cpf) != 11:
        return {
            "cpf": cpf,
            "valido": False,
            "mensagem": "CPF deve ter exatamente 11 dígitos"
        }
    
    # Validar se são apenas números
    if not cpf.isdigit():
        return {
            "cpf": cpf,
            "valido": False,
            "mensagem": "CPF deve conter apenas números"
        }
    
    validador = CPF()
    
    # Validar dígitos verificadores
    cpf_valido = validador.validate(cpf)
    
    if cpf_valido:
        return {
            "cpf": cpf,
            "valido": True,
            "mensagem": "CPF válido"
        }
    else:
        return {
            "cpf": cpf,
            "valido": False,
            "mensagem": "CPF inválido (dígitos verificadores incorretos)"
        }

@router.put(
    "/{cpf}",
    summary="Editar dados do cliente",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def editar_cliente(cpf: str, nome: str = None, telefone: str = None, db: Session = Depends(get_db)):
    """
    Atualiza nome e/ou telefone de um cliente existente.

    **Quando usar:**
    - Corrigir nome digitado incorretamente no cadastro
    - Adicionar ou atualizar telefone do cliente
    - Atualizar dados após solicitação do cliente

    **Campos editáveis:**
    - nome: Nome completo (mínimo 3 caracteres)
    - telefone: Telefone com 10 ou 11 dígitos (opcional)

    **Validações aplicadas:**
    - Cliente deve existir no sistema
    - Nome deve ter no mínimo 3 caracteres (se informado)
    - Telefone: 10 dígitos (fixo) ou 11 dígitos (celular) (se informado)

    **Observação:** Passe apenas os campos que deseja atualizar.
    Campos não informados permanecem inalterados.

    **Parâmetros:**
    - cpf: CPF do cliente (11 dígitos)
    - nome: Novo nome completo (opcional)
    - telefone: Novo telefone (opcional, envie vazio para remover)

    **Exemplos:**

    PUT /api/clientes/12345678900?nome=João Silva
    PUT /api/clientes/12345678900?telefone=51999998888
    PUT /api/clientes/12345678900?nome=João Silva&telefone=51999998888

    **Erros possíveis:**
    - 404: Cliente não encontrado
    - 400: Nome inválido ou telefone com formato incorreto
    """

    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    if nome is not None:
        cliente.nome = validar_nome(nome)

    if telefone is not None:
        telefone_limpo = ''.join(filter(str.isdigit, telefone))
        if telefone_limpo and len(telefone_limpo) not in (10, 11):
            raise HTTPException(
                status_code=400,
                detail="Telefone inválido. Use 10 dígitos (fixo) ou 11 dígitos (celular)"
            )
        cliente.telefone = telefone_limpo or None

    db.commit()
    db.refresh(cliente)

    return {
        "sucesso": True,
        "mensagem": f"{cliente.nome} foi atualizado(a) com sucesso",
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "telefone": cliente.telefone,
            "data_cadastro": cliente.data_cadastro
        }
    }

@router.delete(
    "/{cpf}",
    summary="Excluir cliente (restritivo)",
    dependencies=[Depends(require_role(["admin"]))],
)
def excluir_cliente(cpf: str, db: Session = Depends(get_db)):
    """
    Exclui um cliente do sistema com validações restritivas.
    
    **ATENÇÃO - Validações Aplicadas:**
    -  Bloqueia se cliente possui sacolas ativas
    -  Bloqueia se cliente possui sacolas devolvidas (preservar histórico)
    -  Bloqueia se cliente possui alertas registrados
    -  Só permite exclusão de clientes "limpos" (nunca usaram o sistema)
    
    **Objetivo:** Proteger dados históricos e rastreabilidade
    
    **Quando usar:** Cadastro duplicado ou erro de digitação no cadastro inicial
    
    **Não usar para:** Clientes que já utilizaram o sistema (use suspensão)

    **Parâmetro:**
    - cpf: CPF do cliente (11 dígitos)
    
    **Retorna:**
    - sucesso: true
    - mensagem: Confirmação da exclusão
    
    **Erros possíveis:**
    - 404: Cliente não encontrado
    - 400: Cliente possui sacolas ativas/devolvidas ou alertas
    """
    
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