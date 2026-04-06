"""
Utilitários do sistema Bag+
"""
from .helpers import (
    validar_qrcode_checksum,
    detectar_valores_diferentes_mesmo_dia,
    detectar_valor_repetido_dias_diferentes,
    detectar_abuso_valor_minimo,
    calcular_desconto_fidelidade
)

__all__ = [
    "validar_qrcode_checksum",
    "detectar_valores_diferentes_mesmo_dia",
    "detectar_valor_repetido_dias_diferentes",
    "detectar_abuso_valor_minimo",
    "calcular_desconto_fidelidade"
]