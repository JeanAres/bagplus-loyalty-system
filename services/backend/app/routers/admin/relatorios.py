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
from sqlalchemy import func
from collections import defaultdict

router = APIRouter(
    prefix="/api/admin/relatorios",
    tags=["Admin - Relatórios"]
)


# ============================================
# HELPER: Filtro base por unidade
# ============================================

def filtro_unidade(query, model_field, current_user):
    """
    Aplica filtro de unidade quando o usuário é gerente.
    Admin não recebe filtro.
    """
    if current_user.role == models.UserRole.gerente:
        return query.filter(model_field == current_user.unidade_id)
    return query


# ============================================
# ENDPOINTS
# ============================================

@router.get(
    "/dashboard",
    summary="Dashboard administrativo",
)
def dashboard_admin(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Retorna visão geral completa do negócio em um único endpoint.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: dados globais de todo o sistema
    - Gerente: dados filtrados pela sua unidade

    **Informações consolidadas:**
    - Totais gerais (clientes, sacolas por status)
    - Movimentação financeira (hoje, semana, mês)
    - Alertas e suspensões
    - Top performers
    - Crescimento de clientes
    """

    eh_gerente = current_user.role == models.UserRole.gerente

    # ========== TOTAIS GERAIS ==========
    # Clientes e sacolas são globais — gerente vê tudo
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

    def query_usos(data_inicio):
        """Busca usos a partir de uma data, filtrado por unidade se gerente."""
        q = db.query(models.RegistroUso).filter(
            models.RegistroUso.data_uso >= data_inicio
        )
        if eh_gerente:
            q = q.join(models.Sacola).join(
                models.UsoSacola,
                models.UsoSacola.sacola_id == models.Sacola.id
            ).filter(
                models.UsoSacola.unidade_id == current_user.unidade_id
            )
        return q.all()

    usos_hoje = query_usos(hoje_inicio)
    usos_semana = query_usos(semana_inicio)
    usos_mes = query_usos(mes_inicio)

    todos_usos = db.query(models.RegistroUso).all() if not eh_gerente else usos_mes

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
    top_usos_query = db.query(
        models.Sacola.cliente_cpf,
        func.sum(models.Sacola.utilizacoes).label('total_usos')
    ).filter(models.Sacola.cliente_cpf.isnot(None))

    if eh_gerente:
        top_usos_query = top_usos_query.join(
            models.UsoSacola,
            models.UsoSacola.sacola_id == models.Sacola.id
        ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

    top_usos = top_usos_query.group_by(
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

    top_gastos_query = db.query(
        models.Sacola.cliente_cpf,
        func.sum(models.RegistroUso.valor_compra).label('total_gasto')
    ).join(models.RegistroUso).filter(models.Sacola.cliente_cpf.isnot(None))

    if eh_gerente:
        top_gastos_query = top_gastos_query.join(
            models.UsoSacola,
            models.UsoSacola.sacola_id == models.Sacola.id
        ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

    top_gastos = top_gastos_query.group_by(
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

    return {
        "timestamp": datetime.now(),
        "contexto": {
            "role": current_user.role.value,
            "unidade_id": current_user.unidade_id if eh_gerente else None
        },
        "totais": {
            "clientes": total_clientes,
            "sacolas_total": total_sacolas,
            "sacolas_estoque": sacolas_estoque,
            "sacolas_ativas": sacolas_ativas,
            "sacolas_devolvidas": sacolas_devolvidas
        },
        "financeiro": {
            "hoje": {
                "total_usos": len(usos_hoje),
                "valor_movimentado": round(sum(r.valor_compra for r in usos_hoje), 2)
            },
            "semana": {
                "total_usos": len(usos_semana),
                "valor_movimentado": round(sum(r.valor_compra for r in usos_semana), 2)
            },
            "mes": {
                "total_usos": len(usos_mes),
                "valor_movimentado": round(sum(r.valor_compra for r in usos_mes), 2)
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
)
def relatorio_vendas(
    data_inicio: str,
    data_fim: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Gera relatório detalhado de vendas em um período específico.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: dados globais
    - Gerente: filtrado pela sua unidade

    **Parâmetros:**
    - data_inicio: Data inicial (formato: YYYY-MM-DD)
    - data_fim: Data final (formato: YYYY-MM-DD)
    """

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

    eh_gerente = current_user.role == models.UserRole.gerente

    query = db.query(models.RegistroUso).filter(
        models.RegistroUso.data_uso >= dt_inicio,
        models.RegistroUso.data_uso <= dt_fim
    )

    if eh_gerente:
        query = query.join(models.Sacola).join(
            models.UsoSacola,
            models.UsoSacola.sacola_id == models.Sacola.id
        ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

    registros = query.all()

    if not registros:
        return {
            "periodo": {
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "dias": (dt_fim - dt_inicio).days + 1
            },
            "contexto": {
                "role": current_user.role.value,
                "unidade_id": current_user.unidade_id if eh_gerente else None
            },
            "resumo": {
                "total_usos": 0,
                "valor_total": 0,
                "valor_medio_por_compra": 0,
                "clientes_unicos": 0
            },
            "detalhamento_diario": [],
            "top_performers": {"mais_usos": [], "mais_gastaram": []}
        }

    total_usos = len(registros)
    valor_total = sum(r.valor_compra for r in registros)
    valor_medio_compra = valor_total / total_usos if total_usos > 0 else 0

    clientes_unicos = set()
    for r in registros:
        sacola = db.query(models.Sacola).filter(models.Sacola.id == r.sacola_id).first()
        if sacola and sacola.cliente_cpf:
            clientes_unicos.add(sacola.cliente_cpf)

    usos_por_dia = defaultdict(list)
    for r in registros:
        usos_por_dia[r.data_uso.date()].append(r.valor_compra)

    detalhamento = []
    for dia in sorted(usos_por_dia.keys()):
        valores = usos_por_dia[dia]
        detalhamento.append({
            "data": str(dia),
            "quantidade_usos": len(valores),
            "valor_movimentado": round(sum(valores), 2),
            "valor_medio_dia": round(sum(valores) / len(valores), 2)
        })

    top_usos_query = db.query(
        models.Sacola.cliente_cpf,
        func.count(models.RegistroUso.id).label('total_usos')
    ).join(models.RegistroUso).filter(
        models.RegistroUso.data_uso >= dt_inicio,
        models.RegistroUso.data_uso <= dt_fim,
        models.Sacola.cliente_cpf.isnot(None)
    )

    if eh_gerente:
        top_usos_query = top_usos_query.join(
            models.UsoSacola,
            models.UsoSacola.sacola_id == models.Sacola.id
        ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

    top_usos = top_usos_query.group_by(
        models.Sacola.cliente_cpf
    ).order_by(func.count(models.RegistroUso.id).desc()).limit(5).all()

    top_clientes_usos = []
    for cliente_cpf, total in top_usos:
        cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cliente_cpf).first()
        if cliente:
            top_clientes_usos.append({
                "cpf": cliente_cpf,
                "nome": cliente.nome,
                "total_usos": int(total)
            })

    top_gastos_query = db.query(
        models.Sacola.cliente_cpf,
        func.sum(models.RegistroUso.valor_compra).label('total_gasto')
    ).join(models.RegistroUso).filter(
        models.RegistroUso.data_uso >= dt_inicio,
        models.RegistroUso.data_uso <= dt_fim,
        models.Sacola.cliente_cpf.isnot(None)
    )

    if eh_gerente:
        top_gastos_query = top_gastos_query.join(
            models.UsoSacola,
            models.UsoSacola.sacola_id == models.Sacola.id
        ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

    top_gastos = top_gastos_query.group_by(
        models.Sacola.cliente_cpf
    ).order_by(func.sum(models.RegistroUso.valor_compra).desc()).limit(5).all()

    top_clientes_gastos = []
    for cliente_cpf, total in top_gastos:
        cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cliente_cpf).first()
        if cliente:
            top_clientes_gastos.append({
                "cpf": cliente_cpf,
                "nome": cliente.nome,
                "total_gasto": round(float(total), 2)
            })

    return {
        "periodo": {
            "data_inicio": data_inicio,
            "data_fim": data_fim,
            "dias": (dt_fim.date() - dt_inicio.date()).days + 1
        },
        "contexto": {
            "role": current_user.role.value,
            "unidade_id": current_user.unidade_id if eh_gerente else None
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
)
def estatisticas_gerais(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Retorna estatísticas consolidadas do sistema.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: dados globais
    - Gerente: filtrado pela sua unidade
    """

    eh_gerente = current_user.role == models.UserRole.gerente

    # ========== TAXA DE DEVOLUÇÃO ==========
    sacolas_distribuidas = db.query(models.Sacola).filter(
        models.Sacola.status.in_([models.StatusSacola.ativo, models.StatusSacola.devolvido])
    ).count()

    sacolas_devolvidas_count = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.devolvido
    ).count()

    sacolas_ativas_count = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.ativo
    ).count()

    taxa_devolucao = (sacolas_devolvidas_count / sacolas_distribuidas * 100) if sacolas_distribuidas > 0 else 0

    # ========== TEMPO MÉDIO DE USO ==========
    sacolas_dev = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.devolvido,
        models.Sacola.data_vinculacao.isnot(None),
        models.Sacola.data_devolucao.isnot(None)
    ).all()

    tempo_medio_dias = 0
    if sacolas_dev:
        tempos = [(s.data_devolucao - s.data_vinculacao).days for s in sacolas_dev]
        tempo_medio_dias = sum(tempos) / len(tempos)

    # ========== RECORDES ==========
    usos_query = db.query(
        models.Sacola.cliente_cpf,
        func.sum(models.Sacola.utilizacoes).label('total_usos')
    ).filter(models.Sacola.cliente_cpf.isnot(None))

    if eh_gerente:
        usos_query = usos_query.join(
            models.UsoSacola,
            models.UsoSacola.sacola_id == models.Sacola.id
        ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

    cliente_mais_fiel = usos_query.group_by(
        models.Sacola.cliente_cpf
    ).order_by(func.sum(models.Sacola.utilizacoes).desc()).first()

    cliente_mais_fiel_info = None
    if cliente_mais_fiel:
        c = db.query(models.Cliente).filter(models.Cliente.cpf == cliente_mais_fiel[0]).first()
        cliente_mais_fiel_info = {
            "cpf": cliente_mais_fiel[0],
            "nome": c.nome if c else "Desconhecido",
            "total_usos": int(cliente_mais_fiel[1])
        }

    gastos_query = db.query(
        models.Sacola.cliente_cpf,
        func.sum(models.RegistroUso.valor_compra).label('total_gasto')
    ).join(models.RegistroUso).filter(models.Sacola.cliente_cpf.isnot(None))

    if eh_gerente:
        gastos_query = gastos_query.join(
            models.UsoSacola,
            models.UsoSacola.sacola_id == models.Sacola.id
        ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

    cliente_mais_gastou = gastos_query.group_by(
        models.Sacola.cliente_cpf
    ).order_by(func.sum(models.RegistroUso.valor_compra).desc()).first()

    cliente_mais_gastou_info = None
    if cliente_mais_gastou:
        c = db.query(models.Cliente).filter(models.Cliente.cpf == cliente_mais_gastou[0]).first()
        cliente_mais_gastou_info = {
            "cpf": cliente_mais_gastou[0],
            "nome": c.nome if c else "Desconhecido",
            "total_gasto": round(float(cliente_mais_gastou[1]), 2)
        }

    sacola_mais_usada = db.query(models.Sacola).order_by(
        models.Sacola.utilizacoes.desc()
    ).first()

    sacola_mais_usada_info = None
    if sacola_mais_usada and sacola_mais_usada.utilizacoes > 0:
        sacola_mais_usada_info = {
            "id": sacola_mais_usada.id,
            "utilizacoes": sacola_mais_usada.utilizacoes,
            "status": sacola_mais_usada.status.value
        }

    # ========== PERFORMANCE FINANCEIRA ==========
    registros_query = db.query(models.RegistroUso)
    if eh_gerente:
        registros_query = registros_query.join(models.Sacola).join(
            models.UsoSacola,
            models.UsoSacola.sacola_id == models.Sacola.id
        ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

    todos_registros = registros_query.all()
    total_movimentado = sum(r.valor_compra for r in todos_registros)
    total_usos_sistema = len(todos_registros)
    valor_medio_compra = total_movimentado / total_usos_sistema if total_usos_sistema > 0 else 0

    # ========== CRESCIMENTO ==========
    hoje = datetime.now()
    inicio_semana = (hoje - timedelta(days=hoje.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    novos_clientes_semana = db.query(models.Cliente).filter(
        models.Cliente.data_cadastro >= inicio_semana
    ).count()

    novos_clientes_mes = db.query(models.Cliente).filter(
        models.Cliente.data_cadastro >= inicio_mes
    ).count()

    return {
        "contexto": {
            "role": current_user.role.value,
            "unidade_id": current_user.unidade_id if eh_gerente else None
        },
        "taxa_devolucao": {
            "percentual": round(taxa_devolucao, 2),
            "sacolas_devolvidas": sacolas_devolvidas_count,
            "sacolas_ativas": sacolas_ativas_count,
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
            "total_clientes": db.query(models.Cliente).count(),
            "novos_esta_semana": novos_clientes_semana,
            "novos_este_mes": novos_clientes_mes
        }
    }


@router.get(
    "/crescimento",
    summary="Análise de crescimento do negócio",
)
def analise_crescimento(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Retorna análise de crescimento mês a mês (últimos 6 meses).

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: dados globais
    - Gerente: filtrado pela sua unidade
    """

    eh_gerente = current_user.role == models.UserRole.gerente
    hoje = datetime.now()
    inicio = (hoje - relativedelta(months=5)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    meses = []
    mes_atual = inicio

    for i in range(6):
        mes_inicio = mes_atual
        mes_fim = mes_atual + relativedelta(months=1) - timedelta(seconds=1)

        novos_clientes = db.query(models.Cliente).filter(
            models.Cliente.data_cadastro >= mes_inicio,
            models.Cliente.data_cadastro <= mes_fim
        ).count()

        sacolas_ativadas = db.query(models.Sacola).filter(
            models.Sacola.data_vinculacao >= mes_inicio,
            models.Sacola.data_vinculacao <= mes_fim
        ).count()

        usos_query = db.query(models.RegistroUso).filter(
            models.RegistroUso.data_uso >= mes_inicio,
            models.RegistroUso.data_uso <= mes_fim
        )

        if eh_gerente:
            usos_query = usos_query.join(models.Sacola).join(
                models.UsoSacola,
                models.UsoSacola.sacola_id == models.Sacola.id
            ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

        usos = usos_query.all()

        meses.append({
            "mes": mes_atual.strftime('%Y-%m'),
            "mes_nome": mes_atual.strftime('%B/%Y'),
            "novos_clientes": novos_clientes,
            "sacolas_ativadas": sacolas_ativadas,
            "valor_movimentado": round(sum(u.valor_compra for u in usos), 2),
            "total_usos": len(usos)
        })

        mes_atual = mes_atual + relativedelta(months=1)

    total_novos_clientes = sum(m['novos_clientes'] for m in meses)
    total_sacolas_ativadas = sum(m['sacolas_ativadas'] for m in meses)
    total_valor = sum(m['valor_movimentado'] for m in meses)

    mes_mais_clientes = max(meses, key=lambda m: m['novos_clientes']) if meses else None
    mes_mais_faturamento = max(meses, key=lambda m: m['valor_movimentado']) if meses else None

    crescimento_percentual = 0
    if len(meses) >= 2 and meses[0]['valor_movimentado'] > 0:
        crescimento_percentual = (
            (meses[-1]['valor_movimentado'] - meses[0]['valor_movimentado'])
            / meses[0]['valor_movimentado'] * 100
        )

    return {
        "contexto": {
            "role": current_user.role.value,
            "unidade_id": current_user.unidade_id if eh_gerente else None
        },
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
            "total_usos": sum(m['total_usos'] for m in meses),
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


@router.get(
    "/vendas-por-terminal",
    summary="Relatório de vendas por terminal"
)
def relatorio_vendas_por_terminal(
    data: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Retorna relatório de vendas agrupadas por terminal (caixa).

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: todos os terminais do sistema
    - Gerente: apenas terminais da sua unidade

    **Filtros:**
    - data: Data específica (YYYY-MM-DD) - padrão: hoje
    """

    import json

    if not data:
        data_filtro = datetime.now().date()
    else:
        try:
            data_filtro = datetime.strptime(data, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data inválida. Use formato: YYYY-MM-DD"
            )

    eh_gerente = current_user.role == models.UserRole.gerente
    inicio_dia = datetime.combine(data_filtro, datetime.min.time())
    fim_dia = datetime.combine(data_filtro, datetime.max.time())

    vendas_query = db.query(models.RegistroUso).filter(
        models.RegistroUso.data_uso >= inicio_dia,
        models.RegistroUso.data_uso <= fim_dia
    )

    if eh_gerente:
        vendas_query = vendas_query.join(models.Sacola).join(
            models.UsoSacola,
            models.UsoSacola.sacola_id == models.Sacola.id
        ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

    vendas_dia = vendas_query.all()

    # Buscar logs para mapear terminal — usando timestamp e usuario_id (Sprint 10)
    logs_login = db.query(models.LogAuditoria).filter(
        models.LogAuditoria.acao == "login",
        models.LogAuditoria.timestamp >= inicio_dia,
        models.LogAuditoria.timestamp <= fim_dia
    ).all()

    if eh_gerente:
        logs_login = [l for l in logs_login if l.unidade_id == current_user.unidade_id]

    vendas_por_terminal = {}

    for venda in vendas_dia:
        # Pegar terminal do log de login mais próximo antes da venda
        log_proximo = db.query(models.LogAuditoria).filter(
            models.LogAuditoria.acao == "login",
            models.LogAuditoria.timestamp <= venda.data_uso,
            models.LogAuditoria.timestamp >= inicio_dia
        ).order_by(models.LogAuditoria.timestamp.desc()).first()

        terminal = "sem terminal"
        usuario_nome = "desconhecido"

        if log_proximo:
            try:
                detalhes = json.loads(log_proximo.detalhes) if log_proximo.detalhes else {}
                terminal = detalhes.get("terminal") or "sem terminal"
            except Exception:
                pass

            if log_proximo.usuario:
                usuario_nome = log_proximo.usuario.username

        if terminal not in vendas_por_terminal:
            vendas_por_terminal[terminal] = {
                "total_vendas": 0,
                "valor_total": 0.0,
                "usuarios": set(),
                "horarios": []
            }

        vendas_por_terminal[terminal]["total_vendas"] += 1
        vendas_por_terminal[terminal]["valor_total"] += float(venda.valor_compra)
        vendas_por_terminal[terminal]["usuarios"].add(usuario_nome)
        vendas_por_terminal[terminal]["horarios"].append(venda.data_uso)

    resultado = []
    for terminal, dados in sorted(vendas_por_terminal.items()):
        ticket_medio = dados["valor_total"] / dados["total_vendas"] if dados["total_vendas"] > 0 else 0
        horarios = sorted(dados["horarios"])

        resultado.append({
            "terminal": terminal,
            "total_vendas": dados["total_vendas"],
            "valor_total": round(dados["valor_total"], 2),
            "ticket_medio": round(ticket_medio, 2),
            "usuarios": sorted(list(dados["usuarios"])),
            "primeira_venda": horarios[0].strftime("%H:%M") if horarios else None,
            "ultima_venda": horarios[-1].strftime("%H:%M") if horarios else None
        })

    total_geral_vendas = sum(r["total_vendas"] for r in resultado)
    total_geral_valor = sum(r["valor_total"] for r in resultado)
    ticket_medio_geral = total_geral_valor / total_geral_vendas if total_geral_vendas > 0 else 0

    return {
        "data": data_filtro.strftime("%Y-%m-%d"),
        "contexto": {
            "role": current_user.role.value,
            "unidade_id": current_user.unidade_id if eh_gerente else None
        },
        "resumo": {
            "total_vendas": total_geral_vendas,
            "valor_total": round(total_geral_valor, 2),
            "ticket_medio": round(ticket_medio_geral, 2),
            "terminais_ativos": len(resultado)
        },
        "vendas_por_terminal": resultado
    }


@router.get(
    "/vendas-por-unidade",
    summary="Relatório de vendas por unidade",
)
def relatorio_vendas_por_unidade(
    entidade_id: int = None,
    data_inicio: str = None,
    data_fim: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Retorna relatório de vendas agrupadas por unidade.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: informa entidade_id para ver todas as unidades de uma entidade
    - Gerente: vê automaticamente apenas os dados da sua unidade

    **Parâmetros:**
    - entidade_id: ID da entidade (obrigatório para admin)
    - data_inicio: Data inicial (YYYY-MM-DD) — padrão: início do mês atual
    - data_fim: Data final (YYYY-MM-DD) — padrão: hoje
    """

    eh_gerente = current_user.role == models.UserRole.gerente

    # Admin precisa informar entidade_id
    if not eh_gerente and entidade_id is None:
        raise HTTPException(
            status_code=400,
            detail="Admin deve informar entidade_id"
        )

    # Datas padrão
    hoje = datetime.now()
    if not data_inicio:
        dt_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="data_inicio inválida. Use YYYY-MM-DD")

    if not data_fim:
        dt_fim = hoje.replace(hour=23, minute=59, second=59)
    else:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except ValueError:
            raise HTTPException(status_code=400, detail="data_fim inválida. Use YYYY-MM-DD")

    # Gerente só vê sua unidade
    if eh_gerente:
        unidades = db.query(models.Unidade).filter(
            models.Unidade.id == current_user.unidade_id
        ).all()
    else:
        entidade = db.query(models.Entidade).filter(
            models.Entidade.id == entidade_id,
            models.Entidade.ativo == True
        ).first()
        if not entidade:
            raise HTTPException(status_code=404, detail="Entidade não encontrada ou inativa")
        unidades = db.query(models.Unidade).filter(
            models.Unidade.entidade_id == entidade_id,
            models.Unidade.ativo == True
        ).all()

    resultado = []
    for unidade in unidades:
        usos = db.query(models.UsoSacola).filter(
            models.UsoSacola.unidade_id == unidade.id,
            models.UsoSacola.data_hora >= dt_inicio,
            models.UsoSacola.data_hora <= dt_fim
        ).all()

        total_usos = len(usos)
        valor_total = sum(u.valor_compra or 0 for u in usos)
        ticket_medio = valor_total / total_usos if total_usos > 0 else 0

        resultado.append({
            "unidade_id": unidade.id,
            "unidade_nome": unidade.nome,
            "cidade": unidade.cidade,
            "estado": unidade.estado,
            "total_usos": total_usos,
            "valor_total": round(valor_total, 2),
            "ticket_medio": round(ticket_medio, 2)
        })

    total_geral = sum(r["total_usos"] for r in resultado)
    valor_geral = sum(r["valor_total"] for r in resultado)

    return {
        "periodo": {
            "data_inicio": dt_inicio.strftime('%Y-%m-%d'),
            "data_fim": dt_fim.strftime('%Y-%m-%d')
        },
        "contexto": {
            "role": current_user.role.value,
            "entidade_id": entidade_id if not eh_gerente else current_user.entidade_id,
            "unidade_id": current_user.unidade_id if eh_gerente else None
        },
        "resumo": {
            "total_usos": total_geral,
            "valor_total": round(valor_geral, 2),
            "ticket_medio_geral": round(valor_geral / total_geral if total_geral > 0 else 0, 2),
            "total_unidades": len(resultado)
        },
        "vendas_por_unidade": sorted(resultado, key=lambda x: x["valor_total"], reverse=True)
    }


@router.get(
    "/vendas-totais-entidade",
    summary="Vendas totais consolidadas de uma entidade",
)
def relatorio_vendas_totais_entidade(
    entidade_id: int,
    data_inicio: str = None,
    data_fim: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Retorna vendas totais consolidadas de todas as unidades de uma entidade.

    **Permissão:** Admin only

    **Parâmetros:**
    - entidade_id: ID da entidade (obrigatório)
    - data_inicio: Data inicial (YYYY-MM-DD) — padrão: início do mês atual
    - data_fim: Data final (YYYY-MM-DD) — padrão: hoje
    """

    entidade = db.query(models.Entidade).filter(
        models.Entidade.id == entidade_id,
        models.Entidade.ativo == True
    ).first()

    if not entidade:
        raise HTTPException(status_code=404, detail="Entidade não encontrada ou inativa")

    hoje = datetime.now()
    if not data_inicio:
        dt_inicio = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="data_inicio inválida. Use YYYY-MM-DD")

    if not data_fim:
        dt_fim = hoje.replace(hour=23, minute=59, second=59)
    else:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except ValueError:
            raise HTTPException(status_code=400, detail="data_fim inválida. Use YYYY-MM-DD")

    unidades = db.query(models.Unidade).filter(
        models.Unidade.entidade_id == entidade_id,
        models.Unidade.ativo == True
    ).all()

    detalhamento_unidades = []
    total_geral_usos = 0
    total_geral_valor = 0.0

    for unidade in unidades:
        usos = db.query(models.UsoSacola).filter(
            models.UsoSacola.unidade_id == unidade.id,
            models.UsoSacola.data_hora >= dt_inicio,
            models.UsoSacola.data_hora <= dt_fim
        ).all()

        total_usos = len(usos)
        valor_total = sum(u.valor_compra or 0 for u in usos)

        total_geral_usos += total_usos
        total_geral_valor += valor_total

        detalhamento_unidades.append({
            "unidade_id": unidade.id,
            "unidade_nome": unidade.nome,
            "cidade": unidade.cidade,
            "estado": unidade.estado,
            "total_usos": total_usos,
            "valor_total": round(valor_total, 2),
            "ticket_medio": round(valor_total / total_usos if total_usos > 0 else 0, 2),
            "participacao_percentual": 0  # calculado abaixo
        })

    # Calcular participação percentual de cada unidade
    for item in detalhamento_unidades:
        item["participacao_percentual"] = round(
            item["valor_total"] / total_geral_valor * 100 if total_geral_valor > 0 else 0, 2
        )

    return {
        "entidade": {
            "id": entidade.id,
            "nome_comercial": entidade.nome_comercial,
            "cnpj": entidade.cnpj
        },
        "periodo": {
            "data_inicio": dt_inicio.strftime('%Y-%m-%d'),
            "data_fim": dt_fim.strftime('%Y-%m-%d')
        },
        "consolidado": {
            "total_usos": total_geral_usos,
            "valor_total": round(total_geral_valor, 2),
            "ticket_medio": round(total_geral_valor / total_geral_usos if total_geral_usos > 0 else 0, 2),
            "total_unidades": len(unidades)
        },
        "detalhamento_por_unidade": sorted(
            detalhamento_unidades,
            key=lambda x: x["valor_total"],
            reverse=True
        )
    }