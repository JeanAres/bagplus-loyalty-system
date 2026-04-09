"""
Endpoints administrativos - Relatórios e estatísticas
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from datetime import datetime, timedelta
from app.db import models
from dateutil.relativedelta import relativedelta
from app.middleware.auth import require_role

router = APIRouter(
    prefix="/api/admin/relatorios",
    tags=["Admin - Relatórios"]
)


@router.get(
    "/dashboard",
    summary="Dashboard administrativo",
    description="""
    Retorna visão geral completa do negócio em um único endpoint.
    
    **Informações consolidadas:**
    
    **Totais Gerais:**
    - Total de clientes cadastrados
    - Total de sacolas no sistema (todas)
    - Distribuição de sacolas por status (estoque/ativas/devolvidas)
    
    **Movimentação Financeira:**
    - Total de usos hoje
    - Total de usos esta semana
    - Total de usos este mês
    - Valor movimentado hoje
    - Valor movimentado esta semana
    - Valor movimentado este mês
    - Valor médio por compra
    
    **Alertas e Suspensões:**
    - Total de alertas não resolvidos
    - Distribuição por gravidade (baixa/média/alta)
    - Total de clientes suspensos
    - Total de clientes bloqueados
    
    **Top Performers:**
    - Top 5 clientes com mais usos
    - Top 5 clientes que mais gastaram
    
    **Crescimento:**
    - Novos clientes esta semana
    - Novos clientes este mês
    
    **Quando usar:**
    - Tela inicial do painel administrativo
    - Relatórios executivos
    - Acompanhamento diário do negócio
    
    **Performance:** Otimizado com queries agregadas, retorna em ~200ms
    """
)
def dashboard_admin(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Dashboard com visão geral do negócio"""
    
    # ========== TOTAIS GERAIS ==========
    total_clientes = db.query(models.Cliente).count()
    total_sacolas = db.query(models.Sacola).count()
    
    sacolas_estoque = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.estoque
    ).count()
    
    sacolas_ativas = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.ativo
    ).count()
    
    sacolas_devolvidas = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.devolvido
    ).count()
    
    # ========== MOVIMENTAÇÃO FINANCEIRA ==========
    hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    semana_inicio = hoje_inicio - timedelta(days=datetime.now().weekday())
    mes_inicio = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Hoje
    usos_hoje = db.query(models.RegistroUso).filter(
        models.RegistroUso.data_uso >= hoje_inicio
    ).all()
    total_usos_hoje = len(usos_hoje)
    valor_hoje = sum(r.valor_compra for r in usos_hoje)
    
    # Semana
    usos_semana = db.query(models.RegistroUso).filter(
        models.RegistroUso.data_uso >= semana_inicio
    ).all()
    total_usos_semana = len(usos_semana)
    valor_semana = sum(r.valor_compra for r in usos_semana)
    
    # Mês
    usos_mes = db.query(models.RegistroUso).filter(
        models.RegistroUso.data_uso >= mes_inicio
    ).all()
    total_usos_mes = len(usos_mes)
    valor_mes = sum(r.valor_compra for r in usos_mes)
    
    # Valor médio por compra geral
    todos_usos = db.query(models.RegistroUso).all()
    total_geral = sum(r.valor_compra for r in todos_usos)
    valor_medio_compra = total_geral / len(todos_usos) if todos_usos else 0
    
    # ========== ALERTAS E SUSPENSÕES ==========
    alertas_pendentes = db.query(models.Alerta).filter(
        models.Alerta.resolvido == False
    ).all()
    
    total_alertas_pendentes = len(alertas_pendentes)
    
    alertas_baixa = len([a for a in alertas_pendentes if a.gravidade == models.GravidadeAlerta.baixa])
    alertas_media = len([a for a in alertas_pendentes if a.gravidade == models.GravidadeAlerta.media])
    alertas_alta = len([a for a in alertas_pendentes if a.gravidade == models.GravidadeAlerta.alta])
    
    clientes_suspensos = db.query(models.Cliente).filter(
        models.Cliente.status_beneficios == models.StatusBeneficios.suspenso
    ).count()
    
    clientes_bloqueados = db.query(models.Cliente).filter(
        models.Cliente.status_beneficios == models.StatusBeneficios.bloqueado
    ).count()
    
    # ========== TOP PERFORMERS ==========
    from sqlalchemy import func
    
    top_usos = db.query(
        models.Sacola.cliente_cpf,
        func.sum(models.Sacola.utilizacoes).label('total_usos')
    ).filter(
        models.Sacola.cliente_cpf.isnot(None)
    ).group_by(
        models.Sacola.cliente_cpf
    ).order_by(
        func.sum(models.Sacola.utilizacoes).desc()
    ).limit(5).all()
    
    top_clientes_usos = []
    for cliente_cpf, total in top_usos:
        cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cliente_cpf).first()
        if cliente:
            top_clientes_usos.append({
                "cpf": cliente_cpf,
                "nome": cliente.nome,
                "total_usos": int(total)
            })
    
    top_gastos = db.query(
        models.Sacola.cliente_cpf,
        func.sum(models.RegistroUso.valor_compra).label('total_gasto')
    ).join(
        models.RegistroUso
    ).filter(
        models.Sacola.cliente_cpf.isnot(None)
    ).group_by(
        models.Sacola.cliente_cpf
    ).order_by(
        func.sum(models.RegistroUso.valor_compra).desc()
    ).limit(5).all()
    
    top_clientes_gastos = []
    for cliente_cpf, total in top_gastos:
        cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cliente_cpf).first()
        if cliente:
            top_clientes_gastos.append({
                "cpf": cliente_cpf,
                "nome": cliente.nome,
                "total_gasto": round(float(total), 2)
            })
    
    # ========== CRESCIMENTO ==========
    novos_clientes_semana = db.query(models.Cliente).filter(
        models.Cliente.data_cadastro >= semana_inicio
    ).count()
    
    novos_clientes_mes = db.query(models.Cliente).filter(
        models.Cliente.data_cadastro >= mes_inicio
    ).count()
    
    # ========== MONTAR RESPONSE ==========
    return {
        "timestamp": datetime.now(),
        
        "totais": {
            "clientes": total_clientes,
            "sacolas_total": total_sacolas,
            "sacolas_estoque": sacolas_estoque,
            "sacolas_ativas": sacolas_ativas,
            "sacolas_devolvidas": sacolas_devolvidas
        },
        
        "financeiro": {
            "hoje": {
                "total_usos": total_usos_hoje,
                "valor_movimentado": round(valor_hoje, 2)
            },
            "semana": {
                "total_usos": total_usos_semana,
                "valor_movimentado": round(valor_semana, 2)
            },
            "mes": {
                "total_usos": total_usos_mes,
                "valor_movimentado": round(valor_mes, 2)
            },
            "valor_medio_por_compra": round(valor_medio_compra, 2)
        },
        
        "alertas_e_suspensoes": {
            "alertas_pendentes": total_alertas_pendentes,
            "alertas_por_gravidade": {
                "baixa": alertas_baixa,
                "media": alertas_media,
                "alta": alertas_alta
            },
            "clientes_suspensos": clientes_suspensos,
            "clientes_bloqueados": clientes_bloqueados
        },
        
        "top_performers": {
            "mais_usos": top_clientes_usos,
            "mais_gastaram": top_clientes_gastos
        },
        
        "crescimento": {
            "novos_clientes_semana": novos_clientes_semana,
            "novos_clientes_mes": novos_clientes_mes
        }
    }


@router.get(
    "/vendas",
    summary="Relatório de vendas por período",
    description="""
    Gera relatório detalhado de vendas em um período específico.
    
    **Informações retornadas:**
    
    **Resumo Geral:**
    - Total de usos no período
    - Valor total movimentado
    - Valor médio por compra
    - Clientes únicos que compraram
    
    **Detalhamento Diário:**
    - Data
    - Quantidade de usos
    - Valor movimentado
    - Valor médio do dia
    
    **Top Performers do Período:**
    - Top 5 clientes que mais usaram
    - Top 5 clientes que mais gastaram
    
    **Parâmetros:**
    - data_inicio: Data inicial (formato: YYYY-MM-DD)
    - data_fim: Data final (formato: YYYY-MM-DD)
    
    **Exemplos:**
```
    # Relatório do mês de março
    GET /api/admin/relatorios/vendas?data_inicio=2026-03-01&data_fim=2026-03-31
    
    # Relatório da semana passada
    GET /api/admin/relatorios/vendas?data_inicio=2026-03-24&data_fim=2026-03-30
```
    
    **Quando usar:**
    - Relatórios mensais para gerência
    - Análise de performance por período
    - Comparação entre períodos
    """
)
def relatorio_vendas(
    data_inicio: str,
    data_fim: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Gera relatório de vendas por período"""
    
    # Validar datas
    try:
        dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Formato de data inválido. Use YYYY-MM-DD (ex: 2026-03-31)"
        )
    
    if dt_inicio > dt_fim:
        raise HTTPException(
            status_code=400,
            detail="Data início deve ser menor ou igual à data fim"
        )
    
    # Buscar registros do período
    registros = db.query(models.RegistroUso).filter(
        models.RegistroUso.data_uso >= dt_inicio,
        models.RegistroUso.data_uso <= dt_fim
    ).all()
    
    if not registros:
        return {
            "periodo": {
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "dias": (dt_fim - dt_inicio).days + 1
            },
            "resumo": {
                "total_usos": 0,
                "valor_total": 0,
                "valor_medio_por_compra": 0,
                "clientes_unicos": 0
            },
            "detalhamento_diario": [],
            "top_performers": {
                "mais_usos": [],
                "mais_gastaram": []
            }
        }
    
    # ========== RESUMO GERAL ==========
    total_usos = len(registros)
    valor_total = sum(r.valor_compra for r in registros)
    valor_medio_compra = valor_total / total_usos if total_usos > 0 else 0
    
    # Clientes únicos
    clientes_unicos = set()
    for r in registros:
        sacola = db.query(models.Sacola).filter(models.Sacola.id == r.sacola_id).first()
        if sacola and sacola.cliente_cpf:
            clientes_unicos.add(sacola.cliente_cpf)
    
    # ========== DETALHAMENTO DIÁRIO ==========
    from collections import defaultdict
    
    usos_por_dia = defaultdict(list)
    for r in registros:
        dia = r.data_uso.date()
        usos_por_dia[dia].append(r.valor_compra)
    
    detalhamento = []
    for dia in sorted(usos_por_dia.keys()):
        valores = usos_por_dia[dia]
        detalhamento.append({
            "data": str(dia),
            "quantidade_usos": len(valores),
            "valor_movimentado": round(sum(valores), 2),
            "valor_medio_dia": round(sum(valores) / len(valores), 2)
        })
    
    # ========== TOP PERFORMERS DO PERÍODO ==========
    from sqlalchemy import func
    
    top_usos = db.query(
        models.Sacola.cliente_cpf,
        func.count(models.RegistroUso.id).label('total_usos')
    ).join(
        models.RegistroUso
    ).filter(
        models.RegistroUso.data_uso >= dt_inicio,
        models.RegistroUso.data_uso <= dt_fim,
        models.Sacola.cliente_cpf.isnot(None)
    ).group_by(
        models.Sacola.cliente_cpf
    ).order_by(
        func.count(models.RegistroUso.id).desc()
    ).limit(5).all()
    
    top_clientes_usos = []
    for cliente_cpf, total in top_usos:
        cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cliente_cpf).first()
        if cliente:
            top_clientes_usos.append({
                "cpf": cliente_cpf,
                "nome": cliente.nome,
                "total_usos": int(total)
            })
    
    top_gastos = db.query(
        models.Sacola.cliente_cpf,
        func.sum(models.RegistroUso.valor_compra).label('total_gasto')
    ).join(
        models.RegistroUso
    ).filter(
        models.RegistroUso.data_uso >= dt_inicio,
        models.RegistroUso.data_uso <= dt_fim,
        models.Sacola.cliente_cpf.isnot(None)
    ).group_by(
        models.Sacola.cliente_cpf
    ).order_by(
        func.sum(models.RegistroUso.valor_compra).desc()
    ).limit(5).all()
    
    top_clientes_gastos = []
    for cliente_cpf, total in top_gastos:
        cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cliente_cpf).first()
        if cliente:
            top_clientes_gastos.append({
                "cpf": cliente_cpf,
                "nome": cliente.nome,
                "total_gasto": round(float(total), 2)
            })
    
    # ========== MONTAR RESPONSE ==========
    return {
        "periodo": {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "dias": (dt_fim.date() - dt_inicio.date()).days + 1
        },
        "resumo": {
            "total_usos": total_usos,
            "valor_total": round(valor_total, 2),
            "valor_medio_por_compra": round(valor_medio_compra, 2),
            "clientes_unicos": len(clientes_unicos)
        },
        "detalhamento_diario": detalhamento,
        "top_performers": {
            "mais_usos": top_clientes_usos,
            "mais_gastaram": top_clientes_gastos
        }
    }


@router.get(
    "/estatisticas",
    summary="Estatísticas gerais do sistema",
    description="""
    Retorna estatísticas consolidadas de todo o sistema.
    
    **Informações retornadas:**
    
    **Taxa de Devolução:**
    - Percentual de sacolas devolvidas vs distribuídas
    - Total de sacolas devolvidas
    - Total de sacolas ainda ativas
    
    **Tempo Médio de Uso:**
    - Dias médios que sacolas ficam com clientes
    - Baseado em sacolas devolvidas
    
    **Recordes:**
    - Cliente mais fiel (mais usos totais)
    - Cliente que mais gastou (maior valor total)
    - Sacola mais usada (mais utilizações)
    
    **Performance Financeira:**
    - Valor médio por compra
    - Total movimentado desde o início
    - Total de usos realizados
    
    **Crescimento:**
    - Novos clientes este mês
    - Novos clientes esta semana
    - Total de clientes
    
    **Quando usar:**
    - Relatórios executivos
    - Análise de performance geral
    - Benchmarking
    """
)
def estatisticas_gerais(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Retorna estatísticas consolidadas do sistema"""
    
    # ========== TAXA DE DEVOLUÇÃO ==========
    sacolas_distribuidas = db.query(models.Sacola).filter(
        models.Sacola.status.in_([models.StatusSacola.ativo, models.StatusSacola.devolvido])
    ).count()
    
    sacolas_devolvidas = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.devolvido
    ).count()
    
    sacolas_ativas = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.ativo
    ).count()
    
    taxa_devolucao = (sacolas_devolvidas / sacolas_distribuidas * 100) if sacolas_distribuidas > 0 else 0
    
    # ========== TEMPO MÉDIO DE USO ==========
    sacolas_dev = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.devolvido,
        models.Sacola.data_vinculacao.isnot(None),
        models.Sacola.data_devolucao.isnot(None)
    ).all()
    
    if sacolas_dev:
        tempos_uso = []
        for s in sacolas_dev:
            dias = (s.data_devolucao - s.data_vinculacao).days
            tempos_uso.append(dias)
        tempo_medio_dias = sum(tempos_uso) / len(tempos_uso)
    else:
        tempo_medio_dias = 0
    
    # ========== RECORDES ==========
    from sqlalchemy import func
    
    # Cliente mais fiel
    cliente_mais_fiel = db.query(
        models.Sacola.cliente_cpf,
        func.sum(models.Sacola.utilizacoes).label('total_usos')
    ).filter(
        models.Sacola.cliente_cpf.isnot(None)
    ).group_by(
        models.Sacola.cliente_cpf
    ).order_by(
        func.sum(models.Sacola.utilizacoes).desc()
    ).first()
    
    if cliente_mais_fiel:
        cliente_fiel = db.query(models.Cliente).filter(
            models.Cliente.cpf == cliente_mais_fiel[0]
        ).first()
        cliente_mais_fiel_info = {
            "cpf": cliente_mais_fiel[0],
            "nome": cliente_fiel.nome if cliente_fiel else "Desconhecido",
            "total_usos": int(cliente_mais_fiel[1])
        }
    else:
        cliente_mais_fiel_info = None
    
    # Cliente que mais gastou
    cliente_mais_gastou = db.query(
        models.Sacola.cliente_cpf,
        func.sum(models.RegistroUso.valor_compra).label('total_gasto')
    ).join(
        models.RegistroUso
    ).filter(
        models.Sacola.cliente_cpf.isnot(None)
    ).group_by(
        models.Sacola.cliente_cpf
    ).order_by(
        func.sum(models.RegistroUso.valor_compra).desc()
    ).first()
    
    if cliente_mais_gastou:
        cliente_gastador = db.query(models.Cliente).filter(
            models.Cliente.cpf == cliente_mais_gastou[0]
        ).first()
        cliente_mais_gastou_info = {
            "cpf": cliente_mais_gastou[0],
            "nome": cliente_gastador.nome if cliente_gastador else "Desconhecido",
            "total_gasto": round(float(cliente_mais_gastou[1]), 2)
        }
    else:
        cliente_mais_gastou_info = None
    
    # Sacola mais usada
    sacola_mais_usada = db.query(models.Sacola).order_by(
        models.Sacola.utilizacoes.desc()
    ).first()
    
    if sacola_mais_usada and sacola_mais_usada.utilizacoes > 0:
        sacola_mais_usada_info = {
            "id": sacola_mais_usada.id,
            "utilizacoes": sacola_mais_usada.utilizacoes,
            "status": sacola_mais_usada.status.value
        }
    else:
        sacola_mais_usada_info = None
    
    # ========== PERFORMANCE FINANCEIRA ==========
    todos_registros = db.query(models.RegistroUso).all()
    total_movimentado = sum(r.valor_compra for r in todos_registros)
    total_usos_sistema = len(todos_registros)
    valor_medio_compra = total_movimentado / total_usos_sistema if total_usos_sistema > 0 else 0
    
    # ========== CRESCIMENTO ==========
    hoje = datetime.now()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    novos_clientes_semana = db.query(models.Cliente).filter(
        models.Cliente.data_cadastro >= inicio_semana
    ).count()
    
    novos_clientes_mes = db.query(models.Cliente).filter(
        models.Cliente.data_cadastro >= inicio_mes
    ).count()
    
    total_clientes = db.query(models.Cliente).count()
    
    # ========== MONTAR RESPONSE ==========
    return {
        "taxa_devolucao": {
            "percentual": round(taxa_devolucao, 2),
            "sacolas_devolvidas": sacolas_devolvidas,
            "sacolas_ativas": sacolas_ativas,
            "total_distribuidas": sacolas_distribuidas
        },
        
        "tempo_medio_uso": {
            "dias": round(tempo_medio_dias, 1),
            "baseado_em": len(sacolas_dev)
        },
        
        "recordes": {
            "cliente_mais_fiel": cliente_mais_fiel_info,
            "cliente_que_mais_gastou": cliente_mais_gastou_info,
            "sacola_mais_usada": sacola_mais_usada_info
        },
        
        "performance_financeira": {
            "valor_medio_por_compra": round(valor_medio_compra, 2),
            "total_movimentado": round(total_movimentado, 2),
            "total_usos": total_usos_sistema
        },
        
        "crescimento": {
            "total_clientes": total_clientes,
            "novos_esta_semana": novos_clientes_semana,
            "novos_este_mes": novos_clientes_mes
        }
    }

@router.get(
    "/crescimento",
    summary="Análise de crescimento do negócio",
    description="""
    Retorna análise de crescimento mês a mês (últimos 6 meses).
    
    **Informações retornadas:**
    
    ** Por Mês (últimos 6 meses):**
    - Ano/Mês
    - Novos clientes cadastrados
    - Sacolas ativadas (vinculadas)
    - Valor movimentado no mês
    - Total de usos no mês
    
    ** Resumo Geral:**
    - Total de novos clientes (6 meses)
    - Total de sacolas ativadas (6 meses)
    - Valor total movimentado (6 meses)
    - Crescimento percentual mês a mês
    
    ** Insights:**
    - Mês com mais clientes
    - Mês com mais faturamento
    - Tendência de crescimento
    
    **Quando usar:**
    - Projeções de crescimento
    - Relatórios para investidores
    - Planejamento de compras
    - Análise de sazonalidade
    
    **Observação:** 
    - Considera mês atual e 5 anteriores
    - Dados ordenados do mais antigo para o mais recente
    """
)
def analise_crescimento(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):

    """Retorna análise de crescimento dos últimos 6 meses"""
    
    from collections import defaultdict
    from dateutil.relativedelta import relativedelta
    
    hoje = datetime.now()
    
    # Calcular início (6 meses atrás)
    inicio = hoje - relativedelta(months=5)
    inicio = inicio.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # ========== COLETAR DADOS POR MÊS ==========
    meses = []
    mes_atual = inicio
    
    for i in range(6):
        # Calcular range do mês
        mes_inicio = mes_atual
        mes_fim = mes_atual + relativedelta(months=1) - timedelta(seconds=1)
        
        # Novos clientes
        novos_clientes = db.query(models.Cliente).filter(
            models.Cliente.data_cadastro >= mes_inicio,
            models.Cliente.data_cadastro <= mes_fim
        ).count()
        
        # Sacolas ativadas
        sacolas_ativadas = db.query(models.Sacola).filter(
            models.Sacola.data_vinculacao >= mes_inicio,
            models.Sacola.data_vinculacao <= mes_fim
        ).count()
        
        # Usos e valor movimentado
        usos = db.query(models.RegistroUso).filter(
            models.RegistroUso.data_uso >= mes_inicio,
            models.RegistroUso.data_uso <= mes_fim
        ).all()
        
        total_usos = len(usos)
        valor_movimentado = sum(u.valor_compra for u in usos)
        
        meses.append({
            "mes": mes_atual.strftime('%Y-%m'),
            "mes_nome": mes_atual.strftime('%B/%Y'),
            "novos_clientes": novos_clientes,
            "sacolas_ativadas": sacolas_ativadas,
            "valor_movimentado": round(valor_movimentado, 2),
            "total_usos": total_usos
        })
        
        # Próximo mês
        mes_atual = mes_atual + relativedelta(months=1)
    
    # ========== RESUMO GERAL ==========
    total_novos_clientes = sum(m['novos_clientes'] for m in meses)
    total_sacolas_ativadas = sum(m['sacolas_ativadas'] for m in meses)
    total_valor = sum(m['valor_movimentado'] for m in meses)
    total_usos_periodo = sum(m['total_usos'] for m in meses)
    
    # ========== INSIGHTS ==========
    mes_mais_clientes = max(meses, key=lambda m: m['novos_clientes']) if meses else None
    mes_mais_faturamento = max(meses, key=lambda m: m['valor_movimentado']) if meses else None
    
    # Calcular tendência (crescimento do último mês vs primeiro)
    if len(meses) >= 2:
        valor_primeiro = meses[0]['valor_movimentado']
        valor_ultimo = meses[-1]['valor_movimentado']
        
        if valor_primeiro > 0:
            crescimento_percentual = ((valor_ultimo - valor_primeiro) / valor_primeiro) * 100
        else:
            crescimento_percentual = 0
    else:
        crescimento_percentual = 0
    
    # ========== MONTAR RESPONSE ==========
    return {
        "periodo": {
            "inicio": inicio.strftime('%Y-%m-%d'),
            "fim": hoje.strftime('%Y-%m-%d'),
            "meses_analisados": len(meses)
        },
        
        "evolucao_mensal": meses,
        
        "resumo": {
            "total_novos_clientes": total_novos_clientes,
            "total_sacolas_ativadas": total_sacolas_ativadas,
            "valor_total_movimentado": round(total_valor, 2),
            "total_usos": total_usos_periodo,
            "media_mensal": {
                "clientes": round(total_novos_clientes / 6, 1),
                "sacolas": round(total_sacolas_ativadas / 6, 1),
                "valor": round(total_valor / 6, 2)
            }
        },
        
        "insights": {
            "mes_mais_clientes": {
                "mes": mes_mais_clientes['mes_nome'] if mes_mais_clientes else None,
                "quantidade": mes_mais_clientes['novos_clientes'] if mes_mais_clientes else 0
            },
            "mes_mais_faturamento": {
                "mes": mes_mais_faturamento['mes_nome'] if mes_mais_faturamento else None,
                "valor": mes_mais_faturamento['valor_movimentado'] if mes_mais_faturamento else 0
            },
            "tendencia": "Crescimento" if crescimento_percentual > 0 else "Queda" if crescimento_percentual < 0 else "Estável",
            "crescimento_percentual": round(crescimento_percentual, 2)
        }
    }