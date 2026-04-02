"""
Endpoints administrativos - Gestão de sacolas
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime
import models

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
def sacolas_proximo_limite(limite: int = 35, db: Session = Depends(get_db)):
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
def listar_estoque(lote_id: int = None, db: Session = Depends(get_db)):
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