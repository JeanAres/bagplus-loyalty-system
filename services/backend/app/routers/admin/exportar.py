"""
Endpoints administrativos - Exportação de dados para CSV
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from datetime import datetime
from app.middleware.auth import require_role
from app.db import models
import csv
import io

router = APIRouter(
    prefix="/api/admin/exportar",
    tags=["Admin - Exportação"]
)


def _calcular_estado(utilizacoes: int, dias_uso: int) -> str:
    """Calcula estado da sacola pelo critério mais restritivo."""
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
    "/clientes",
    summary="Exportar clientes para CSV",
)
def exportar_clientes(
    status: str = None,
    data_inicio: str = None,
    data_fim: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Gera arquivo CSV com dados de clientes cadastrados.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: todos os clientes
    - Gerente: clientes que tiveram usos na sua unidade

    **Colunas do CSV:**
    - CPF, Nome, Data de Cadastro, Status, Sacolas Ativas, Total Gasto (R$), Total de Usos

    **Filtros disponíveis:**
    - status: ativo/suspenso/bloqueado (opcional)
    - data_inicio: Data inicial de cadastro (YYYY-MM-DD, opcional)
    - data_fim: Data final de cadastro (YYYY-MM-DD, opcional)

    **Formato:** CSV (UTF-8 com BOM, compatível com Excel)
    """

    eh_gerente = current_user.role == models.UserRole.gerente

    query = db.query(models.Cliente)

    if status:
        try:
            status_enum = models.StatusBeneficios(status)
            query = query.filter(models.Cliente.status_beneficios == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Status inválido. Use: ativo, suspenso ou bloqueado"
            )

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(models.Cliente.data_cadastro >= dt_inicio)
        except ValueError:
            raise HTTPException(status_code=400, detail="Data início inválida. Use formato: YYYY-MM-DD")

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(models.Cliente.data_cadastro <= dt_fim)
        except ValueError:
            raise HTTPException(status_code=400, detail="Data fim inválida. Use formato: YYYY-MM-DD")

    # Gerente: filtrar apenas clientes que tiveram usos na sua unidade
    if eh_gerente:
        cpfs_unidade = db.query(models.UsoSacola.sacola_id).filter(
            models.UsoSacola.unidade_id == current_user.unidade_id
        ).subquery()
        sacolas_unidade = db.query(models.Sacola.cliente_cpf).filter(
            models.Sacola.id.in_(cpfs_unidade),
            models.Sacola.cliente_cpf.isnot(None)
        ).distinct().subquery()
        query = query.filter(models.Cliente.cpf.in_(sacolas_unidade))

    clientes = query.all()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    writer.writerow(['CPF', 'Nome', 'Data Cadastro', 'Status', 'Sacolas Ativas', 'Total Gasto (R$)', 'Total Usos'])

    for cliente in clientes:
        sacolas_ativas = db.query(models.Sacola).filter(
            models.Sacola.cliente_cpf == cliente.cpf,
            models.Sacola.status == models.StatusSacola.ativo
        ).count()

        registros_query = db.query(models.RegistroUso).join(models.Sacola).filter(
            models.Sacola.cliente_cpf == cliente.cpf
        )
        if eh_gerente:
            registros_query = registros_query.join(
                models.UsoSacola,
                models.UsoSacola.sacola_id == models.Sacola.id
            ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

        registros = registros_query.all()
        total_gasto = sum(r.valor_compra for r in registros)

        writer.writerow([
            cliente.cpf,
            cliente.nome,
            cliente.data_cadastro.strftime('%d/%m/%Y %H:%M'),
            cliente.status_beneficios.value,
            sacolas_ativas,
            f"{total_gasto:.2f}".replace('.', ','),
            len(registros)
        ])

    output.seek(0)
    filename = f"clientes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/sacolas",
    summary="Exportar sacolas para CSV",
)
def exportar_sacolas(
    status: str = None,
    lote_id: int = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Gera arquivo CSV com dados das sacolas do sistema.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: todas as sacolas
    - Gerente: sacolas que tiveram usos na sua unidade

    **Colunas do CSV:**
    - ID Sacola, Status, Cliente CPF, Cliente Nome, Utilizações,
      Data Vinculação, Dias de Uso, Estado, Lote ID, Data Fabricação

    **Filtros disponíveis:**
    - status: estoque/ativo/devolvido (opcional)
    - lote_id: ID do lote (opcional)

    **Formato:** CSV (UTF-8 com BOM, compatível com Excel)
    """

    eh_gerente = current_user.role == models.UserRole.gerente

    query = db.query(models.Sacola)

    if status:
        try:
            status_enum = models.StatusSacola(status)
            query = query.filter(models.Sacola.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Status inválido. Use: estoque, ativo ou devolvido"
            )

    if lote_id:
        query = query.filter(models.Sacola.lote_id == lote_id)

    if eh_gerente:
        ids_unidade = db.query(models.UsoSacola.sacola_id).filter(
            models.UsoSacola.unidade_id == current_user.unidade_id
        ).distinct().subquery()
        query = query.filter(models.Sacola.id.in_(ids_unidade))

    sacolas = query.order_by(models.Sacola.id).all()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        'ID Sacola', 'Status', 'Cliente CPF', 'Cliente Nome',
        'Utilizações', 'Data Vinculação', 'Dias de Uso', 'Estado',
        'Lote ID', 'Data Fabricação'
    ])

    for sacola in sacolas:
        cliente = None
        if sacola.cliente_cpf:
            cliente = db.query(models.Cliente).filter(
                models.Cliente.cpf == sacola.cliente_cpf
            ).first()

        dias_uso = 0
        if sacola.data_vinculacao:
            dias_uso = (datetime.now() - sacola.data_vinculacao).days

        estado = "-"
        if sacola.status == models.StatusSacola.ativo:
            estado = _calcular_estado(sacola.utilizacoes, dias_uso).capitalize()

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

    output.seek(0)
    filename = f"sacolas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/usos",
    summary="Exportar registros de uso para CSV",
)
def exportar_usos(
    data_inicio: str = None,
    data_fim: str = None,
    cpf: str = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Gera arquivo CSV com histórico de utilizações de sacolas.

    **Permissão:** Admin ou Gerente

    **Comportamento por role:**
    - Admin: todos os usos do sistema
    - Gerente: apenas usos da sua unidade

    **Colunas do CSV:**
    - Data/Hora, Sacola ID, Cliente CPF, Cliente Nome, Valor da Compra (R$)

    **Filtros disponíveis:**
    - data_inicio: Data inicial (YYYY-MM-DD, opcional)
    - data_fim: Data final (YYYY-MM-DD, opcional)
    - cpf: Filtrar por cliente específico (opcional)

    **Formato:** CSV (UTF-8 com BOM, compatível com Excel)
    """

    eh_gerente = current_user.role == models.UserRole.gerente

    query = db.query(models.RegistroUso).join(models.Sacola)

    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(models.RegistroUso.data_uso >= dt_inicio)
        except ValueError:
            raise HTTPException(status_code=400, detail="Data início inválida. Use formato: YYYY-MM-DD")

    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(models.RegistroUso.data_uso <= dt_fim)
        except ValueError:
            raise HTTPException(status_code=400, detail="Data fim inválida. Use formato: YYYY-MM-DD")

    if cpf:
        query = query.filter(models.Sacola.cliente_cpf == cpf)

    if eh_gerente:
        query = query.join(
            models.UsoSacola,
            models.UsoSacola.sacola_id == models.Sacola.id
        ).filter(models.UsoSacola.unidade_id == current_user.unidade_id)

    registros = query.order_by(models.RegistroUso.data_uso.desc()).all()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    writer.writerow(['Data/Hora', 'Sacola ID', 'Cliente CPF', 'Cliente Nome', 'Valor Compra (R$)'])

    for registro in registros:
        sacola = db.query(models.Sacola).filter(models.Sacola.id == registro.sacola_id).first()
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

    output.seek(0)
    filename = f"usos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )