"""
Gerador de QR Codes - Lógica reutilizável
Usado por: API REST e Script CLI
"""
import qrcode
import hashlib
import csv
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from io import BytesIO
from typing import Optional, Dict, List


# Caminhos relativos à raiz do projeto
# __file__ está em: services/backend/app/core/qrcode_generator.py
# Subir 5 níveis: qrcode_generator.py -> core -> app -> backend -> services -> RAIZ
current_file = os.path.abspath(__file__)
core_dir = os.path.dirname(current_file)           # app/core/
app_dir = os.path.dirname(core_dir)                # app/
backend_dir = os.path.dirname(app_dir)             # backend/
services_dir = os.path.dirname(backend_dir)        # services/
BASE_DIR = os.path.dirname(services_dir)           # bagplus-loyalty-system/ (RAIZ)

STORAGE_DIR = os.path.join(BASE_DIR, "storage", "qrcodes")
CONTROLE_SEQUENCIA = os.path.join(STORAGE_DIR, "ultimo_id.txt")


def ler_ultimo_id() -> int:
    """
    Lê o último ID gerado do arquivo de controle
    
    Returns:
        int: Último ID usado (0 se arquivo não existe)
    """
    if os.path.exists(CONTROLE_SEQUENCIA):
        with open(CONTROLE_SEQUENCIA, 'r', encoding='utf-8') as f:
            conteudo = f.read().strip()
            return int(conteudo) if conteudo else 0
    return 0


def salvar_ultimo_id(ultimo_id: int) -> None:
    """
    Salva o último ID gerado no arquivo de controle
    
    Args:
        ultimo_id: ID a ser salvo
    """
    os.makedirs(STORAGE_DIR, exist_ok=True)
    with open(CONTROLE_SEQUENCIA, 'w', encoding='utf-8') as f:
        f.write(str(ultimo_id))


def gerar_checksum(sacola_id: str, data_criacao: str, secret_key: str) -> str:
    """
    Gera código de verificação de 6 caracteres
    
    Args:
        sacola_id: ID da sacola (ex: BAG-00001)
        data_criacao: Data no formato YYYY-MM-DD
        secret_key: Chave secreta para hash
        
    Returns:
        str: Checksum de 6 caracteres
    """
    texto = f"{sacola_id}{data_criacao}{secret_key}"
    hash_completo = hashlib.sha256(texto.encode()).hexdigest()
    return hash_completo[:6]


def gerar_qrcode_memoria(conteudo: str):
    """
    Gera QR Code em memória (não salva arquivo)
    
    Args:
        conteudo: Texto a ser codificado no QR Code
        
    Returns:
        PIL.Image: Imagem do QR Code
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(conteudo)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img


def gerar_pdf_grid(
    inicio: int,
    fim: int,
    data_criacao: str,
    secret_key: str,
    output_path: str
) -> str:
    """
    Gera PDF com grid de QR Codes para impressão
    
    Args:
        inicio: ID inicial do lote
        fim: ID final do lote
        data_criacao: Data de criação
        secret_key: Chave secreta
        output_path: Caminho do arquivo PDF
        
    Returns:
        str: Caminho do PDF gerado
    """
    # Configurações do PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    largura, altura = A4
    
    # Configurações do grid
    qr_size = 3 * cm
    cols = 2
    rows = 5
    margin_x = 3 * cm
    margin_y = 2 * cm
    spacing_x = 1 * cm
    spacing_y = 1 * cm
    
    qr_index = 0
    
    for num in range(inicio, fim + 1):
        sacola_id = f"BAG-{num:05d}"
        checksum = gerar_checksum(sacola_id, data_criacao, secret_key)
        conteudo_qr = f"{sacola_id}:{data_criacao}:{checksum}"
        
        # Gerar QR Code em memória
        img_qr = gerar_qrcode_memoria(conteudo_qr)
        
        # Converter para BytesIO para ReportLab
        img_buffer = BytesIO()
        img_qr.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_reader = ImageReader(img_buffer)
        
        # Calcular posição no grid
        page_qr_index = qr_index % (cols * rows)
        
        # Nova página se necessário
        if qr_index > 0 and page_qr_index == 0:
            c.showPage()
        
        col = page_qr_index % cols
        row = page_qr_index // cols
        
        x = margin_x + col * (qr_size + spacing_x)
        y = altura - margin_y - (row + 1) * (qr_size + spacing_y)
        
        # Desenhar QR Code
        c.drawImage(img_reader, x, y, width=qr_size, height=qr_size)
        
        # Desenhar ID
        c.setFont("Helvetica-Bold", 8)
        text_width = c.stringWidth(sacola_id, "Helvetica-Bold", 8)
        c.drawString(x + (qr_size - text_width) / 2, y - 0.4 * cm, sacola_id)
        
        # Desenhar data
        c.setFont("Helvetica", 6)
        text_width = c.stringWidth(data_criacao, "Helvetica", 6)
        c.drawString(x + (qr_size - text_width) / 2, y - 0.7 * cm, data_criacao)
        
        qr_index += 1
    
    c.save()
    return output_path


def gerar_lote_qrcodes(
    quantidade: int,
    secret_key: str,
    data_criacao: Optional[str] = None,
    formatos: List[str] = ["csv", "pdf"]
) -> Dict:
    """
    Gera lote de QR Codes (CSV e/ou PDF)
    
    Função principal reutilizável para API e CLI
    
    Args:
        quantidade: Número de QR Codes a gerar
        secret_key: Chave secreta do sistema
        data_criacao: Data de criação (YYYY-MM-DD). Default: hoje
        formatos: Lista de formatos ['csv', 'pdf']. Default: ambos
        
    Returns:
        Dict com informações do lote gerado:
        {
            "sucesso": bool,
            "quantidade": int,
            "inicio": int,
            "fim": int,
            "intervalo": str,
            "data_criacao": str,
            "arquivos": {
                "csv": str | None,
                "pdf": str | None
            },
            "sacolas": List[Dict]  # Dados das sacolas geradas
        }
    """
    # Validações
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero")
    
    if quantidade > 10000:
        raise ValueError("Quantidade máxima: 10.000 por lote")
    
    if not secret_key:
        raise ValueError("SECRET_KEY não fornecida")
    
    # Data padrão: hoje
    if not data_criacao:
        data_criacao = datetime.now().strftime('%Y-%m-%d')
    
    # Validar formatos
    formatos_validos = ["csv", "pdf"]
    formatos = [f.lower() for f in formatos if f.lower() in formatos_validos]
    if not formatos:
        formatos = ["csv", "pdf"]
    
    # Ler último ID usado
    ultimo_id = ler_ultimo_id()
    inicio = ultimo_id + 1
    fim = inicio + quantidade - 1
    
    # Criar estrutura de pastas
    csv_dir = os.path.join(STORAGE_DIR, "csv")
    pdf_dir = os.path.join(STORAGE_DIR, "pdf")
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Lista de sacolas
    sacolas = []
    
    # Gerar dados
    for num in range(inicio, fim + 1):
        sacola_id = f"BAG-{num:05d}"
        checksum = gerar_checksum(sacola_id, data_criacao, secret_key)
        conteudo_qr = f"{sacola_id}:{data_criacao}:{checksum}"
        
        sacolas.append({
            "id": sacola_id,
            "data_criacao": data_criacao,
            "checksum": checksum,
            "qr_content": conteudo_qr
        })
    
    # Caminhos dos arquivos
    nome_lote = f"lote_{inicio:05d}-{fim:05d}"
    arquivos_gerados = {}
    
    # Gerar CSV
    if "csv" in formatos:
        csv_path = os.path.join(csv_dir, f"{nome_lote}.csv")
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'data_criacao', 'checksum', 'qr_content'])
            writer.writeheader()
            writer.writerows(sacolas)
        arquivos_gerados["csv"] = csv_path
    else:
        arquivos_gerados["csv"] = None
    
    # Gerar PDF
    if "pdf" in formatos:
        pdf_path = os.path.join(pdf_dir, f"{nome_lote}_IMPRESSAO.pdf")
        gerar_pdf_grid(inicio, fim, data_criacao, secret_key, pdf_path)
        arquivos_gerados["pdf"] = pdf_path
    else:
        arquivos_gerados["pdf"] = None
    
    # Atualizar controle de sequência
    salvar_ultimo_id(fim)
    
    return {
        "sucesso": True,
        "quantidade": quantidade,
        "inicio": inicio,
        "fim": fim,
        "intervalo": f"BAG-{inicio:05d} até BAG-{fim:05d}",
        "data_criacao": data_criacao,
        "arquivos": arquivos_gerados,
        "sacolas": sacolas
    }