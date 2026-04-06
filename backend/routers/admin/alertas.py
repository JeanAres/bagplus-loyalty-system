"""
Endpoints administrativos - Gerenciamento de alertas
"""
from utils.audit import registrar_log
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime
import models
from middleware.auth import require_role

router = APIRouter(
    prefix="/api/admin/alertas",
    tags=["Admin - Alertas"]
)


@router.get(
    "/",
    summary="Listar alertas",
    description="""
    Lista alertas de padrões suspeitos detectados automaticamente.
    
    **Tipos de alertas detectados:**
    - 🔴 valores_diferentes_mesmo_dia: Cliente usou múltiplas sacolas com valores diferentes no mesmo dia (esperado: rancho com valores iguais)
    - 🟡 valor_repetido_dias_diferentes: Cliente sempre compra mesmo valor em dias separados (80%+ de repetição)
    - 🔴 abuso_valor_minimo: Cliente usou 8+ sacolas com R$ 15,00 no mesmo dia
    
    **Gravidades:**
    - 🔴 Alta: Requer investigação urgente
    - 🟡 Média: Revisar quando possível
    - 🟢 Baixa: Apenas informativo
    
    **Filtros disponíveis (query params):**
    - resolvido: true/false (padrão: todos)
    - gravidade: baixa/media/alta
    - tipo: tipo específico do alerta
    
    **Exemplos de uso:**
    - GET /api/admin/alertas → todos os alertas
    - GET /api/admin/alertas?resolvido=false → apenas pendentes
    - GET /api/admin/alertas?gravidade=alta → apenas alta gravidade
    - GET /api/admin/alertas?resolvido=false&gravidade=alta → pendentes de alta gravidade
    
    **Informações retornadas:**
    - ID do alerta
    - Tipo e gravidade
    - Cliente associado (CPF e nome)
    - Descrição detalhada
    - Status de resolução
    - Observações (se resolvido)
    
    **Observação:** Ordenado por data de detecção (mais recente primeiro)
    """
)
def listar_alertas(
    resolvido: bool = None,
    gravidade: str = None,
    tipo: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Lista alertas com filtros opcionais"""
    
    query = db.query(models.Alerta)
    
    # Aplicar filtros
    if resolvido is not None:
        query = query.filter(models.Alerta.resolvido == resolvido)
    
    if gravidade:
        try:
            grav = models.GravidadeAlerta(gravidade)
            query = query.filter(models.Alerta.gravidade == grav)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Gravidade inválida. Use: baixa, media ou alta"
            )
    
    if tipo:
        try:
            tipo_enum = models.TipoAlerta(tipo)
            query = query.filter(models.Alerta.tipo == tipo_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Tipo inválido"
            )
    
    alertas = query.order_by(models.Alerta.data_deteccao.desc()).all()
    
    # Buscar informações do cliente para cada alerta
    alertas_data = []
    for alerta in alertas:
        cliente = db.query(models.Cliente).filter(
            models.Cliente.cpf == alerta.cliente_cpf
        ).first()
        
        alertas_data.append({
            "id": alerta.id,
            "tipo": alerta.tipo.value,
            "gravidade": alerta.gravidade.value,
            "cliente": {
                "cpf": alerta.cliente_cpf,
                "nome": cliente.nome if cliente else "Desconhecido"
            },
            "descricao": alerta.descricao,
            "data_deteccao": alerta.data_deteccao,
            "resolvido": alerta.resolvido,
            "observacao": alerta.observacao,
            "data_resolucao": alerta.data_resolucao
        })
    
    return {
        "total": len(alertas_data),
        "alertas": alertas_data
    }


@router.post(
    "/{alerta_id}/resolver",
    summary="Resolver alerta",
    description="""
    Marca um alerta como resolvido após investigação.
    
    **Quando usar:**
    - Após investigar o padrão suspeito
    - Após confirmar fraude ou inocência
    - Após tomar ação necessária (suspensão, aviso, etc)
    
    **Fluxo recomendado:**
    1. Receber alerta automático
    2. Investigar caso (ligar para cliente, revisar histórico)
    3. Tomar ação se necessário:
       - Fraude confirmada: suspender cliente
       - Comportamento legítimo: liberar
       - Dúvida: manter monitoramento
    4. Resolver alerta com observação detalhada
    
    **Parâmetros:**
    - alerta_id: ID do alerta (obtido em GET /alertas)
    - observacao: Resultado da investigação (mínimo 10 caracteres)
    
    **Exemplos de observações:**
```
    "Verificado com cliente. Era rancho legítimo de fato. Liberado."
    "Confirmada fraude. Cliente suspenso por uso indevido."
    "Cliente explicou situação. Foram múltiplas compras no mesmo dia. Normal."
    "Padrão suspeito confirmado. Monitorar próximos usos."
```
    
    **Validações:**
    - Alerta deve existir
    - Alerta não pode já estar resolvido
    - Observação deve ter mínimo 10 caracteres
    
    **Observação:** Após resolver, alerta não pode ser "desresolvido"
    """
)
def resolver_alerta(
    alerta_id: int,
    observacao: str,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Marca alerta como resolvido"""
    
    alerta = db.query(models.Alerta).filter(models.Alerta.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    if alerta.resolvido:
        raise HTTPException(
            status_code=400,
            detail=f"Alerta já foi resolvido em {alerta.data_resolucao}"
        )
    
    if not observacao or len(observacao.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Observação deve ter pelo menos 10 caracteres"
        )
    
    # Marcar como resolvido
    alerta.resolvido = True
    alerta.observacao = observacao.strip()
    alerta.data_resolucao = datetime.now()
    
    db.commit()
    # Registrar log
    registrar_log(
        db=db,
        usuario=current_user,
        acao="resolver_alerta",
        entidade_tipo="Alerta",
        entidade_id=str(alerta_id),
        detalhes={
            "tipo_alerta": alerta.tipo.value,
            "gravidade": alerta.gravidade.value,
            "cliente_cpf": alerta.cliente_cpf,
            "observacao": observacao
        }
    )
    db.refresh(alerta)
    
    return {
        "sucesso": True,
        "mensagem": "Alerta marcado como resolvido",
        "alerta": {
            "id": alerta.id,
            "tipo": alerta.tipo.value,
            "resolvido": alerta.resolvido,
            "observacao": alerta.observacao,
            "data_resolucao": alerta.data_resolucao
        }
    }