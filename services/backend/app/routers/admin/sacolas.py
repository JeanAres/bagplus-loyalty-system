"""
Endpoints administrativos - Gestão de sacolas
"""
from app.core.audit import registrar_log
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from datetime import datetime
from app.db import models
from app.middleware.auth import require_role
from collections import defaultdict

router = APIRouter(
    prefix="/api/admin/sacolas",
    tags=["Admin - Sacolas"]
)


def _calcular_estado(utilizacoes: int, dias_uso: int) -> str:
    """Calcula estado pelo critério mais restritivo entre usos e dias."""
    ranking = ["verde", "amarelo", "vermelho", "expirado"]

    if utilizacoes <= 15:
        estado_uso = "verde"
    elif utilizacoes <= 25:
        estado_uso = "amarelo"
    elif utilizacoes <= 40:
        estado_uso = "vermelho"
    else:
        estado_uso = "expirado"

    if dias_uso <= 60:
        estado_dias = "verde"
    elif dias_uso <= 80:
        estado_dias = "amarelo"
    elif dias_uso <= 90:
        estado_dias = "vermelho"
    else:
        estado_dias = "expirado"

    return ranking[max(ranking.index(estado_uso), ranking.index(estado_dias))]


@router.get(
    "/proximo-limite",
    summary="Sacolas próximas do limite",
)
def sacolas_proximo_limite(
    limite: int = 35,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Lista sacolas que estão próximas de atingir o limite de 40 usos.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: todas as sacolas do sistema
    - Gerente: apenas sacolas com usos na sua unidade

    **Parâmetros:**
    - limite: Quantidade mínima de usos (padrão: 35)
    """

    if limite < 1 or limite > 40:
        raise HTTPException(status_code=400, detail="Limite deve estar entre 1 e 40")

    eh_gerente = current_user.role == models.UserRole.gerente

    query = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.ativo,
        models.Sacola.utilizacoes >= limite
    )

    if eh_gerente:
        ids_unidade = db.query(models.UsoSacola.sacola_id).filter(
            models.UsoSacola.unidade_id == current_user.unidade_id
        ).distinct().subquery()
        query = query.filter(models.Sacola.id.in_(ids_unidade))

    sacolas = query.order_by(models.Sacola.utilizacoes.desc()).all()

    resultado = []
    for sacola in sacolas:
        cliente = db.query(models.Cliente).filter(
            models.Cliente.cpf == sacola.cliente_cpf
        ).first()

        dias_uso = 0
        if sacola.data_vinculacao:
            dias_uso = (datetime.now() - sacola.data_vinculacao).days

        estado = _calcular_estado(sacola.utilizacoes, dias_uso)

        resultado.append({
            "sacola_id": sacola.id,
            "cliente": {
                "cpf": sacola.cliente_cpf,
                "nome": cliente.nome if cliente else "Desconhecido"
            },
            "utilizacoes": sacola.utilizacoes,
            "usos_restantes": 40 - sacola.utilizacoes,
            "dias_de_uso": dias_uso,
            "estado": estado,
            "alerta": "CRÍTICO" if sacola.utilizacoes >= 38 else "ATENÇÃO"
        })

    return {
        "total_sacolas": len(resultado),
        "limite_configurado": limite,
        "contexto": {
            "role": current_user.role.value,
            "unidade_id": current_user.unidade_id if eh_gerente else None
        },
        "sacolas": resultado
    }


@router.get(
    "/estoque",
    summary="Listar sacolas em estoque",
)
def listar_estoque(
    lote_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Lista sacolas disponíveis em estoque (não vinculadas a clientes).

    **Permissão:** Admin ou Gerente

    **Parâmetros:**
    - lote_id: Filtrar por lote específico (opcional)
    """

    query = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.estoque
    )

    if lote_id:
        lote = db.query(models.Lote).filter(models.Lote.id == lote_id).first()
        if not lote:
            raise HTTPException(status_code=404, detail=f"Lote {lote_id} não encontrado")
        query = query.filter(models.Sacola.lote_id == lote_id)

    sacolas = query.order_by(models.Sacola.id).all()

    lotes_dict = {}
    for sacola in sacolas:
        if sacola.lote_id not in lotes_dict:
            lote = db.query(models.Lote).filter(models.Lote.id == sacola.lote_id).first()
            lotes_dict[sacola.lote_id] = {
                "lote_id": sacola.lote_id,
                "data_fabricacao": lote.data_fabricacao if lote else "Desconhecido",
                "quantidade": 0,
                "range_inicio": sacola.id,
                "range_fim": sacola.id
            }

        lotes_dict[sacola.lote_id]["quantidade"] += 1
        lotes_dict[sacola.lote_id]["range_fim"] = sacola.id

    ids_disponiveis = [s.id for s in sacolas[:100]]

    return {
        "total_em_estoque": len(sacolas),
        "filtro_lote": lote_id,
        "distribuicao_por_lote": list(lotes_dict.values()),
        "ids_disponiveis_amostra": ids_disponiveis,
        "observacao": "Amostra limitada a 100 IDs. Use filtro por lote para ver detalhes específicos." if len(sacolas) > 100 else None
    }


@router.post(
    "/{sacola_id}/transferir",
    summary="Transferir sacola entre clientes",
)
def transferir_sacola(
    sacola_id: str,
    cpf_origem: str,
    cpf_destino: str,
    motivo: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Transfere uma sacola de um cliente para outro.

    **Permissão:** Admin

    **Validações:**
    - Sacola deve estar ativa
    - Cliente origem deve ser o dono atual
    - Cliente destino deve existir e estar ativo
    - Motivo obrigatório (mínimo 10 caracteres)
    """

    if not motivo or len(motivo.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Motivo deve ter pelo menos 10 caracteres"
        )

    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")

    if sacola.status != models.StatusSacola.ativo:
        raise HTTPException(
            status_code=400,
            detail=f"Sacola não está ativa. Status atual: {sacola.status.value}"
        )

    if sacola.cliente_cpf != cpf_origem:
        raise HTTPException(
            status_code=400,
            detail=f"Cliente origem ({cpf_origem}) não é o dono atual da sacola. Dono atual: {sacola.cliente_cpf}"
        )

    cliente_origem = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_origem).first()
    if not cliente_origem:
        raise HTTPException(status_code=404, detail=f"Cliente origem não encontrado: {cpf_origem}")

    cliente_destino = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_destino).first()
    if not cliente_destino:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente destino não encontrado: {cpf_destino}. Cadastre o cliente primeiro."
        )

    if cliente_destino.status_beneficios != models.StatusBeneficios.ativo:
        raise HTTPException(
            status_code=403,
            detail="Cliente destino está suspenso/bloqueado. Não pode receber sacolas."
        )

    if cpf_origem == cpf_destino:
        raise HTTPException(
            status_code=400,
            detail="Cliente origem e destino são o mesmo. Transferência não necessária."
        )

    sacola.cliente_cpf = cpf_destino
    db.commit()

    registrar_log(
        db=db,
        usuario=current_user,
        acao="transferir_sacola",
        entidade_tipo="Sacola",
        entidade_id=sacola_id,
        detalhes={
            "cpf_origem": cpf_origem,
            "nome_origem": cliente_origem.nome,
            "cpf_destino": cpf_destino,
            "nome_destino": cliente_destino.nome,
            "motivo": motivo.strip(),
            "utilizacoes_atual": sacola.utilizacoes
        }
    )
    db.refresh(sacola)

    return {
        "sucesso": True,
        "mensagem": "Sacola transferida com sucesso",
        "transferencia": {
            "sacola_id": sacola_id,
            "de": {"cpf": cpf_origem, "nome": cliente_origem.nome},
            "para": {"cpf": cpf_destino, "nome": cliente_destino.nome},
            "motivo": motivo.strip(),
            "data_transferencia": datetime.now(),
            "utilizacoes_atual": sacola.utilizacoes
        },
        "observacao": "Transferência irreversível. Histórico de uso foi preservado."
    }


@router.post(
    "/{sacola_id}/resetar-contador",
    summary="Resetar contador de usos (Admin)",
)
def resetar_contador(
    sacola_id: str,
    motivo: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Reseta o contador de utilizações de uma sacola para zero.

    **Permissão:** Admin

    **OPERAÇÃO SENSÍVEL - USE COM CAUTELA**

    **Validações:**
    - Sacola deve estar ativa
    - Motivo obrigatório (mínimo 15 caracteres)
    """

    if not motivo or len(motivo.strip()) < 15:
        raise HTTPException(
            status_code=400,
            detail="Motivo deve ter pelo menos 15 caracteres. Esta é uma operação sensível."
        )

    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")

    if sacola.status != models.StatusSacola.ativo:
        raise HTTPException(
            status_code=400,
            detail=f"Sacola não está ativa. Status atual: {sacola.status.value}."
        )

    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == sacola.cliente_cpf).first()
    utilizacoes_anterior = sacola.utilizacoes

    sacola.utilizacoes = 0
    db.commit()

    registrar_log(
        db=db,
        usuario=current_user,
        acao="resetar_contador",
        entidade_tipo="Sacola",
        entidade_id=sacola_id,
        detalhes={
            "utilizacoes_anterior": utilizacoes_anterior,
            "utilizacoes_nova": 0,
            "motivo": motivo.strip(),
            "cliente_cpf": sacola.cliente_cpf,
            "cliente_nome": cliente.nome if cliente else "Desconhecido"
        }
    )
    db.refresh(sacola)

    total_registros = db.query(models.RegistroUso).filter(
        models.RegistroUso.sacola_id == sacola_id
    ).count()

    return {
        "sucesso": True,
        "mensagem": "Contador de utilizações resetado",
        "sacola": {
            "id": sacola_id,
            "cliente": {
                "cpf": sacola.cliente_cpf,
                "nome": cliente.nome if cliente else "Desconhecido"
            },
            "utilizacoes_anterior": utilizacoes_anterior,
            "utilizacoes_atual": sacola.utilizacoes,
            "registros_historico_preservados": total_registros
        },
        "operacao": {
            "motivo": motivo.strip(),
            "data": datetime.now(),
            "irreversivel": True
        },
        "aviso": "Histórico de uso foi preservado. Apenas o contador foi resetado."
    }


@router.get(
    "/em-risco",
    summary="Identificar sacolas em risco",
)
def sacolas_em_risco(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Lista sacolas com padrões problemáticos que requerem atenção.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: todas as sacolas do sistema
    - Gerente: apenas sacolas com usos na sua unidade

    **Padrões detectados:**
    - Sem uso prolongado (30+ dias sem uso)
    - Uso intenso (20+ usos em menos de 30 dias)
    - Múltiplas próximas do limite (3+ sacolas com 30+ usos)
    """

    eh_gerente = current_user.role == models.UserRole.gerente

    query = db.query(models.Sacola).filter(models.Sacola.status == models.StatusSacola.ativo)

    if eh_gerente:
        ids_unidade = db.query(models.UsoSacola.sacola_id).filter(
            models.UsoSacola.unidade_id == current_user.unidade_id
        ).distinct().subquery()
        query = query.filter(models.Sacola.id.in_(ids_unidade))

    sacolas_ativas = query.all()

    sem_uso_prolongado = []
    uso_intenso = []
    hoje = datetime.now()

    for sacola in sacolas_ativas:
        cliente = None
        if sacola.cliente_cpf:
            cliente = db.query(models.Cliente).filter(
                models.Cliente.cpf == sacola.cliente_cpf
            ).first()

        # Sem uso prolongado
        if sacola.ultima_utilizacao:
            dias_sem_uso = (hoje - sacola.ultima_utilizacao).days
            if dias_sem_uso > 30:
                sem_uso_prolongado.append({
                    "sacola_id": sacola.id,
                    "cliente": {
                        "cpf": sacola.cliente_cpf,
                        "nome": cliente.nome if cliente else "Desconhecido"
                    } if sacola.cliente_cpf else None,
                    "utilizacoes": sacola.utilizacoes,
                    "dias_sem_uso": dias_sem_uso,
                    "ultimo_uso": sacola.ultima_utilizacao,
                    "gravidade": "alta" if dias_sem_uso > 60 else "média",
                    "motivo": f"Sem uso há {dias_sem_uso} dias (possível perda ou abandono)"
                })

        # Uso intenso
        if sacola.data_vinculacao:
            dias_posse = (hoje - sacola.data_vinculacao).days
            if dias_posse < 30 and sacola.utilizacoes >= 20:
                uso_intenso.append({
                    "sacola_id": sacola.id,
                    "cliente": {
                        "cpf": sacola.cliente_cpf,
                        "nome": cliente.nome if cliente else "Desconhecido"
                    } if sacola.cliente_cpf else None,
                    "utilizacoes": sacola.utilizacoes,
                    "dias_posse": dias_posse,
                    "media_usos_dia": round(sacola.utilizacoes / dias_posse, 1) if dias_posse > 0 else 0,
                    "gravidade": "alta",
                    "motivo": f"{sacola.utilizacoes} usos em apenas {dias_posse} dias"
                })

    # Múltiplas próximas do limite
    sacolas_por_cliente = defaultdict(list)
    for sacola in sacolas_ativas:
        if sacola.cliente_cpf and sacola.utilizacoes >= 30:
            sacolas_por_cliente[sacola.cliente_cpf].append(sacola)

    multiplas_proximo_limite = []
    for cpf, sacolas_cliente in sacolas_por_cliente.items():
        if len(sacolas_cliente) >= 3:
            cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
            multiplas_proximo_limite.append({
                "cliente": {
                    "cpf": cpf,
                    "nome": cliente.nome if cliente else "Desconhecido"
                },
                "quantidade_sacolas": len(sacolas_cliente),
                "sacolas": [
                    {
                        "id": s.id,
                        "utilizacoes": s.utilizacoes,
                        "usos_restantes": 40 - s.utilizacoes
                    }
                    for s in sorted(sacolas_cliente, key=lambda x: x.utilizacoes, reverse=True)
                ],
                "gravidade": "média",
                "motivo": f"Cliente possui {len(sacolas_cliente)} sacolas com 30+ usos"
            })

    total_riscos = len(sem_uso_prolongado) + len(uso_intenso) + len(multiplas_proximo_limite)
    riscos_alta = len([s for s in sem_uso_prolongado if s['gravidade'] == 'alta']) + len(uso_intenso)
    riscos_media = len([s for s in sem_uso_prolongado if s['gravidade'] == 'média']) + len(multiplas_proximo_limite)

    return {
        "timestamp": hoje,
        "contexto": {
            "role": current_user.role.value,
            "unidade_id": current_user.unidade_id if eh_gerente else None
        },
        "total_sacolas_ativas": len(sacolas_ativas),
        "total_riscos_detectados": total_riscos,
        "resumo_gravidade": {
            "alta": riscos_alta,
            "media": riscos_media
        },
        "categorias": {
            "sem_uso_prolongado": {
                "total": len(sem_uso_prolongado),
                "descricao": "Sacolas sem uso há mais de 30 dias",
                "sacolas": sorted(sem_uso_prolongado, key=lambda x: x['dias_sem_uso'], reverse=True)
            },
            "uso_intenso": {
                "total": len(uso_intenso),
                "descricao": "Sacolas com 20+ usos em menos de 30 dias",
                "sacolas": sorted(uso_intenso, key=lambda x: x['utilizacoes'], reverse=True)
            },
            "multiplas_proximo_limite": {
                "total": len(multiplas_proximo_limite),
                "descricao": "Clientes com 3+ sacolas acima de 30 usos",
                "casos": sorted(multiplas_proximo_limite, key=lambda x: x['quantidade_sacolas'], reverse=True)
            }
        },
        "acoes_sugeridas": {
            "sem_uso_prolongado": "Contatar cliente para verificar status da sacola",
            "uso_intenso": "Investigar padrão de uso (possível uso comercial)",
            "multiplas_proximo_limite": "Incentivar devolução antes de expirar"
        }
    }