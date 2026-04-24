"""
Validações e sanitização de inputs
"""
import bleach
import re
from typing import Optional
from fastapi import HTTPException


def sanitize_string(text: str, max_length: int = 500) -> str:
    """
    Remove HTML, JavaScript e caracteres perigosos.
    
    Args:
        text: String a ser sanitizada
        max_length: Comprimento máximo permitido
    
    Returns:
        String sanitizada e segura
    
    Raises:
        HTTPException: Se texto exceder max_length
    """
    if not text:
        return ""
    
    # Remover HTML/JS
    cleaned = bleach.clean(text, tags=[], strip=True)
    
    # Remover espaços extras
    cleaned = " ".join(cleaned.split())
    
    # Validar comprimento
    if len(cleaned) > max_length:
        raise HTTPException(
            status_code=400,
            detail=f"Texto excede tamanho máximo de {max_length} caracteres"
        )
    
    return cleaned.strip()


def validar_cpf_formato(cpf: str) -> str:
    """
    Valida formato do CPF e retorna apenas números.
    
    Args:
        cpf: CPF com ou sem formatação
    
    Returns:
        CPF com apenas números (11 dígitos)
    
    Raises:
        HTTPException: Se CPF inválido
    """
    if not cpf:
        raise HTTPException(status_code=400, detail="CPF é obrigatório")
    
    # Remover caracteres não numéricos
    cpf_numeros = re.sub(r'\D', '', cpf)
    
    # Validar comprimento
    if len(cpf_numeros) != 11:
        raise HTTPException(
            status_code=400,
            detail="CPF deve ter exatamente 11 dígitos"
        )
    
    # Validar se não são todos iguais (ex: 111.111.111-11)
    if cpf_numeros == cpf_numeros[0] * 11:
        raise HTTPException(
            status_code=400,
            detail="CPF inválido (todos dígitos iguais)"
        )
    
    return cpf_numeros


def validar_valor_monetario(valor: str) -> float:
    """
    Valida e converte valor monetário.
    
    Aceita formatos: 125.50, 125,50, R$ 125.50
    
    Args:
        valor: String com valor monetário
    
    Returns:
        Float com valor convertido
    
    Raises:
        HTTPException: Se valor inválido ou negativo
    """
    if not valor:
        raise HTTPException(status_code=400, detail="Valor é obrigatório")
    
    # Remover R$, espaços
    valor_limpo = valor.replace('R$', '').replace(' ', '')
    
    # Trocar vírgula por ponto
    valor_limpo = valor_limpo.replace(',', '.')
    
    # Validar formato numérico
    try:
        valor_float = float(valor_limpo)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Valor inválido. Use formato: 120.50 ou 120,50"
        )
    
    # Validar se positivo
    if valor_float < 0:
        raise HTTPException(
            status_code=400,
            detail="Valor não pode ser negativo"
        )
    
    # Arredondar para 2 casas decimais
    return round(valor_float, 2)


def validar_nome(nome: str, min_length: int = 3, max_length: int = 100) -> str:
    """
    Valida e sanitiza nome de pessoa.
    
    Args:
        nome: Nome a ser validado
        min_length: Comprimento mínimo
        max_length: Comprimento máximo
    
    Returns:
        Nome sanitizado e validado
    
    Raises:
        HTTPException: Se nome inválido
    """
    # Sanitizar
    nome_limpo = sanitize_string(nome, max_length)
    
    # Validar comprimento mínimo
    if len(nome_limpo) < min_length:
        raise HTTPException(
            status_code=400,
            detail=f"Nome deve ter pelo menos {min_length} caracteres"
        )
    
    # Validar caracteres (letras, espaços, acentos, hífens)
    if not re.match(r'^[a-zA-ZÀ-ÿ\s\-\']+$', nome_limpo):
        raise HTTPException(
            status_code=400,
            detail="Nome contém caracteres inválidos"
        )
    
    return nome_limpo