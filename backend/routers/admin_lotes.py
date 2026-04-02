"""
Endpoints administrativos - Gerenciamento de lotes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
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
    db: Session = Depends(get_db)
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
def listar_lotes(db: Session = Depends(get_db)):
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