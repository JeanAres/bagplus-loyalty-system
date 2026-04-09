import os
import shutil

ARQUIVO_PROTEGIDO = 'ultimo_id.txt'

def limpar_qrcodes():
    """Limpa pasta de QR Codes mantendo controle de sequência"""
    
    pasta_base = '../../storage/qrcodes'
    pasta_csv = os.path.join(pasta_base, 'csv')
    pasta_pdf = os.path.join(pasta_base, 'pdf')
    
    if not os.path.exists(pasta_base):
        print(f"\nPasta {pasta_base} não existe!")
        return
    
    # Listar arquivos que serão deletados
    arquivos_csv = []
    arquivos_pdf = []
    
    # CSV
    if os.path.exists(pasta_csv):
        for item in os.listdir(pasta_csv):
            caminho_completo = os.path.join(pasta_csv, item)
            if os.path.isfile(caminho_completo):
                arquivos_csv.append(item)
    
    # PDF
    if os.path.exists(pasta_pdf):
        for item in os.listdir(pasta_pdf):
            caminho_completo = os.path.join(pasta_pdf, item)
            if os.path.isfile(caminho_completo):
                arquivos_pdf.append(item)
    
    total_arquivos = len(arquivos_csv) + len(arquivos_pdf)
    
    if total_arquivos == 0:
        print("\nPastas já estão vazias!")
        return
    
    # Mostrar o que será deletado
    print(f"\n{'='*60}")
    print("LIMPEZA DE QR CODES")
    print(f"{'='*60}")
    print(f"Pasta base: {pasta_base}")
    print(f"Protegido: {ARQUIVO_PROTEGIDO} (será mantido)")
    print(f"\nArquivos que serão DELETADOS ({total_arquivos}):")
    print(f"{'='*60}")
    
    if arquivos_csv:
        print(f"\nCSV ({len(arquivos_csv)}):")
        for f in arquivos_csv:
            print(f"   - csv/{f}")
    
    if arquivos_pdf:
        print(f"\nPDF ({len(arquivos_pdf)}):")
        for f in arquivos_pdf:
            print(f"   - pdf/{f}")
    
    print(f"\n{'='*60}")
    print(f"ARQUIVO PROTEGIDO (NÃO será deletado): {ARQUIVO_PROTEGIDO}")
    print(f"{'='*60}")
    
    # Confirmação
    resposta = input("\nCONFIRMA EXCLUSÃO? (S/N): ").strip().upper()
    
    if resposta != 'S':
        print("\nLimpeza cancelada pelo usuário.")
        return
    
    # Deletar arquivos
    print("\nDeletando arquivos...")
    deletados = 0
    erros = 0
    
    # Deletar CSVs
    for arquivo in arquivos_csv:
        try:
            caminho = os.path.join(pasta_csv, arquivo)
            os.remove(caminho)
            deletados += 1
            print(f" Deletado: csv/{arquivo}")
        except Exception as e:
            erros += 1
            print(f" Erro ao deletar csv/{arquivo}: {e}")
    
    # Deletar PDFs
    for arquivo in arquivos_pdf:
        try:
            caminho = os.path.join(pasta_pdf, arquivo)
            os.remove(caminho)
            deletados += 1
            print(f"✅ Deletado: pdf/{arquivo}")
        except Exception as e:
            erros += 1
            print(f"❌ Erro ao deletar pdf/{arquivo}: {e}")
    
    # Resumo
    print(f"\n{'='*60}")
    print(f"Deletados: {deletados} arquivos")
    if erros > 0:
        print(f"Erros: {erros}")
    print(f"Preservado: {ARQUIVO_PROTEGIDO}")
    print(f"{'='*60}\n")
    
    # Verificar qual é o último ID
    caminho_controle = os.path.join(pasta_base, ARQUIVO_PROTEGIDO)
    if os.path.exists(caminho_controle):
        with open(caminho_controle, 'r') as f:
            ultimo_id = f.read().strip()
            print(f"Último ID registrado: BAG-{int(ultimo_id):05d}")
            print(f"Próximo lote começará em: BAG-{int(ultimo_id)+1:05d}\n")

if __name__ == "__main__":
    print("\nLIMPADOR DE QR CODES - BAG+ SYSTEM")
    print("Remove todos os arquivos EXCETO controle de sequência\n")
    
    limpar_qrcodes()