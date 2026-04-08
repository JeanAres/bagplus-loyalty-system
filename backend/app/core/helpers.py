"""
Funções auxiliares compartilhadas
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db import models
import os
import hashlib


def validar_qrcode_checksum(qr_code: str):
    """
    Valida formato e checksum de um QR Code
    
    Retorna: (valido: bool, sacola_id: str, data_criacao: str, erro: str)
    """
    
    # 1. VALIDAR FORMATO
    partes = qr_code.split(':')
    if len(partes) != 3:
        return False, None, None, "Formato inválido. Esperado: BAG-00001:2026-03-31:abc123"
    
    sacola_id = partes[0]
    data_criacao = partes[1]
    checksum_recebido = partes[2]
    
    # 2. VALIDAR ID
    if not sacola_id.startswith('BAG-'):
        return False, None, None, "ID deve começar com BAG-"
    
    try:
        numero = int(sacola_id.split('-')[1])
        if numero < 1:
            return False, None, None, "Número do ID inválido"
    except:
        return False, None, None, "Formato de ID inválido"
    
    # 3. VALIDAR DATA
    try:
        datetime.strptime(data_criacao, '%Y-%m-%d')
    except:
        return False, None, None, "Data inválida. Formato esperado: AAAA-MM-DD"
    
    # 4. VALIDAR CHECKSUM
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        return False, None, None, "Erro de configuração do servidor"
    
    texto = f"{sacola_id}{data_criacao}{SECRET_KEY}"
    hash_completo = hashlib.sha256(texto.encode()).hexdigest()
    checksum_correto = hash_completo[:6]
    
    if checksum_recebido != checksum_correto:
        return False, None, None, "QR Code inválido ou falsificado"
    
    # TUDO VÁLIDO
    return True, sacola_id, data_criacao, None


def detectar_valores_diferentes_mesmo_dia(cliente_cpf: str, db: Session):
    """
    Detecta uso de múltiplas sacolas com valores diferentes no mesmo dia
    """
    hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    registros_hoje = db.query(models.RegistroUso).join(
        models.Sacola
    ).filter(
        models.Sacola.cliente_cpf == cliente_cpf,
        models.RegistroUso.data_uso >= hoje_inicio
    ).all()
    
    if len(registros_hoje) < 4:
        return
    
    valores = [r.valor_compra for r in registros_hoje]
    valores_unicos = len(set(valores))
    
    if valores_unicos > 2:
        alerta_existe = db.query(models.Alerta).filter(
            models.Alerta.cliente_cpf == cliente_cpf,
            models.Alerta.tipo == models.TipoAlerta.valores_diferentes_mesmo_dia,
            models.Alerta.data_deteccao >= hoje_inicio,
            models.Alerta.resolvido == False
        ).first()
        
        if not alerta_existe:
            alerta = models.Alerta(
                tipo=models.TipoAlerta.valores_diferentes_mesmo_dia,
                gravidade=models.GravidadeAlerta.alta,
                cliente_cpf=cliente_cpf,
                descricao=f"Cliente usou {len(registros_hoje)} sacolas hoje com {valores_unicos} valores diferentes (esperado: valor único em rancho)"
            )
            db.add(alerta)
            db.commit()


def detectar_valor_repetido_dias_diferentes(cliente_cpf: str, db: Session):
    """
    Detecta se cliente sempre compra mesmo valor em dias separados
    """
    trinta_dias_atras = datetime.now() - timedelta(days=30)
    
    registros = db.query(models.RegistroUso).join(
        models.Sacola
    ).filter(
        models.Sacola.cliente_cpf == cliente_cpf,
        models.RegistroUso.data_uso >= trinta_dias_atras
    ).all()
    
    if len(registros) < 10:
        return
    
    usos_por_dia = {}
    for r in registros:
        dia = r.data_uso.date()
        if dia not in usos_por_dia:
            usos_por_dia[dia] = []
        usos_por_dia[dia].append(r.valor_compra)
    
    if len(usos_por_dia) < 5:
        return
    
    valores_por_dia = []
    for dia, valores in usos_por_dia.items():
        valor_mais_comum = max(set(valores), key=valores.count)
        valores_por_dia.append(valor_mais_comum)
    
    valor_mais_comum_geral = max(set(valores_por_dia), key=valores_por_dia.count)
    repeticoes = valores_por_dia.count(valor_mais_comum_geral)
    percentual = (repeticoes / len(valores_por_dia)) * 100
    
    if percentual >= 80:
        alerta_existe = db.query(models.Alerta).filter(
            models.Alerta.cliente_cpf == cliente_cpf,
            models.Alerta.tipo == models.TipoAlerta.valor_repetido_dias_diferentes,
            models.Alerta.resolvido == False
        ).first()
        
        if not alerta_existe:
            alerta = models.Alerta(
                tipo=models.TipoAlerta.valor_repetido_dias_diferentes,
                gravidade=models.GravidadeAlerta.media,
                cliente_cpf=cliente_cpf,
                descricao=f"Cliente compra sempre R$ {valor_mais_comum_geral:.2f} em {repeticoes} de {len(valores_por_dia)} dias diferentes (últimos 30 dias)"
            )
            db.add(alerta)
            db.commit()


def detectar_abuso_valor_minimo(cliente_cpf: str, db: Session):
    """
    Detecta uso excessivo com valor mínimo
    """
    hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    registros_hoje = db.query(models.RegistroUso).join(
        models.Sacola
    ).filter(
        models.Sacola.cliente_cpf == cliente_cpf,
        models.RegistroUso.data_uso >= hoje_inicio
    ).all()
    
    if len(registros_hoje) < 8:
        return
    
    valores_minimos = [r for r in registros_hoje if r.valor_compra == 15.00]
    percentual_minimo = (len(valores_minimos) / len(registros_hoje)) * 100
    
    if percentual_minimo >= 90:
        alerta_existe = db.query(models.Alerta).filter(
            models.Alerta.cliente_cpf == cliente_cpf,
            models.Alerta.tipo == models.TipoAlerta.abuso_valor_minimo,
            models.Alerta.data_deteccao >= hoje_inicio,
            models.Alerta.resolvido == False
        ).first()
        
        if not alerta_existe:
            alerta = models.Alerta(
                tipo=models.TipoAlerta.abuso_valor_minimo,
                gravidade=models.GravidadeAlerta.alta,
                cliente_cpf=cliente_cpf,
                descricao=f"Cliente usou {len(registros_hoje)} sacolas hoje, {len(valores_minimos)} com valor mínimo R$ 15,00 (possível fraude)"
            )
            db.add(alerta)
            db.commit()


def calcular_desconto_fidelidade(utilizacoes: int):
    """
    Calcula desconto por fidelidade baseado em marcos
    """
    MARCOS_FIDELIDADE = {
        10: 5.00,
        20: 10.00,
        30: 15.00,
        40: 20.00
    }
    
    desconto_acumulado = 0
    proximo_marco = None
    proximo_desconto = 0
    usos_para_proximo = 0
    
    for marco, valor_desconto in sorted(MARCOS_FIDELIDADE.items()):
        if utilizacoes >= marco:
            desconto_acumulado = valor_desconto
        elif proximo_marco is None:
            proximo_marco = marco
            proximo_desconto = valor_desconto
            usos_para_proximo = marco - utilizacoes
            break
    
    return {
        "desconto_atual": desconto_acumulado,
        "proximo_marco": proximo_marco,
        "proximo_desconto": proximo_desconto,
        "usos_para_proximo": usos_para_proximo
    }