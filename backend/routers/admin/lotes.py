"""
Endpoints administrativos - Gerenciamento de lotes
"""
from fastapi import APIRouter, Depends, HTTPException
from utils.audit import registrar_log
from sqlalchemy.orm import Session
from database import get_db
from middleware.auth import require_role
from datetime import datetime
import models
import os
import hashlib

router = APIRouter(
    prefix="/api/admin/lotes",
    tags=["Admin - Lotes"]
)


@router.post(
    "/importar",
    summary="Importar lote de sacolas",
    description="""
    Importa um lote de sacolas gerado pelo script gerar_qrcodes.py
    
    **Processo:**
    1. Recebe intervalo de IDs (início e fim)
    2. Cria todas as sacolas no banco com status "estoque"
    3. Calcula checksum SHA256 para cada sacola
    4. Registra o lote para rastreamento
    
    **Parâmetros:**
    - data_fabricacao: Data de fabricação do lote (formato: YYYY-MM-DD)
    - inicio: Primeiro ID do lote (ex: 1 para BAG-00001)
    - fim: Último ID do lote (ex: 5000 para BAG-05000)
    
    **Validações:**
    - Data deve estar no formato correto
    - Início deve ser menor que fim
    - IDs não podem estar duplicados
    
    **Exemplo:**
```
    data_fabricacao: 2026-03-31
    inicio: 1
    fim: 5000
```
    
    **Observação:** Use os mesmos valores do CSV gerado pelo script
    """
)
def importar_lote_csv(
    data_fabricacao: str,
    inicio: int,
    fim: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Importa lote de sacolas para o banco"""
    
    # Validar data
    try:
        datetime.strptime(data_fabricacao, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Data inválida. Use formato YYYY-MM-DD (ex: 2026-03-31)"
        )
    
    # Validar range
    if inicio >= fim:
        raise HTTPException(
            status_code=400,
            detail="Início deve ser menor que fim"
        )
    
    quantidade = fim - inicio + 1
    
    if quantidade > 10000:
        raise HTTPException(
            status_code=400,
            detail="Limite máximo de 10.000 sacolas por lote"
        )
    
    # Verificar duplicatas
    primeiro_id = f"BAG-{inicio:05d}"
    ultimo_id = f"BAG-{fim:05d}"
    
    duplicata = db.query(models.Sacola).filter(
        models.Sacola.id.between(primeiro_id, ultimo_id)
    ).first()
    
    if duplicata:
        raise HTTPException(
            status_code=400,
            detail=f"Lote já foi importado. Sacola {duplicata.id} já existe no banco."
        )
    
    # Criar lote
    lote = models.Lote(
        data_fabricacao=data_fabricacao,
        quantidade=quantidade,
        inicio=inicio,
        fim=fim
    )
    db.add(lote)
    db.commit()
    db.refresh(lote)
    
    # Criar sacolas
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="SECRET_KEY não configurada no servidor"
        )
    
    sacolas_criadas = []
    
    for numero in range(inicio, fim + 1):
        sacola_id = f"BAG-{numero:05d}"
        
        # Calcular checksum
        texto = f"{sacola_id}{data_fabricacao}{SECRET_KEY}"
        hash_completo = hashlib.sha256(texto.encode()).hexdigest()
        checksum = hash_completo[:6]
        
        # Criar sacola
        sacola = models.Sacola(
            id=sacola_id,
            data_criacao=data_fabricacao,
            checksum=checksum,
            status=models.StatusSacola.estoque,
            lote_id=lote.id
        )
        db.add(sacola)
        sacolas_criadas.append(sacola_id)
    
    db.commit()
    # Registrar log
    registrar_log(
        db=db,
        usuario=current_user,
        acao="importar_lote",
        entidade_tipo="Lote",
        entidade_id=str(lote.id),
        detalhes={
            "data_fabricacao": data_fabricacao,
            "quantidade": quantidade,
            "range": f"{inicio} - {fim}"
        }
    )
    
    return {
        "sucesso": True,
        "mensagem": f"Lote importado com sucesso",
        "lote": {
            "id": lote.id,
            "data_fabricacao": lote.data_fabricacao,
            "quantidade": quantidade,
            "range": f"{primeiro_id} até {ultimo_id}"
        },
        "sacolas_criadas": len(sacolas_criadas)
    }


@router.get(
    "/",
    summary="Listar todos os lotes",
    description="""
    Lista todos os lotes de sacolas importados no sistema.
    
    **Informações retornadas para cada lote:**
    - ID do lote
    - Data de fabricação
    - Data de importação no sistema
    - Quantidade de sacolas
    - Range de IDs (início e fim)
    - Estatísticas de distribuição:
      - Sacolas em estoque
      - Sacolas ativas
      - Sacolas devolvidas
    
    **Quando usar:**
    - Conferir lotes importados
    - Verificar disponibilidade de estoque
    - Auditoria de importações
    
    **Observação:** Ordenado do mais recente para o mais antigo
    """
)
def listar_lotes(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Lista todos os lotes importados"""
    
    lotes = db.query(models.Lote).order_by(models.Lote.data_importacao.desc()).all()
    
    lotes_data = []
    for lote in lotes:
        # Contar sacolas por status
        sacolas_estoque = db.query(models.Sacola).filter(
            models.Sacola.lote_id == lote.id,
            models.Sacola.status == models.StatusSacola.estoque
        ).count()
        
        sacolas_ativas = db.query(models.Sacola).filter(
            models.Sacola.lote_id == lote.id,
            models.Sacola.status == models.StatusSacola.ativo
        ).count()
        
        sacolas_devolvidas = db.query(models.Sacola).filter(
            models.Sacola.lote_id == lote.id,
            models.Sacola.status == models.StatusSacola.devolvido
        ).count()
        
        lotes_data.append({
            "id": lote.id,
            "data_fabricacao": lote.data_fabricacao,
            "data_importacao": lote.data_importacao,
            "quantidade": lote.quantidade,
            "range": f"BAG-{lote.inicio:05d} até BAG-{lote.fim:05d}",
            "distribuicao": {
                "estoque": sacolas_estoque,
                "ativas": sacolas_ativas,
                "devolvidas": sacolas_devolvidas
            }
        })
    
    return {
        "total_lotes": len(lotes_data),
        "lotes": lotes_data
    }

@router.get(
    "/{lote_id}/estatisticas",
    summary="Estatísticas de performance do lote",
    description="""
    Retorna análise completa de performance de um lote específico.
    
    **Informações retornadas:**
    
    ** Distribuição:**
    - Total de sacolas no lote
    - Quantidade em estoque (nunca distribuídas)
    - Quantidade ativas (em uso)
    - Quantidade devolvidas
    - Taxa de ativação (% distribuídas)
    - Taxa de devolução (% devolvidas)
    
    ** Tempo de Uso:**
    - Tempo médio de uso (dias)
    - Baseado em sacolas devolvidas do lote
    
    ** Performance Financeira:**
    - Valor total movimentado pelo lote
    - Valor médio por sacola
    - Total de usos realizados
    
    ** Top Performers:**
    - Top 5 sacolas mais usadas do lote
    - Com cliente associado e utilizações
    
    **Quando usar:**
    - Comparar qualidade entre lotes
    - Identificar lotes problemáticos
    - Decisões de compra (qual fornecedor/data)
    - Análise de ciclo de vida
    
    **Parâmetro:**
    - lote_id: ID do lote (número inteiro)
    
    **Observação:** 
    - Lote deve existir no sistema
    - Cálculos baseados em dados reais
    """
)
def estatisticas_lote(
    lote_id: int, 
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """Retorna estatísticas completas de um lote"""
    
    # Buscar lote
    lote = db.query(models.Lote).filter(models.Lote.id == lote_id).first()
    if not lote:
        raise HTTPException(status_code=404, detail=f"Lote {lote_id} não encontrado")
    
    # Buscar todas sacolas do lote
    sacolas = db.query(models.Sacola).filter(models.Sacola.lote_id == lote_id).all()
    
    if not sacolas:
        return {
            "lote": {
                "id": lote_id,
                "data_fabricacao": lote.data_fabricacao,
                "data_importacao": lote.data_importacao,
                "quantidade_total": 0
            },
            "distribuicao": {
                "estoque": 0,
                "ativas": 0,
                "devolvidas": 0,
                "taxa_ativacao": 0,
                "taxa_devolucao": 0
            },
            "tempo_uso": {
                "medio_dias": 0,
                "baseado_em": 0
            },
            "performance_financeira": {
                "valor_total_movimentado": 0,
                "valor_medio_por_sacola": 0,
                "total_usos": 0
            },
            "top_sacolas": []
        }
    
    # ========== DISTRIBUIÇÃO ==========
    total_sacolas = len(sacolas)
    
    estoque = len([s for s in sacolas if s.status == models.StatusSacola.estoque])
    ativas = len([s for s in sacolas if s.status == models.StatusSacola.ativo])
    devolvidas = len([s for s in sacolas if s.status == models.StatusSacola.devolvido])
    
    distribuidas = ativas + devolvidas
    taxa_ativacao = (distribuidas / total_sacolas * 100) if total_sacolas > 0 else 0
    taxa_devolucao = (devolvidas / distribuidas * 100) if distribuidas > 0 else 0
    
    # ========== TEMPO DE USO ==========
    sacolas_devolvidas = [s for s in sacolas if s.status == models.StatusSacola.devolvido 
                          and s.data_vinculacao and s.data_devolucao]
    
    if sacolas_devolvidas:
        tempos_uso = []
        for s in sacolas_devolvidas:
            dias = (s.data_devolucao - s.data_vinculacao).days
            tempos_uso.append(dias)
        tempo_medio_dias = sum(tempos_uso) / len(tempos_uso)
    else:
        tempo_medio_dias = 0
    
    # ========== PERFORMANCE FINANCEIRA ==========
    valor_total = 0
    total_usos = 0
    
    for sacola in sacolas:
        registros = db.query(models.RegistroUso).filter(
            models.RegistroUso.sacola_id == sacola.id
        ).all()
        
        valor_total += sum(r.valor_compra for r in registros)
        total_usos += len(registros)
    
    valor_medio_por_sacola = valor_total / distribuidas if distribuidas > 0 else 0
    
    # ========== TOP PERFORMERS ==========
    sacolas_ordenadas = sorted(sacolas, key=lambda s: s.utilizacoes, reverse=True)
    top_5 = sacolas_ordenadas[:5]
    
    top_sacolas = []
    for sacola in top_5:
        if sacola.utilizacoes > 0:
            cliente = None
            if sacola.cliente_cpf:
                cliente = db.query(models.Cliente).filter(
                    models.Cliente.cpf == sacola.cliente_cpf
                ).first()
            
            top_sacolas.append({
                "sacola_id": sacola.id,
                "utilizacoes": sacola.utilizacoes,
                "status": sacola.status.value,
                "cliente": {
                    "cpf": sacola.cliente_cpf,
                    "nome": cliente.nome if cliente else "Desconhecido"
                } if sacola.cliente_cpf else None
            })
    
    # ========== MONTAR RESPONSE ==========
    return {
        "lote": {
            "id": lote_id,
            "data_fabricacao": lote.data_fabricacao,
            "data_importacao": lote.data_importacao,
            "quantidade_total": total_sacolas,
            "range_ids": f"{lote.inicio} - {lote.fim}"
        },
        
        "distribuicao": {
            "estoque": estoque,
            "ativas": ativas,
            "devolvidas": devolvidas,
            "taxa_ativacao": round(taxa_ativacao, 2),
            "taxa_devolucao": round(taxa_devolucao, 2)
        },
        
        "tempo_uso": {
            "medio_dias": round(tempo_medio_dias, 1),
            "baseado_em": len(sacolas_devolvidas)
        },
        
        "performance_financeira": {
            "valor_total_movimentado": round(valor_total, 2),
            "valor_medio_por_sacola": round(valor_medio_por_sacola, 2),
            "total_usos": total_usos
        },
        
        "top_sacolas": top_sacolas
    }