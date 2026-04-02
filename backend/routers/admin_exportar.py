"""
Endpoints administrativos - Exportação de dados para CSV
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime
import models
import csv
import io

router = APIRouter(
    prefix="/api/admin/exportar",
    tags=["Admin - Exportação"]
)


@router.get(
    "/clientes",
    summary="Exportar clientes para CSV",
    description="""
    Gera arquivo CSV com dados de todos os clientes cadastrados.
    
    **Colunas do CSV:**
    - CPF
    - Nome
    - Data de Cadastro
    - Status dos Benefícios
    - Sacolas Ativas
    - Total Gasto (R$)
    - Total de Usos
    
    **Filtros disponíveis:**
    - status: ativo/suspenso/bloqueado (opcional)
    - data_inicio: Data inicial de cadastro (YYYY-MM-DD, opcional)
    - data_fim: Data final de cadastro (YYYY-MM-DD, opcional)
    
    **Exemplos:**
```
    # Todos os clientes
    GET /api/admin/exportar/clientes
    
    # Apenas suspensos
    GET /api/admin/exportar/clientes?status=suspenso
    
    # Cadastrados em março
    GET /api/admin/exportar/clientes?data_inicio=2026-03-01&data_fim=2026-03-31
```
    
    **Quando usar:**
    - Backup de dados
    - Análise em Excel/Google Sheets
    - Importação em outros sistemas
    - Relatórios executivos
    
    **Formato:** CSV (compatível com Excel)  
    **Encoding:** UTF-8 com BOM (abre corretamente no Excel)
    """
)
def exportar_clientes(
    status: str = None,
    data_inicio: str = None,
    data_fim: str = None,
    db: Session = Depends(get_db)
):
    """Exporta clientes para CSV"""
    
    # Query base
    query = db.query(models.Cliente)
    
    # Filtrar por status
    if status:
        try:
            status_enum = models.StatusBeneficios(status)
            query = query.filter(models.Cliente.status_beneficios == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Status inválido. Use: ativo, suspenso ou bloqueado"
            )
    
    # Filtrar por período
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(models.Cliente.data_cadastro >= dt_inicio)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data início inválida. Use formato: YYYY-MM-DD"
            )
    
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(models.Cliente.data_cadastro <= dt_fim)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data fim inválida. Use formato: YYYY-MM-DD"
            )
    
    clientes = query.all()
    
    # Criar CSV em memória
    output = io.StringIO()
    # BOM para UTF-8 (Excel reconhece acentos)
    output.write('\ufeff')
    
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    # Cabeçalho
    writer.writerow([
        'CPF',
        'Nome',
        'Data Cadastro',
        'Status',
        'Sacolas Ativas',
        'Total Gasto (R$)',
        'Total Usos'
    ])
    
    # Dados
    for cliente in clientes:
        # Contar sacolas ativas
        sacolas_ativas = db.query(models.Sacola).filter(
            models.Sacola.cliente_cpf == cliente.cpf,
            models.Sacola.status == models.StatusSacola.ativo
        ).count()
        
        # Calcular total gasto
        registros = db.query(models.RegistroUso).join(
            models.Sacola
        ).filter(
            models.Sacola.cliente_cpf == cliente.cpf
        ).all()
        
        total_gasto = sum(r.valor_compra for r in registros)
        total_usos = len(registros)
        
        writer.writerow([
            cliente.cpf,
            cliente.nome,
            cliente.data_cadastro.strftime('%d/%m/%Y %H:%M'),
            cliente.status_beneficios.value,
            sacolas_ativas,
            f"{total_gasto:.2f}".replace('.', ','),
            total_usos
        ])
    
    # Preparar response
    output.seek(0)
    
    filename = f"clientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get(
    "/sacolas",
    summary="Exportar sacolas para CSV",
    description="""
    Gera arquivo CSV com dados de todas as sacolas do sistema.
    
    **Colunas do CSV:**
    - ID da Sacola
    - Status
    - Cliente CPF
    - Cliente Nome
    - Utilizações
    - Data Vinculação
    - Dias de Uso
    - Estado (verde/amarelo/vermelho)
    - Lote ID
    - Data Fabricação
    
    **Filtros disponíveis:**
    - status: estoque/ativo/devolvido (opcional)
    - lote_id: ID do lote (opcional)
    
    **Exemplos:**
```
    # Todas as sacolas
    GET /api/admin/exportar/sacolas
    
    # Apenas em estoque
    GET /api/admin/exportar/sacolas?status=estoque
    
    # Sacolas do lote 1
    GET /api/admin/exportar/sacolas?lote_id=1
```
    
    **Quando usar:**
    - Inventário completo
    - Auditoria de distribuição
    - Controle de estoque
    - Análise de ciclo de vida
    
    **Formato:** CSV (compatível com Excel)  
    **Encoding:** UTF-8 com BOM
    """
)
def exportar_sacolas(
    status: str = None,
    lote_id: int = None,
    db: Session = Depends(get_db)
):
    """Exporta sacolas para CSV"""
    
    # Query base
    query = db.query(models.Sacola)
    
    # Filtrar por status
    if status:
        try:
            status_enum = models.StatusSacola(status)
            query = query.filter(models.Sacola.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Status inválido. Use: estoque, ativo ou devolvido"
            )
    
    # Filtrar por lote
    if lote_id:
        query = query.filter(models.Sacola.lote_id == lote_id)
    
    sacolas = query.order_by(models.Sacola.id).all()
    
    # Criar CSV em memória
    output = io.StringIO()
    output.write('\ufeff')
    
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    # Cabeçalho
    writer.writerow([
        'ID Sacola',
        'Status',
        'Cliente CPF',
        'Cliente Nome',
        'Utilizações',
        'Data Vinculação',
        'Dias de Uso',
        'Estado',
        'Lote ID',
        'Data Fabricação'
    ])
    
    # Dados
    for sacola in sacolas:
        # Buscar cliente
        cliente = None
        if sacola.cliente_cpf:
            cliente = db.query(models.Cliente).filter(
                models.Cliente.cpf == sacola.cliente_cpf
            ).first()
        
        # Calcular dias de uso
        dias_uso = 0
        if sacola.data_vinculacao:
            dias_uso = (datetime.now() - sacola.data_vinculacao).days
        
        # Determinar estado
        estado = "-"
        if sacola.status == models.StatusSacola.ativo:
            if sacola.utilizacoes <= 15 and dias_uso <= 60:
                estado = "Verde"
            elif sacola.utilizacoes <= 25 and dias_uso <= 80:
                estado = "Amarelo"
            else:
                estado = "Vermelho"
        
        # Buscar lote
        lote = None
        if sacola.lote_id:
            lote = db.query(models.Lote).filter(models.Lote.id == sacola.lote_id).first()
        
        writer.writerow([
            sacola.id,
            sacola.status.value,
            sacola.cliente_cpf or "-",
            cliente.nome if cliente else "-",
            sacola.utilizacoes,
            sacola.data_vinculacao.strftime('%d/%m/%Y %H:%M') if sacola.data_vinculacao else "-",
            dias_uso if dias_uso > 0 else "-",
            estado,
            sacola.lote_id or "-",
            lote.data_fabricacao if lote else "-"
        ])
    
    # Preparar response
    output.seek(0)
    
    filename = f"sacolas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get(
    "/usos",
    summary="Exportar registros de uso para CSV",
    description="""
    Gera arquivo CSV com histórico completo de utilizações de sacolas.
    
    **Colunas do CSV:**
    - Data/Hora do Uso
    - Sacola ID
    - Cliente CPF
    - Cliente Nome
    - Valor da Compra (R$)
    
    **Filtros disponíveis:**
    - data_inicio: Data inicial (YYYY-MM-DD, opcional)
    - data_fim: Data final (YYYY-MM-DD, opcional)
    - cpf: Filtrar por cliente específico (opcional)
    
    **Exemplos:**
```
    # Todos os usos
    GET /api/admin/exportar/usos
    
    # Usos de março
    GET /api/admin/exportar/usos?data_inicio=2026-03-01&data_fim=2026-03-31
    
    # Usos de um cliente
    GET /api/admin/exportar/usos?cpf=12345678900
```
    
    **Quando usar:**
    - Análise financeira detalhada
    - Auditoria de transações
    - Integração com sistema contábil
    - Relatórios fiscais
    - Base para BI/Analytics
    
    **Formato:** CSV (compatível com Excel)  
    **Encoding:** UTF-8 com BOM  
    **Observação:** Pode gerar arquivo grande em sistemas com muito histórico
    """
)
def exportar_usos(
    data_inicio: str = None,
    data_fim: str = None,
    cpf: str = None,
    db: Session = Depends(get_db)
):
    """Exporta registros de uso para CSV"""
    
    # Query base
    query = db.query(models.RegistroUso).join(models.Sacola)
    
    # Filtrar por período
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(models.RegistroUso.data_uso >= dt_inicio)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data início inválida. Use formato: YYYY-MM-DD"
            )
    
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(models.RegistroUso.data_uso <= dt_fim)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data fim inválida. Use formato: YYYY-MM-DD"
            )
    
    # Filtrar por cliente
    if cpf:
        query = query.filter(models.Sacola.cliente_cpf == cpf)
    
    registros = query.order_by(models.RegistroUso.data_uso.desc()).all()
    
    # Criar CSV em memória
    output = io.StringIO()
    output.write('\ufeff')
    
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    # Cabeçalho
    writer.writerow([
        'Data/Hora',
        'Sacola ID',
        'Cliente CPF',
        'Cliente Nome',
        'Valor Compra (R$)'
    ])
    
    # Dados
    for registro in registros:
        # Buscar sacola
        sacola = db.query(models.Sacola).filter(
            models.Sacola.id == registro.sacola_id
        ).first()
        
        # Buscar cliente
        cliente = None
        if sacola and sacola.cliente_cpf:
            cliente = db.query(models.Cliente).filter(
                models.Cliente.cpf == sacola.cliente_cpf
            ).first()
        
        writer.writerow([
            registro.data_uso.strftime('%d/%m/%Y %H:%M:%S'),
            registro.sacola_id,
            sacola.cliente_cpf if sacola else "-",
            cliente.nome if cliente else "-",
            f"{registro.valor_compra:.2f}".replace('.', ',')
        ])
    
    # Preparar response
    output.seek(0)
    
    filename = f"usos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )