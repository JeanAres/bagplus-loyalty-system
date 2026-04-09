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

router = APIRouter(
    prefix="/api/admin/sacolas",
    tags=["Admin - Sacolas"]
)


@router.get(
    "/proximo-limite",
    summary="Sacolas próximas do limite",
    description="""
    Lista sacolas que estão próximas de atingir o limite de 40 usos.
    
    **Funcionalidade:**
    - Identifica sacolas que estão perto de expirar
    - Permite avisar clientes antecipadamente
    - Evita surpresas no caixa
    
    **Informações retornadas:**
    - ID da sacola
    - Cliente associado (CPF e nome)
    - Utilizações atuais
    - Usos restantes até o limite
    - Dias de uso
    - Estado da sacola (verde/amarelo/vermelho)
    
    **Parâmetros:**
    - limite: Quantidade mínima de usos para considerar "próximo do limite" (padrão: 35)
    
    **Exemplos:**
```
    # Sacolas com 35+ usos (padrão)
    GET /api/admin/sacolas/proximo-limite
    
    # Sacolas com 30+ usos
    GET /api/admin/sacolas/proximo-limite?limite=30
    
    # Sacolas com 38+ usos (muito crítico)
    GET /api/admin/sacolas/proximo-limite?limite=38
```
    
    **Quando usar:**
    - Rotina diária de gestão
    - Avisar clientes que precisam devolver logo
    - Planejamento de reposição de estoque
    
    **Observação:** 
    - Ordenado por utilizações (maior primeiro)
    - Limite máximo é 40 usos
    """
)
def sacolas_proximo_limite(
    limite: int = 35, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Lista sacolas próximas do limite de 40 usos"""
    
    # Validar limite
    if limite < 1 or limite > 40:
        raise HTTPException(
            status_code=400,
            detail="Limite deve estar entre 1 e 40"
        )
    
    # Buscar sacolas ativas com >= limite usos
    sacolas = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.ativo,
        models.Sacola.utilizacoes >= limite
    ).order_by(models.Sacola.utilizacoes.desc()).all()
    
    resultado = []
    for sacola in sacolas:
        # Buscar cliente
        cliente = db.query(models.Cliente).filter(
            models.Cliente.cpf == sacola.cliente_cpf
        ).first()
        
        # Calcular dias de uso
        if sacola.data_vinculacao:
            dias_uso = (datetime.now() - sacola.data_vinculacao).days
        else:
            dias_uso = 0
        
        # Determinar estado
        if sacola.utilizacoes <= 15 and dias_uso <= 60:
            estado = "verde"
        elif sacola.utilizacoes <= 25 and dias_uso <= 80:
            estado = "amarelo"
        else:
            estado = "vermelho"
        
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
        "sacolas": resultado
    }


@router.get(
    "/estoque",
    summary="Listar sacolas em estoque",
    description="""
    Lista sacolas disponíveis em estoque (não vinculadas a clientes).
    
    **Funcionalidade:**
    - Verificar disponibilidade de sacolas
    - Conferir estoque por lote
    - Planejar compra de novos lotes
    
    **Informações retornadas:**
    - Total de sacolas em estoque
    - Distribuição por lote
    - Range de IDs disponíveis
    - Data de fabricação de cada lote
    
    **Parâmetros (opcionais):**
    - lote_id: Filtrar por lote específico
    
    **Exemplos:**
```
    # Todo o estoque
    GET /api/admin/sacolas/estoque
    
    # Estoque de um lote específico
    GET /api/admin/sacolas/estoque?lote_id=1
```
    
    **Quando usar:**
    - Verificar disponibilidade antes de vincular
    - Conferência de estoque
    - Planejamento de compras
    - Auditoria de inventário
    
    **Observação:** 
    - Status "estoque" = nunca foram distribuídas
    - Ordenado por ID da sacola
    """
)
def listar_estoque(
    lote_id: int = None, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Lista sacolas disponíveis em estoque"""
    
    # Query base
    query = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.estoque
    )
    
    # Filtrar por lote se especificado
    if lote_id:
        lote = db.query(models.Lote).filter(models.Lote.id == lote_id).first()
        if not lote:
            raise HTTPException(
                status_code=404,
                detail=f"Lote {lote_id} não encontrado"
            )
        query = query.filter(models.Sacola.lote_id == lote_id)
    
    sacolas = query.order_by(models.Sacola.id).all()
    
    # ========== DISTRIBUIÇÃO POR LOTE ==========
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
    
    distribuicao_lotes = list(lotes_dict.values())
    
    # ========== LISTA DE IDs ==========
    # Limitar a 100 IDs na resposta (performance)
    ids_disponiveis = [s.id for s in sacolas[:100]]
    
    return {
        "total_em_estoque": len(sacolas),
        "filtro_lote": lote_id,
        "distribuicao_por_lote": distribuicao_lotes,
        "ids_disponiveis_amostra": ids_disponiveis,
        "observacao": "Amostra limitada a 100 IDs. Use filtro por lote para ver detalhes específicos." if len(sacolas) > 100 else None
    }

@router.post(
    "/{sacola_id}/transferir",
    summary="Transferir sacola entre clientes",
    description="""
    Transfere uma sacola de um cliente para outro.
    
    **Casos de uso:**
    - Cliente perdeu a sacola
    - Cliente quer dar sacola para familiar
    - Transferência de propriedade
    - Correção de vinculação errada
    
    **Validações:**
    - Sacola deve estar ativa
    - Cliente origem deve ser o dono atual
    - Cliente destino deve existir e estar ativo
    - Motivo obrigatório (mínimo 10 caracteres)
    - Cliente destino não pode estar suspenso
    
    **Parâmetros:**
    - sacola_id: ID da sacola (ex: BAG-00001)
    - cpf_origem: CPF do cliente atual (validação)
    - cpf_destino: CPF do novo dono
    - motivo: Motivo da transferência
    
    **Exemplo:**
```json
    {
      "cpf_origem": "12345678900",
      "cpf_destino": "99988877766",
      "motivo": "Cliente perdeu a sacola e autorizou transferência para familiar"
    }
```
    
    **O que acontece:**
    - Sacola muda de dono
    - Utilizações e histórico são preservados
    - Transferência é irreversível
    
    **Observação:** 
    - Operação sensível - registre motivo detalhado
    - Não é possível desfazer
    - Cliente origem perde acesso à sacola
    """
)
def transferir_sacola(
    sacola_id: str,
    cpf_origem: str,
    cpf_destino: str,
    motivo: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """Transfere sacola de um cliente para outro"""
    
    # Validar motivo
    if not motivo or len(motivo.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Motivo deve ter pelo menos 10 caracteres"
        )
    
    # Buscar sacola
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    # Verificar se sacola está ativa
    if sacola.status != models.StatusSacola.ativo:
        raise HTTPException(
            status_code=400,
            detail=f"Sacola não está ativa. Status atual: {sacola.status.value}"
        )
    
    # Validar cliente origem (deve ser o dono atual)
    if sacola.cliente_cpf != cpf_origem:
        raise HTTPException(
            status_code=400,
            detail=f"Cliente origem ({cpf_origem}) não é o dono atual da sacola. Dono atual: {sacola.cliente_cpf}"
        )
    
    # Buscar cliente origem
    cliente_origem = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_origem).first()
    if not cliente_origem:
        raise HTTPException(status_code=404, detail=f"Cliente origem não encontrado: {cpf_origem}")
    
    # Buscar cliente destino
    cliente_destino = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_destino).first()
    if not cliente_destino:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente destino não encontrado: {cpf_destino}. Cadastre o cliente primeiro."
        )
    
    # Verificar se cliente destino está ativo
    if cliente_destino.status_beneficios != models.StatusBeneficios.ativo:
        raise HTTPException(
            status_code=403,
            detail=f"Cliente destino está suspenso/bloqueado. Não pode receber sacolas."
        )
    
    # Verificar se não é o mesmo cliente
    if cpf_origem == cpf_destino:
        raise HTTPException(
            status_code=400,
            detail="Cliente origem e destino são o mesmo. Transferência não necessária."
        )
    
    # Transferir sacola
    sacola.cliente_cpf = cpf_destino
    
    db.commit()
    # Registrar log
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
            "de": {
                "cpf": cpf_origem,
                "nome": cliente_origem.nome
            },
            "para": {
                "cpf": cpf_destino,
                "nome": cliente_destino.nome
            },
            "motivo": motivo.strip(),
            "data_transferencia": datetime.now(),
            "utilizacoes_atual": sacola.utilizacoes
        },
        "observacao": "Transferência irreversível. Histórico de uso foi preservado."
    }


@router.post(
    "/{sacola_id}/resetar-contador",
    summary="Resetar contador de usos (Admin)",
    description="""
    Reseta o contador de utilizações de uma sacola para zero.
    
    **OPERAÇÃO SENSÍVEL - USE COM CAUTELA**
    
    **Casos de uso válidos:**
    - Erro de lançamento (registrou uso duplicado)
    - Falha no sistema (contador descontrolado)
    - Correção de dados após migração
    - Testes em ambiente de desenvolvimento
    
    **Casos INVÁLIDOS:**
    - Dar "nova chance" para cliente
    - Burlar limite de 40 usos
    - Favorecer clientes específicos
    
    **Validações:**
    - Sacola deve estar ativa
    - Motivo obrigatório (mínimo 15 caracteres)
    - Operação irreversível
    - Não deleta histórico de uso
    
    **Parâmetros:**
    - sacola_id: ID da sacola (ex: BAG-00001)
    - motivo: Motivo detalhado do reset
    
    **Exemplo:**
```json
    {
      "motivo": "Erro de sistema registrou 10 usos duplicados. Resetando para recalcular corretamente."
    }
```
    
    **O que acontece:**
    - Contador de utilizações → 0
    - Histórico de uso preservado
    - Sacola volta a aceitar 40 usos
    
    **O que NÃO acontece:**
    - Registros de uso NÃO são deletados
    - Data de vinculação permanece
    - Estado da sacola não muda
    
    **Observação:** 
    - Operação MUITO sensível
    - Registre motivo MUITO detalhado
    - Irreversível - não há como desfazer
    - Use apenas para correções legítimas
    """
)
def resetar_contador(
    sacola_id: str,
    motivo: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """Reseta contador de utilizações (operação sensível)"""
    
    # Validar motivo (mais rigoroso)
    if not motivo or len(motivo.strip()) < 15:
        raise HTTPException(
            status_code=400,
            detail="Motivo deve ter pelo menos 15 caracteres. Esta é uma operação sensível."
        )
    
    # Buscar sacola
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    # Verificar se sacola está ativa
    if sacola.status != models.StatusSacola.ativo:
        raise HTTPException(
            status_code=400,
            detail=f"Sacola não está ativa. Status atual: {sacola.status.value}. Só é possível resetar sacolas ativas."
        )
    
    # Buscar cliente
    cliente = db.query(models.Cliente).filter(
        models.Cliente.cpf == sacola.cliente_cpf
    ).first()
    
    # Guardar valores antigos
    utilizacoes_anterior = sacola.utilizacoes

    # Buscar cliente
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == sacola.cliente_cpf).first()
    
    # Resetar contador
    sacola.utilizacoes = 0
    
    db.commit()
    # Registrar log
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
    
    # Contar registros de uso (para validação)
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
    description="""
    Lista sacolas com padrões problemáticos que requerem atenção.
    
    **Padrões detectados:**
    
    ** Sem Uso Prolongado:**
    - Sacolas ativas sem uso há mais de 30 dias
    - Motivo: Cliente pode ter esquecido, perdido ou abandonado
    - Ação sugerida: Contato para verificar status
    
    ** Uso Intenso:**
    - Sacolas com 20+ usos em menos de 30 dias
    - Motivo: Uso comercial não autorizado ou compartilhamento
    - Ação sugerida: Investigar padrão de uso
    
    ** Múltiplas Próximas do Limite:**
    - Clientes com 3+ sacolas acima de 30 usos
    - Motivo: Acúmulo excessivo sem devolução
    - Ação sugerida: Incentivar devolução
    
    **Informações retornadas para cada categoria:**
    - Sacola ID
    - Cliente (CPF e nome)
    - Utilizações atuais
    - Dias desde último uso ou dias de posse
    - Motivo do risco
    - Gravidade (baixa/média/alta)
    
    **Quando usar:**
    - Rotina diária de gestão
    - Contato proativo com clientes
    - Prevenir perdas de sacolas
    - Identificar padrões suspeitos
    - Gestão de relacionamento
    
    **Observação:** 
    - Apenas sacolas ativas
    - Ordenado por gravidade (alta → baixa)
    """
)
def sacolas_em_risco(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Identifica sacolas com padrões problemáticos"""
    
    # Buscar todas sacolas ativas
    sacolas_ativas = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.ativo
    ).all()
    
    # ========== CATEGORIAS DE RISCO ==========
    sem_uso_prolongado = []
    uso_intenso = []
    multiplas_proximo_limite = []
    
    hoje = datetime.now()
    
    # ========== ANALISAR CADA SACOLA ==========
    for sacola in sacolas_ativas:
        # Buscar cliente
        cliente = None
        if sacola.cliente_cpf:
            cliente = db.query(models.Cliente).filter(
                models.Cliente.cpf == sacola.cliente_cpf
            ).first()
        
        # ========== 1. SEM USO PROLONGADO ==========
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
        
        # ========== 2. USO INTENSO ==========
        if sacola.data_vinculacao:
            dias_posse = (hoje - sacola.data_vinculacao).days
            
            # Se tem 20+ usos em menos de 30 dias
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
                    "motivo": f"{sacola.utilizacoes} usos em apenas {dias_posse} dias (uso comercial ou compartilhamento?)"
                })
    
    # ========== 3. MÚLTIPLAS PRÓXIMAS DO LIMITE ==========
    # Agrupar sacolas por cliente
    from collections import defaultdict
    sacolas_por_cliente = defaultdict(list)
    
    for sacola in sacolas_ativas:
        if sacola.cliente_cpf and sacola.utilizacoes >= 30:
            sacolas_por_cliente[sacola.cliente_cpf].append(sacola)
    
    # Clientes com 3+ sacolas acima de 30 usos
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
                    } for s in sorted(sacolas_cliente, key=lambda x: x.utilizacoes, reverse=True)
                ],
                "gravidade": "média",
                "motivo": f"Cliente possui {len(sacolas_cliente)} sacolas com 30+ usos (acúmulo sem devolução)"
            })
    
    # ========== ESTATÍSTICAS ==========
    total_riscos = len(sem_uso_prolongado) + len(uso_intenso) + len(multiplas_proximo_limite)
    
    riscos_alta = (
        len([s for s in sem_uso_prolongado if s['gravidade'] == 'alta']) +
        len([s for s in uso_intenso if s['gravidade'] == 'alta'])
    )
    
    riscos_media = (
        len([s for s in sem_uso_prolongado if s['gravidade'] == 'média']) +
        len(multiplas_proximo_limite)
    )
    
    # ========== MONTAR RESPONSE ==========
    return {
        "timestamp": hoje,
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