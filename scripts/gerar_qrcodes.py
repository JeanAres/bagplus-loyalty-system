import qrcode
import hashlib
import csv
import os
from datetime import datetime
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from io import BytesIO

load_dotenv('../backend/.env')

SECRET_KEY = os.getenv('SECRET_KEY')

if not SECRET_KEY:
    raise Exception("ERRO: SECRET_KEY não encontrada no arquivo .env")

# Arquivo de controle de sequência
CONTROLE_SEQUENCIA = '../qrcodes/ultimo_id.txt'

def ler_ultimo_id():
    """Lê o último ID gerado do arquivo de controle"""
    if os.path.exists(CONTROLE_SEQUENCIA):
        with open(CONTROLE_SEQUENCIA, 'r', encoding='utf-8') as f:
            return int(f.read().strip())
    return 0

def salvar_ultimo_id(ultimo_id):
    """Salva o último ID gerado no arquivo de controle"""
    os.makedirs('../qrcodes', exist_ok=True)
    with open(CONTROLE_SEQUENCIA, 'w', encoding='utf-8') as f:
        f.write(str(ultimo_id))

def gerar_checksum(sacola_id, data_criacao):
    """Gera código de verificação de 6 caracteres baseado em ID + Data + SECRET_KEY"""
    texto = f"{sacola_id}{data_criacao}{SECRET_KEY}"
    hash_completo = hashlib.sha256(texto.encode()).hexdigest()
    return hash_completo[:6]

def gerar_qrcode_memoria(conteudo):
    """Gera QR Code em memória (não salva arquivo)"""
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

def gerar_pdf_grid(inicio, fim, data_criacao):
    """Gera PDF com grid de QR Codes direto da memória (sem arquivos PNG)"""
    
    pdf_path = f"../qrcodes/lote_{inicio:05d}-{fim:05d}_IMPRESSAO.pdf"
    
    # Configurações do PDF
    c = canvas.Canvas(pdf_path, pagesize=A4)
    largura, altura = A4
    
    # Configurações do grid
    qr_size = 3 * cm  # 3cm x 3cm
    cols = 2
    rows = 5
    margin_x = 3 * cm
    margin_y = 2 * cm
    spacing_x = 1 * cm
    spacing_y = 1 * cm
    
    qr_index = 0
    total_qrs = fim - inicio + 1
    
    print(f"\nGerando PDF para impressão...")
    
    for num in range(inicio, fim + 1):
        sacola_id = f"BAG-{num:05d}"
        checksum = gerar_checksum(sacola_id, data_criacao)
        conteudo_qr = f"{sacola_id}:{data_criacao}:{checksum}"
        
        # Gerar QR Code em memória (não salva arquivo)
        img_qr = gerar_qrcode_memoria(conteudo_qr)
        
        # Converter PIL Image para BytesIO para ReportLab usar
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
        
        # Desenhar ID abaixo do QR Code
        c.setFont("Helvetica-Bold", 8)
        text_width = c.stringWidth(sacola_id, "Helvetica-Bold", 8)
        c.drawString(x + (qr_size - text_width) / 2, y - 0.4 * cm, sacola_id)
        
        # Desenhar data (menor)
        c.setFont("Helvetica", 6)
        text_width = c.stringWidth(data_criacao, "Helvetica", 6)
        c.drawString(x + (qr_size - text_width) / 2, y - 0.7 * cm, data_criacao)
        
        qr_index += 1
    
    c.save()
    print(f"PDF gerado: {pdf_path}")
    print(f"Total de páginas: {(total_qrs + (cols * rows) - 1) // (cols * rows)}")

def gerar_lote(quantidade, data_criacao=None):
    """Gera lote de QR Codes (CSV + PDF, sem PNGs individuais)"""
    
    # Se não passar data, usa data de hoje
    if not data_criacao:
        data_criacao = datetime.now().strftime('%Y-%m-%d')
    
    # Ler último ID usado
    ultimo_id = ler_ultimo_id()
    inicio = ultimo_id + 1
    fim = inicio + quantidade - 1
    
    # Criar pastas se não existirem
    os.makedirs("../qrcodes", exist_ok=True)
    
    # Lista para CSV
    sacolas = []
    
    print(f"\n{'='*60}")
    print(f"GERAÇÃO DE LOTE DE QR CODES")
    print(f"{'='*60}")
    print(f"Último ID gerado anteriormente: BAG-{ultimo_id:05d}")
    print(f"Novo lote: BAG-{inicio:05d} até BAG-{fim:05d}")
    print(f"Quantidade: {quantidade} sacolas")
    print(f"Data de criação: {data_criacao}")
    print(f"{'='*60}\n")
    
    # Confirmação de segurança
    resposta = input("Confirma geração? (S/N): ").strip().upper()
    if resposta != 'S':
        print("\nGeração cancelada pelo usuário.")
        return
    
    print()
    print("Processando QR Codes...")
    
    for num in range(inicio, fim + 1):
        sacola_id = f"BAG-{num:05d}"
        checksum = gerar_checksum(sacola_id, data_criacao)
        
        # Formato: BAG-00001:2026-03-31:a3f9d2
        conteudo_qr = f"{sacola_id}:{data_criacao}:{checksum}"

        # Adicionar à lista CSV
        sacolas.append({
            "id": sacola_id,
            "data_criacao": data_criacao,
            "checksum": checksum,
            "qr_content": conteudo_qr
        })
        
        # Mostrar progresso a cada 100
        if num % 100 == 0 or num == fim:
            print(f"✅ Processado até: {sacola_id}")
    
    # Salvar CSV
    csv_path = f"../qrcodes/lote_{inicio:05d}-{fim:05d}.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'data_criacao', 'checksum', 'qr_content'])
        writer.writeheader()
        writer.writerows(sacolas)
    
    print(f"\n✅ CSV gerado: {csv_path}")
    
    # Gerar PDF para impressão (QR Codes direto da memória)
    gerar_pdf_grid(inicio, fim, data_criacao)
    
    # Atualizar controle de sequência
    salvar_ultimo_id(fim)
    
    print(f"\n{'='*60}")
    print(f"Controle atualizado: último ID = BAG-{fim:05d}")
    print(f"\nCONCLUÍDO! {len(sacolas)} QR Codes processados com sucesso!")
    print(f"Localização: ../qrcodes/")
    print(f"\nArquivos gerados:")
    print(f"   - CSV com dados: lote_{inicio:05d}-{fim:05d}.csv")
    print(f"   - PDF para gráfica: lote_{inicio:05d}-{fim:05d}_IMPRESSAO.pdf")
    print(f"   - Controle de ID: ultimo_id.txt")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    print("\nGERADOR DE QR CODES - BAG+ SYSTEM")
    print("IDs são sequenciais e NUNCA se repetem!")
    print("Versão otimizada: Gera apenas CSV + PDF (sem PNGs individuais)\n")
    
    gerar_lote(quantidade=5)
    
    # Para gerar com data específica:
    # gerar_lote(quantidade=5, data_criacao='2026-03-01')