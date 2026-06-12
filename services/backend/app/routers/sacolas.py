"""
Endpoints relacionados a sacolas
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from app.middleware.auth import get_current_user, require_role
from app.core.validators import validar_valor_monetario
from sqlalchemy.orm import Session
from app.db.session import get_db
from datetime import datetime, timedelta
from app.db import models
from app.core.helpers import (
    validar_qrcode_checksum,
    calcular_desconto_fidelidade,
    detectar_valores_diferentes_mesmo_dia,
    detectar_valor_repetido_dias_diferentes,
    detectar_abuso_valor_minimo
)
from app.core.notifications import (
    notificar_sacola_proximo_limite,
    notificar_desconto_disponivel
)
from app.core.audit import registrar_log

router = APIRouter(
    prefix="/api/sacolas",
    tags=["Sacolas"]
)


# ============================================
# HELPER: Calcular estado da sacola
# ============================================

def calcular_estado_sacola(utilizacoes: int, dias_uso: int):
    """
    Calcula estado e desconto de devolução da sacola.

    Usos e dias são avaliados independentemente.
    O mais restritivo dos dois vence.

    Faixas:
    - Verde:    até 15 usos / até 60 dias  → R$ 40,00
    - Amarelo:  até 25 usos / até 80 dias  → R$ 20,00
    - Vermelho: até 40 usos / até 90 dias  → R$ 10,00
    - Expirado: acima dos limites          → R$ 0,00
    """
    ranking = ["verde", "amarelo", "vermelho", "expirado"]
    descontos = {"verde": 40.00, "amarelo": 20.00, "vermelho": 10.00, "expirado": 0.00}

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

    estado = ranking[max(ranking.index(estado_uso), ranking.index(estado_dias))]
    desconto = descontos[estado]

    return estado, desconto


# ============================================
# ENDPOINTS
# ============================================

@router.get(
    "/ativas",
    summary="Listar sacolas ativas",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def listar_sacolas_ativas(db: Session = Depends(get_db)):
    """
    Lista todas as sacolas que estão ativas (vinculadas a clientes).

    **Informações retornadas:**
    - ID da sacola
    - Cliente vinculado
    - Número de utilizações
    - Data da última utilização

    **Observação:** Lista ordenada por última utilização (mais recentes primeiro)
    """

    sacolas = db.query(models.Sacola).filter(
        models.Sacola.status == models.StatusSacola.ativo
    ).order_by(models.Sacola.ultima_utilizacao.desc()).all()

    resultado = []
    for sacola in sacolas:
        cliente = db.query(models.Cliente).filter(
            models.Cliente.cpf == sacola.cliente_cpf
        ).first()

        resultado.append({
            "id": sacola.id,
            "cliente": {
                "cpf": cliente.cpf if cliente else None,
                "nome": cliente.nome if cliente else None
            },
            "utilizacoes": sacola.utilizacoes,
            "ultima_utilizacao": sacola.ultima_utilizacao
        })

    return {
        "total": len(resultado),
        "sacolas": resultado
    }


@router.get(
    "/{sacola_id}",
    summary="Buscar informações da sacola",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def buscar_sacola(sacola_id: str, db: Session = Depends(get_db)):
    """
    Retorna todas as informações de uma sacola específica.

    **Quando usar:**
    - Sistema de caixa ao escanear QR Code
    - Consulta de status de sacola

    **Estados da sacola (o mais restritivo entre usos e dias vence):**
    - 🟢 Verde:    até 15 usos / até 60 dias  → desconto R$ 40,00
    - 🟡 Amarelo:  até 25 usos / até 80 dias  → desconto R$ 20,00
    - 🔴 Vermelho: até 40 usos / até 90 dias  → desconto R$ 10,00
    - ⚫ Expirado: acima dos limites           → sem desconto
    """

    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")

    cliente_info = None
    if sacola.cliente_cpf:
        cliente = db.query(models.Cliente).filter(models.Cliente.cpf == sacola.cliente_cpf).first()
        if cliente:
            cliente_info = {"cpf": cliente.cpf, "nome": cliente.nome}

    fidelidade = calcular_desconto_fidelidade(sacola.utilizacoes)

    if sacola.data_vinculacao:
        dias_uso = (datetime.now() - sacola.data_vinculacao).days
    else:
        dias_uso = 0

    estado, desconto_devolucao = calcular_estado_sacola(sacola.utilizacoes, dias_uso)

    tempo_ultima_utilizacao = None
    if sacola.ultima_utilizacao:
        delta = datetime.now() - sacola.ultima_utilizacao
        horas = delta.total_seconds() / 3600
        tempo_ultima_utilizacao = f"{int(horas)} horas atrás"

    return {
        "id": sacola.id,
        "status": sacola.status.value,
        "utilizacoes": sacola.utilizacoes,
        "dias_de_uso": dias_uso,
        "estado": estado,
        "cliente": cliente_info,
        "descontos": {
            "fidelidade": fidelidade,
            "devolucao": desconto_devolucao
        },
        "ultima_utilizacao": tempo_ultima_utilizacao
    }


@router.post(
    "/ativar",
    summary="Ativar sacola (individual)",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def ativar_sacola(
    qr_code: str,
    cpf_cliente: str,
    request: Request,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Vincula uma sacola a um cliente através do QR Code.

    **Uso principal:** Sistema de caixa com leitora de QR Code (pistolinha)

    **Parâmetros:**
    - qr_code: QR Code completo lido pela pistolinha (ex: BAG-00001:2026-03-31:checksum)
    - cpf_cliente: CPF do cliente (11 dígitos)

    **Observação:** Para vincular múltiplas sacolas de uma vez (testes), use /ativar-lote
    """

    valido, sacola_id, data_criacao, erro = validar_qrcode_checksum(qr_code)
    if not valido:
        raise HTTPException(status_code=400, detail=erro)

    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(
            status_code=404,
            detail=f"Sacola {sacola_id} não encontrada. Verifique se o lote foi importado."
        )

    if sacola.checksum != qr_code.split(':')[2]:
        raise HTTPException(
            status_code=400,
            detail="Checksum não confere com registro do banco. QR Code pode estar adulterado."
        )

    if sacola.status != models.StatusSacola.estoque:
        if sacola.status == models.StatusSacola.ativo:
            cliente_atual = db.query(models.Cliente).filter(
                models.Cliente.cpf == sacola.cliente_cpf
            ).first()
            raise HTTPException(
                status_code=400,
                detail=f"Sacola já está vinculada ao cliente {cliente_atual.nome} (CPF: {cliente_atual.cpf})"
            )
        elif sacola.status == models.StatusSacola.devolvido:
            raise HTTPException(
                status_code=400,
                detail="Sacola já foi devolvida e não pode ser reativada"
            )

    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_cliente).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com CPF {cpf_cliente} não encontrado. Cadastre o cliente primeiro."
        )

    if cliente.status_beneficios != models.StatusBeneficios.ativo:
        if cliente.status_beneficios == models.StatusBeneficios.suspenso:
            raise HTTPException(
                status_code=403,
                detail=f"Cliente suspenso. Motivo: {cliente.motivo_suspensao or 'Não especificado'}"
            )
        elif cliente.status_beneficios == models.StatusBeneficios.bloqueado:
            raise HTTPException(
                status_code=403,
                detail="Cliente bloqueado permanentemente do programa"
            )

    sacola.status = models.StatusSacola.ativo
    sacola.cliente_cpf = cpf_cliente
    sacola.data_vinculacao = datetime.now()

    db.commit()
    db.refresh(sacola)

    # ========== LOG DE AUDITORIA ==========
    try:
        registrar_log(
            db=db,
            usuario=current_user,
            acao="ativar_sacola",
            entidade_tipo="Sacola",
            entidade_id=sacola_id,
            detalhes={
                "sacola_id": sacola_id,
                "cliente_cpf": cpf_cliente,
                "cliente_nome": cliente.nome,
                "terminal": getattr(current_user, 'terminal', None)
            },
            ip_address=request.client.host if request.client else None
        )
        db.commit()
    except Exception as e:
        print(f"Erro ao registrar log de auditoria: {e}")

    return {
        "sucesso": True,
        "mensagem": f"Sacola {sacola_id} ativada com sucesso",
        "sacola": {"id": sacola.id, "status": sacola.status.value},
        "cliente": {"cpf": cliente.cpf, "nome": cliente.nome}
    }


@router.post(
    "/ativar-lote",
    summary="Ativar múltiplas sacolas (lote)",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def ativar_sacolas_lote(
    qr_codes: list[str],
    cpf_cliente: str,
    db: Session = Depends(get_db)
):
    """
    Vincula múltiplas sacolas a um cliente de uma só vez.

    **USO: Apenas para TESTES**
    - Produção: use /ativar com pistolinha (uma por uma)
    - Testes: facilita vincular várias sacolas rapidamente

    **Parâmetros:**
    - qr_codes: Array de QR Codes completos
    - cpf_cliente: CPF do cliente
    """

    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_cliente).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com CPF {cpf_cliente} não encontrado. Cadastre o cliente primeiro."
        )

    if cliente.status_beneficios != models.StatusBeneficios.ativo:
        if cliente.status_beneficios == models.StatusBeneficios.suspenso:
            raise HTTPException(
                status_code=403,
                detail=f"Cliente suspenso. Motivo: {cliente.motivo_suspensao or 'Não especificado'}"
            )
        elif cliente.status_beneficios == models.StatusBeneficios.bloqueado:
            raise HTTPException(
                status_code=403,
                detail="Cliente bloqueado permanentemente do programa"
            )

    vinculadas = []
    erros = []

    for qr_code in qr_codes:
        try:
            valido, sacola_id, data_criacao, erro = validar_qrcode_checksum(qr_code)

            if not valido:
                erros.append({"qr_code": qr_code, "erro": erro})
                continue

            sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
            if not sacola:
                erros.append({
                    "qr_code": qr_code,
                    "erro": f"Sacola {sacola_id} não encontrada no sistema."
                })
                continue

            if sacola.checksum != qr_code.split(':')[2]:
                erros.append({"qr_code": qr_code, "erro": "Checksum não confere com registro do banco."})
                continue

            if sacola.status != models.StatusSacola.estoque:
                if sacola.status == models.StatusSacola.ativo:
                    cliente_atual = db.query(models.Cliente).filter(
                        models.Cliente.cpf == sacola.cliente_cpf
                    ).first()
                    erros.append({
                        "qr_code": qr_code,
                        "erro": f"Sacola já vinculada ao cliente {cliente_atual.nome} (CPF: {cliente_atual.cpf})"
                    })
                    continue
                elif sacola.status == models.StatusSacola.devolvido:
                    erros.append({"qr_code": qr_code, "erro": "Sacola já foi devolvida."})
                    continue

            sacola.status = models.StatusSacola.ativo
            sacola.cliente_cpf = cpf_cliente
            sacola.data_vinculacao = datetime.now()
            vinculadas.append(sacola_id)

        except Exception as e:
            erros.append({"qr_code": qr_code, "erro": f"Erro inesperado: {str(e)}"})

    db.commit()

    total_enviadas = len(qr_codes)
    total_vinculadas = len(vinculadas)
    total_erros = len(erros)

    if total_vinculadas > 0 and total_erros == 0:
        return {
            "sucesso": True,
            "mensagem": f"Todas as {total_vinculadas} sacolas foram vinculadas com sucesso",
            "total_enviadas": total_enviadas,
            "total_vinculadas": total_vinculadas,
            "total_erros": 0,
            "vinculadas": vinculadas,
            "cliente": {"cpf": cliente.cpf, "nome": cliente.nome}
        }
    elif total_vinculadas > 0 and total_erros > 0:
        return {
            "sucesso": "parcial",
            "mensagem": f"{total_vinculadas} sacolas vinculadas, {total_erros} falharam",
            "total_enviadas": total_enviadas,
            "total_vinculadas": total_vinculadas,
            "total_erros": total_erros,
            "vinculadas": vinculadas,
            "erros": erros,
            "cliente": {"cpf": cliente.cpf, "nome": cliente.nome}
        }
    else:
        return {
            "sucesso": False,
            "mensagem": f"Nenhuma sacola foi vinculada. Todas as {total_erros} falharam.",
            "total_enviadas": total_enviadas,
            "total_vinculadas": 0,
            "total_erros": total_erros,
            "erros": erros
        }


@router.post(
    "/registrar-uso",
    summary="Registrar uso da sacola",
)
def registrar_uso(
    qr_code: str,
    valor_compra: str,
    request: Request,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registra uma nova utilização da sacola com valor da compra.

    **Parâmetros:**
    - qr_code: QR Code completo lido pela pistolinha (ex: BAG-00001:2026-03-31:checksum)
    - valor_compra: Valor da compra (aceita vírgula ou ponto, ex: 125,50)

    **Validações aplicadas:**
    -  QR Code deve ser válido
    -  Sacola deve estar ativa (vinculada a cliente)
    -  Intervalo mínimo de 4 horas desde último uso
    -  Valor mínimo de R$ 15,00
    -  Cliente não pode estar suspenso
    -  Máximo 40 utilizações por sacola

    **Detecções automáticas:** fraudes e padrões suspeitos
    **Notificações automáticas:** marcos de fidelidade e proximidade do limite
    """

    # Validar QR Code e extrair sacola_id
    valido, sacola_id, data_criacao, erro = validar_qrcode_checksum(qr_code)
    if not valido:
        raise HTTPException(status_code=400, detail=erro)

    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")

    if sacola.status != models.StatusSacola.ativo:
        raise HTTPException(
            status_code=400,
            detail=f"Sacola não está ativa. Status atual: {sacola.status.value}"
        )

    if sacola.ultima_utilizacao:
        tempo_desde_ultimo = datetime.now() - sacola.ultima_utilizacao
        if tempo_desde_ultimo < timedelta(hours=4):
            horas_restantes = 4 - (tempo_desde_ultimo.total_seconds() / 3600)
            horas = int(horas_restantes)
            minutos = int((horas_restantes - horas) * 60)
            if horas > 0:
                tempo_msg = f"{horas}h {minutos}min"
            else:
                tempo_msg = f"{minutos} minutos"
            raise HTTPException(
                status_code=400,
                detail=f"Intervalo mínimo não atingido. Aguarde {tempo_msg}"
            )

    valor_float = validar_valor_monetario(valor_compra)

    if valor_float < 15.00:
        raise HTTPException(status_code=400, detail="Valor mínimo de compra: R$ 15,00")

    cliente = db.query(models.Cliente).filter(
        models.Cliente.cpf == sacola.cliente_cpf
    ).first()

    if cliente.status_beneficios != models.StatusBeneficios.ativo:
        raise HTTPException(
            status_code=403,
            detail=f"Cliente suspenso. Não pode utilizar sacolas. Motivo: {cliente.motivo_suspensao}"
        )

    if sacola.utilizacoes >= 40:
        raise HTTPException(
            status_code=400,
            detail="Sacola atingiu limite máximo de 40 utilizações. Devolva a sacola."
        )

    # Registrar em RegistroUso (legado)
    registro = models.RegistroUso(
        sacola_id=sacola_id,
        valor_compra=valor_float
    )
    db.add(registro)

    # Registrar em UsoSacola (multi-tenant)
    uso_sacola = models.UsoSacola(
        sacola_id=sacola_id,
        entidade_id=current_user.entidade_id,
        unidade_id=current_user.unidade_id,
        usuario_id=current_user.id,
        valor_compra=valor_float,
        data_hora=datetime.now()
    )
    db.add(uso_sacola)

    sacola.utilizacoes += 1
    sacola.ultima_utilizacao = datetime.now()

    db.commit()
    db.refresh(sacola)

    # ========== LOG DE AUDITORIA ==========
    try:
        terminal = getattr(current_user, 'terminal', None)
        registrar_log(
            db=db,
            usuario=current_user,
            acao="registrar_uso",
            entidade_tipo="Sacola",
            entidade_id=sacola_id,
            detalhes={
                "sacola_id": sacola_id,
                "valor_compra": valor_float,
                "utilizacoes": sacola.utilizacoes,
                "cliente_cpf": sacola.cliente_cpf,
                "terminal": terminal
            },
            ip_address=request.client.host if request.client else None
        )
        db.commit()
    except Exception as e:
        print(f"Erro ao registrar log de auditoria: {e}")

    # ========== NOTIFICAÇÕES AUTOMÁTICAS ==========
    if sacola.utilizacoes >= 35 and sacola.utilizacoes < 40:
        try:
            notificar_sacola_proximo_limite(
                db=db,
                cliente_cpf=sacola.cliente_cpf,
                sacola_id=sacola.id,
                utilizacoes=sacola.utilizacoes
            )
            db.commit()
        except Exception as e:
            print(f"Erro ao criar notificação: {e}")

    marcos_fidelidade = [10, 20, 30, 40]
    if sacola.utilizacoes in marcos_fidelidade:
        try:
            notificar_desconto_disponivel(
                db=db,
                cliente_cpf=sacola.cliente_cpf,
                marco=sacola.utilizacoes
            )
            db.commit()
        except Exception as e:
            print(f"Erro ao criar notificação de desconto: {e}")

    # ========== DETECÇÃO DE FRAUDES ==========
    try:
        detectar_valores_diferentes_mesmo_dia(sacola.cliente_cpf, db)
        detectar_valor_repetido_dias_diferentes(sacola.cliente_cpf, db)
        detectar_abuso_valor_minimo(sacola.cliente_cpf, db)
    except Exception as e:
        print(f"Erro na detecção de padrões: {e}")

    fidelidade = calcular_desconto_fidelidade(sacola.utilizacoes)

    return {
        "sucesso": True,
        "mensagem": f"Uso #{sacola.utilizacoes} registrado com sucesso",
        "sacola": {
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "usos_restantes": 40 - sacola.utilizacoes
        },
        "valor_compra": valor_float,
        "desconto_fidelidade": fidelidade
    }


@router.post(
    "/devolver",
    summary="Devolver sacola",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def devolver_sacola(
    sacola_id: str,
    request: Request,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Processa a devolução de uma sacola e calcula desconto.

    **Cálculo de desconto (o mais restritivo entre usos e dias vence):**
    - 🟢 Verde:    até 15 usos / até 60 dias  → R$ 40,00
    - 🟡 Amarelo:  até 25 usos / até 80 dias  → R$ 20,00
    - 🔴 Vermelho: até 40 usos / até 90 dias  → R$ 10,00
    - ⚫ Expirado: acima dos limites           → R$ 0,00

    **Parâmetro:**
    - sacola_id: ID da sacola (ex: BAG-00001)

    **Observação:** Após devolução, sacola não pode ser reativada
    """

    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")

    if sacola.status != models.StatusSacola.ativo:
        raise HTTPException(
            status_code=400,
            detail=f"Sacola não está ativa. Status: {sacola.status.value}"
        )

    if sacola.data_vinculacao:
        dias_uso = (datetime.now() - sacola.data_vinculacao).days
    else:
        dias_uso = 0

    estado, desconto = calcular_estado_sacola(sacola.utilizacoes, dias_uso)

    sacola.status = models.StatusSacola.devolvido
    sacola.data_devolucao = datetime.now()

    db.commit()
    db.refresh(sacola)

    # ========== LOG DE AUDITORIA ==========
    try:
        registrar_log(
            db=db,
            usuario=current_user,
            acao="devolver_sacola",
            entidade_tipo="Sacola",
            entidade_id=sacola_id,
            detalhes={
                "sacola_id": sacola_id,
                "utilizacoes": sacola.utilizacoes,
                "dias_de_uso": dias_uso,
                "estado": estado,
                "desconto_concedido": desconto,
                "terminal": getattr(current_user, 'terminal', None)
            },
            ip_address=request.client.host if request.client else None
        )
        db.commit()
    except Exception as e:
        print(f"Erro ao registrar log de auditoria: {e}")

    return {
        "sucesso": True,
        "mensagem": "Sacola devolvida com sucesso",
        "sacola": {
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "dias_de_uso": dias_uso,
            "estado": estado
        },
        "desconto_concedido": desconto
    }


@router.get(
    "/{sacola_id}/historico",
    summary="Histórico de uso da sacola",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def historico_uso(sacola_id: str, db: Session = Depends(get_db)):
    """
    Retorna histórico completo de utilizações de uma sacola.

    **Observação:** Histórico ordenado da mais recente para mais antiga
    """

    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")

    registros = db.query(models.RegistroUso).filter(
        models.RegistroUso.sacola_id == sacola_id
    ).order_by(models.RegistroUso.data_uso.desc()).all()

    historico = []
    total_gasto = 0

    for registro in registros:
        historico.append({
            "data_uso": registro.data_uso,
            "valor_compra": registro.valor_compra
        })
        total_gasto += registro.valor_compra

    valor_medio = total_gasto / len(registros) if registros else 0

    return {
        "sacola_id": sacola_id,
        "total_usos": len(registros),
        "total_gasto": round(total_gasto, 2),
        "valor_medio": round(valor_medio, 2),
        "historico": historico
    }


@router.post(
    "/verificar-qr",
    summary="Verificar QR Code sem ativar",
    dependencies=[Depends(require_role(["caixa", "gerente", "admin"]))]
)
def verificar_qr_code(qr_code: str, db: Session = Depends(get_db)):
    """
    Valida o QR Code sem vincular a sacola ao cliente.

    **Parâmetro:**
    - qr_code: QR Code completo (BAG-00001:2026-03-31:checksum)
    """

    valido, sacola_id, data_criacao, erro = validar_qrcode_checksum(qr_code)

    if not valido:
        return {"valido": False, "erro": erro}

    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()

    if not sacola:
        return {"valido": False, "erro": f"Sacola {sacola_id} não encontrada no sistema"}

    if sacola.checksum != qr_code.split(':')[2]:
        return {"valido": False, "erro": "Checksum não confere com registro do banco"}

    return {
        "valido": True,
        "sacola_id": sacola_id,
        "data_criacao": data_criacao,
        "status": sacola.status.value
    }