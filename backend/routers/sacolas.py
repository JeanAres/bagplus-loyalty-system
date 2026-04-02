"""
Endpoints relacionados a sacolas
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime, timedelta
import models
from utils import (
    validar_qrcode_checksum,
    calcular_desconto_fidelidade,
    detectar_valores_diferentes_mesmo_dia,
    detectar_valor_repetido_dias_diferentes,
    detectar_abuso_valor_minimo
)

router = APIRouter(
    prefix="/api/sacolas",
    tags=["Sacolas"]
)


@router.get(
    "/{sacola_id}",
    summary="Buscar informações da sacola",
    description="""
    Retorna todas as informações de uma sacola específica.
    
    **Informações retornadas:**
    - Dados básicos (ID, status, utilizações)
    - Cliente vinculado (se houver)
    - Descontos disponíveis (fidelidade e devolução)
    - Estado da sacola (verde/amarelo/vermelho)
    - Tempo desde última utilização
    
    **Quando usar:** 
    - Sistema de caixa ao escanear QR Code
    - Consulta de status de sacola
    
    **Estados da sacola:**
    - 🟢 Verde: 0-15 usos, até 60 dias (desconto R$ 40,00)
    - 🟡 Amarelo: 16-25 usos, até 80 dias (desconto R$ 20,00)
    - 🔴 Vermelho: 26-40 usos, até 90 dias (desconto R$ 10,00)
    """
)
def buscar_sacola(sacola_id: str, db: Session = Depends(get_db)):
    """Busca informações completas de uma sacola"""
    
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    # Cliente vinculado
    cliente_info = None
    if sacola.cliente_cpf:
        cliente = db.query(models.Cliente).filter(models.Cliente.cpf == sacola.cliente_cpf).first()
        if cliente:
            cliente_info = {
                "cpf": cliente.cpf,
                "nome": cliente.nome
            }
    
    # Calcular desconto por fidelidade
    fidelidade = calcular_desconto_fidelidade(sacola.utilizacoes)
    
    # Calcular estado e desconto por devolução
    if sacola.data_vinculacao:
        dias_uso = (datetime.now() - sacola.data_vinculacao).days
    else:
        dias_uso = 0
    
    if sacola.utilizacoes <= 15 and dias_uso <= 60:
        estado = "verde"
        desconto_devolucao = 40.00
    elif sacola.utilizacoes <= 25 and dias_uso <= 80:
        estado = "amarelo"
        desconto_devolucao = 20.00
    elif sacola.utilizacoes <= 40 and dias_uso <= 90:
        estado = "vermelho"
        desconto_devolucao = 10.00
    else:
        estado = "expirado"
        desconto_devolucao = 0.00
    
    # Tempo desde última utilização
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
    description="""
    Vincula uma sacola a um cliente através do QR Code.
    
    **Uso principal:** Sistema de caixa com leitora de QR Code (pistolinha)
    
    **Validações aplicadas:**
    -  QR Code deve ter formato válido (BAG-00001:2026-03-31:checksum)
    -  Checksum SHA256 deve ser válido (anti-falsificação)
    -  Sacola deve existir no sistema (lote importado)
    -  Sacola deve estar em status "estoque"
    -  Cliente deve existir e estar ativo
    -  Cliente não pode estar suspenso
    
    **Parâmetros:**
    - qr_code: QR Code completo lido pela pistolinha
    - cpf_cliente: CPF do cliente (11 dígitos)
    
    **Observação:** Para vincular múltiplas sacolas de uma vez (testes), use /ativar-lote
    """
)
def ativar_sacola(qr_code: str, cpf_cliente: str, db: Session = Depends(get_db)):
    """Ativa uma sacola vinculando ao cliente"""
    
    # Validar QR Code
    valido, sacola_id, data_criacao, erro = validar_qrcode_checksum(qr_code)
    if not valido:
        raise HTTPException(status_code=400, detail=erro)
    
    # Buscar sacola
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(
            status_code=404,
            detail=f"Sacola {sacola_id} não encontrada. Verifique se o lote foi importado."
        )
    
    # Validar checksum do banco
    if sacola.checksum != qr_code.split(':')[2]:
        raise HTTPException(
            status_code=400,
            detail="Checksum não confere com registro do banco. QR Code pode estar adulterado."
        )
    
    # Verificar status da sacola
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
    
    # Verificar se cliente existe
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_cliente).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com CPF {cpf_cliente} não encontrado. Cadastre o cliente primeiro."
        )
    
    # Verificar se cliente está suspenso
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
    
    # Ativar sacola
    sacola.status = models.StatusSacola.ativo
    sacola.cliente_cpf = cpf_cliente
    sacola.data_vinculacao = datetime.now()
    
    db.commit()
    db.refresh(sacola)
    
    return {
        "sucesso": True,
        "mensagem": f"Sacola {sacola_id} ativada com sucesso",
        "sacola": {
            "id": sacola.id,
            "status": sacola.status.value
        },
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome
        }
    }


@router.post(
    "/ativar-lote",
    summary="Ativar múltiplas sacolas (lote)",
    description="""
    Vincula múltiplas sacolas a um cliente de uma só vez.
    
    **USO: Apenas para TESTES**
    - Produção: use /ativar com pistolinha (uma por uma)
    - Testes: facilita vincular várias sacolas rapidamente
    
    **Comportamento:**
    - Valida TODAS as sacolas (mesmo processo do /ativar)
    - Vincula as que estão válidas
    - Retorna lista de sucessos e erros
    - Se uma falhar, outras continuam (não é tudo-ou-nada)
    
    **Parâmetros:**
    - qr_codes: Array de QR Codes completos
    - cpf_cliente: CPF do cliente
    
    **Exemplo de uso:**
```json
    {
      "qr_codes": [
        "BAG-00001:2026-03-31:abc123",
        "BAG-00002:2026-03-31:def456",
        "BAG-00003:2026-03-31:ghi789"
      ],
      "cpf_cliente": "12345678900"
    }
```
    """
)
def ativar_sacolas_lote(
    qr_codes: list[str],
    cpf_cliente: str,
    db: Session = Depends(get_db)
):
    """Ativa múltiplas sacolas de uma vez (testes)"""
    
    # Verificar se cliente existe
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_cliente).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com CPF {cpf_cliente} não encontrado. Cadastre o cliente primeiro."
        )
    
    # Verificar se cliente está suspenso
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
    
    # Processar cada QR Code
    for qr_code in qr_codes:
        try:
            # Validar QR Code
            valido, sacola_id, data_criacao, erro = validar_qrcode_checksum(qr_code)
            
            if not valido:
                erros.append({
                    "qr_code": qr_code,
                    "erro": erro
                })
                continue
            
            # Buscar sacola
            sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
            if not sacola:
                erros.append({
                    "qr_code": qr_code,
                    "erro": f"Sacola {sacola_id} não encontrada no sistema. Verifique se o lote foi importado."
                })
                continue
            
            # Validar checksum do banco
            if sacola.checksum != qr_code.split(':')[2]:
                erros.append({
                    "qr_code": qr_code,
                    "erro": "Checksum não confere com registro do banco. QR Code pode estar adulterado."
                })
                continue
            
            # Verificar status
            if sacola.status != models.StatusSacola.estoque:
                if sacola.status == models.StatusSacola.ativo:
                    cliente_atual = db.query(models.Cliente).filter(
                        models.Cliente.cpf == sacola.cliente_cpf
                    ).first()
                    erros.append({
                        "qr_code": qr_code,
                        "erro": f"Sacola já está vinculada ao cliente {cliente_atual.nome} (CPF: {cliente_atual.cpf})"
                    })
                    continue
                elif sacola.status == models.StatusSacola.devolvido:
                    erros.append({
                        "qr_code": qr_code,
                        "erro": "Sacola já foi devolvida e não pode ser reativada"
                    })
                    continue
            
            # Ativar sacola
            sacola.status = models.StatusSacola.ativo
            sacola.cliente_cpf = cpf_cliente
            sacola.data_vinculacao = datetime.now()
            
            vinculadas.append(sacola_id)
            
        except Exception as e:
            erros.append({
                "qr_code": qr_code,
                "erro": f"Erro inesperado: {str(e)}"
            })
    
    # Commit todas vinculações
    db.commit()
    
    # Preparar resposta
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
            "cliente": {
                "cpf": cliente.cpf,
                "nome": cliente.nome
            }
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
            "cliente": {
                "cpf": cliente.cpf,
                "nome": cliente.nome
            }
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
    description="""
    Registra uma nova utilização da sacola com valor da compra.
    
    **Validações aplicadas:**
    -  Sacola deve existir
    -  Sacola deve estar ativa (vinculada a cliente)
    -  Intervalo mínimo de 4 horas desde último uso
    -  Valor mínimo de R$ 15,00
    -  Cliente não pode estar suspenso
    -  Máximo 40 utilizações por sacola
    
    **Detecções automáticas executadas:**
    -  Valores diferentes no mesmo dia (rancho suspeito)
    -  Sempre mesmo valor em dias diferentes
    -  Abuso de valor mínimo (muitas sacolas com R$ 15,00)
    
    **Parâmetros:**
    - sacola_id: ID da sacola (ex: BAG-00001)
    - valor_compra: Valor da compra (aceita vírgula ou ponto)
    
    **Observação:** Aceita formatos: 125.50 ou 125,50
    """
)
def registrar_uso(
    sacola_id: str,
    valor_compra: str,
    db: Session = Depends(get_db)
):
    """Registra uso da sacola com valor da compra"""
    
    # Buscar sacola
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    # Verificar se está ativa
    if sacola.status != models.StatusSacola.ativo:
        raise HTTPException(
            status_code=400,
            detail=f"Sacola não está ativa. Status atual: {sacola.status.value}"
        )
    
    # Validar intervalo de 4 horas
    if sacola.ultima_utilizacao:
        tempo_desde_ultimo = datetime.now() - sacola.ultima_utilizacao
        if tempo_desde_ultimo < timedelta(hours=4):
            horas_restantes = 4 - (tempo_desde_ultimo.total_seconds() / 3600)
            raise HTTPException(
                status_code=400,
                detail=f"Intervalo mínimo não atingido. Aguarde {horas_restantes:.1f} horas"
            )
    
    # Converter e validar valor
    try:
        valor_str = valor_compra.replace(',', '.')
        valor_float = float(valor_str)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="Valor da compra inválido. Use formato: 120.50 ou 120,50"
        )
    
    if valor_float < 0:
        raise HTTPException(status_code=400, detail="Valor da compra não pode ser negativo")
    
    # Validar valor mínimo
    if valor_float < 15.00:
        raise HTTPException(status_code=400, detail="Valor mínimo de compra: R$ 15,00")
    
    # Verificar se cliente está suspenso
    cliente = db.query(models.Cliente).filter(
        models.Cliente.cpf == sacola.cliente_cpf
    ).first()
    
    if cliente.status_beneficios != models.StatusBeneficios.ativo:
        raise HTTPException(
            status_code=403,
            detail=f"Cliente suspenso. Não pode utilizar sacolas. Motivo: {cliente.motivo_suspensao}"
        )
    
    # Verificar limite de 40 usos
    if sacola.utilizacoes >= 40:
        raise HTTPException(
            status_code=400,
            detail="Sacola atingiu limite máximo de 40 utilizações. Devolva a sacola."
        )
    
    # Registrar uso
    registro = models.RegistroUso(
        sacola_id=sacola_id,
        valor_compra=valor_float
    )
    db.add(registro)
    
    # Atualizar sacola
    sacola.utilizacoes += 1
    sacola.ultima_utilizacao = datetime.now()
    
    db.commit()
    db.refresh(sacola)
    
    # Executar detecções de padrões suspeitos
    try:
        detectar_valores_diferentes_mesmo_dia(sacola.cliente_cpf, db)
        detectar_valor_repetido_dias_diferentes(sacola.cliente_cpf, db)
        detectar_abuso_valor_minimo(sacola.cliente_cpf, db)
    except Exception as e:
        print(f"Erro na detecção de padrões: {e}")
    
    # Calcular desconto por fidelidade
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
    description="""
    Processa a devolução de uma sacola e calcula desconto.
    
    **Cálculo de desconto baseado no estado:**
    - 🟢 Verde (0-15 usos, até 60 dias): R$ 40,00
    - 🟡 Amarelo (16-25 usos, até 80 dias): R$ 20,00
    - 🔴 Vermelho (26-40 usos, até 90 dias): R$ 10,00
    - ⚫ Fora do prazo: R$ 0,00
    
    **Validações:**
    - Sacola deve estar ativa
    - Desconto calculado automaticamente
    
    **Parâmetro:**
    - sacola_id: ID da sacola (ex: BAG-00001)
    
    **Observação:** Após devolução, sacola não pode ser reativada
    """
)
def devolver_sacola(sacola_id: str, db: Session = Depends(get_db)):
    """Processa devolução da sacola"""
    
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    if sacola.status != models.StatusSacola.ativo:
        raise HTTPException(
            status_code=400,
            detail=f"Sacola não está ativa. Status: {sacola.status.value}"
        )
    
    # Calcular desconto
    if sacola.data_vinculacao:
        dias_uso = (datetime.now() - sacola.data_vinculacao).days
    else:
        dias_uso = 0
    
    if sacola.utilizacoes <= 15 and dias_uso <= 60:
        estado = "verde"
        desconto = 40.00
    elif sacola.utilizacoes <= 25 and dias_uso <= 80:
        estado = "amarelo"
        desconto = 20.00
    elif sacola.utilizacoes <= 40 and dias_uso <= 90:
        estado = "vermelho"
        desconto = 10.00
    else:
        estado = "expirado"
        desconto = 0.00
    
    # Processar devolução
    sacola.status = models.StatusSacola.devolvido
    sacola.data_devolucao = datetime.now()
    
    db.commit()
    db.refresh(sacola)
    
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
    description="""
    Retorna histórico completo de utilizações de uma sacola.
    
    **Informações retornadas:**
    - Lista de todos os usos com data e valor
    - Total gasto usando esta sacola
    - Valor médio por compra
    - Data da primeira e última utilização
    
    **Quando usar:** 
    - Auditoria de uso
    - Análise de padrão de compras
    - Suporte ao cliente
    
    **Observação:** Histórico ordenado da mais recente para mais antiga
    """
)
def historico_uso(sacola_id: str, db: Session = Depends(get_db)):
    """Retorna histórico de uso da sacola"""
    
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