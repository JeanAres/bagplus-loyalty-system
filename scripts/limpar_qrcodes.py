import os
import shutil

ARQUIVO_PROTEGIDO = 'ultimo_id.txt'

def limpar_qrcodes():
    """Limpa pasta de QR Codes mantendo controle de sequência"""
    
    pasta = '../qrcodes'
    
    if not os.path.exists(pasta):
        print("\nPasta /qrcodes não existe!")
        return
    
    # Listar arquivos que serão deletados
    arquivos = []
    for item in os.listdir(pasta):
        caminho_completo = os.path.join(pasta, item)
        
        # Pular o arquivo de controle (comparar apenas nome do arquivo)
        if item == ARQUIVO_PROTEGIDO:
            continue
        
        if os.path.isfile(caminho_completo):
            arquivos.append(item)
    
    if not arquivos:
        print("\nPasta já está vazia (exceto controle de ID)!")
        return
    
    # Mostrar o que será deletado
    print(f"\n{'='*60}")
    print("LIMPEZA DE QR CODES")
    print(f"{'='*60}")
    print(f"Pasta: {pasta}")
    print(f"Protegido: {ARQUIVO_PROTEGIDO} (será mantido)")
    print(f"\nArquivos que serão DELETADOS ({len(arquivos)}):")
    print(f"{'='*60}")
    
    # Agrupar por tipo
    pngs = [f for f in arquivos if f.endswith('.png')]
    csvs = [f for f in arquivos if f.endswith('.csv')]
    pdfs = [f for f in arquivos if f.endswith('.pdf')]
    outros = [f for f in arquivos if f not in pngs + csvs + pdfs]
    
    if pngs:
        print(f"\nImagens PNG: {len(pngs)}")
        if len(pngs) <= 10:
            for f in pngs:
                print(f"   - {f}")
        else:
            print(f"   - {pngs[0]}")
            print(f"   - {pngs[1]}")
            print(f"   - ... (+{len(pngs)-4} arquivos)")
            print(f"   - {pngs[-2]}")
            print(f"   - {pngs[-1]}")
    
    if csvs:
        print(f"\nArquivos CSV: {len(csvs)}")
        for f in csvs:
            print(f"   - {f}")
    
    if pdfs:
        print(f"\nArquivos PDF: {len(pdfs)}")
        for f in pdfs:
            print(f"   - {f}")
    
    if outros:
        print(f"\nOutros arquivos: {len(outros)}")
        for f in outros:
            print(f"   - {f}")
    
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
    
    for arquivo in arquivos:
        try:
            caminho = os.path.join(pasta, arquivo)
            os.remove(caminho)
            deletados += 1
            print(f"Deletado: {arquivo}")
        except Exception as e:
            erros += 1
            print(f"Erro ao deletar {arquivo}: {e}")
    
    # Resumo
    print(f"\n{'='*60}")
    print(f"Deletados: {deletados} arquivos")
    if erros > 0:
        print(f"Erros: {erros}")
    print(f"Preservado: {ARQUIVO_PROTEGIDO}")
    print(f"{'='*60}\n")
    
    # Verificar qual é o último ID
    caminho_controle = os.path.join(pasta, ARQUIVO_PROTEGIDO)
    if os.path.exists(caminho_controle):
        with open(caminho_controle, 'r') as f:
            ultimo_id = f.read().strip()
            print(f"Último ID registrado: BAG-{int(ultimo_id):05d}")
            print(f"Próximo lote começará em: BAG-{int(ultimo_id)+1:05d}\n")

if __name__ == "__main__":
    print("\nLIMPADOR DE QR CODES - BAG+ SYSTEM")
    print("Remove todos os arquivos EXCETO controle de sequência\n")
    
    limpar_qrcodes()