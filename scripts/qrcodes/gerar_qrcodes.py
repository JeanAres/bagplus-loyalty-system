"""
Script CLI para geração de QR Codes
Usa o módulo core/qrcode_generator.py (mesma lógica da API)
Sincronizado com API REST via ultimo_id.txt
"""
import sys
import os

# Adicionar path do backend ao sys.path
# __file__ está em: scripts/qrcodes/gerar_qrcodes.py
script_dir = os.path.dirname(os.path.abspath(__file__))  # scripts/qrcodes/
scripts_dir = os.path.dirname(script_dir)                 # scripts/
root_dir = os.path.dirname(scripts_dir)                   # bagplus-loyalty-system/
backend_path = os.path.join(root_dir, 'services', 'backend')
sys.path.insert(0, backend_path)

from app.core.qrcode_generator import gerar_lote_qrcodes, ler_ultimo_id
from app.core.security import SECRET_KEY
from datetime import datetime


def main():
    """Função principal do CLI"""
    
    print("\n" + "="*60)
    print("GERADOR DE QR CODES - BAG+ SYSTEM (CLI)")
    print("="*60)
    print("IDs são sequenciais e NUNCA se repetem!")
    print("Sincronizado com API REST (compartilha ultimo_id.txt)")
    print("="*60 + "\n")
    
    # Verificar SECRET_KEY
    if not SECRET_KEY:
        print("ERRO: SECRET_KEY não encontrada no .env")
        print("Verifique: services/backend/.env")
        return
    
    # Mostrar último ID
    ultimo_id = ler_ultimo_id()
    proximo_id = ultimo_id + 1
    
    print(f"Status:")
    if ultimo_id > 0:
        print(f"Último ID gerado: BAG-{ultimo_id:05d}")
    else:
        print(f"Nenhum QR Code gerado ainda")
    print(f"Próximo ID: BAG-{proximo_id:05d}")
    print()
    
    # Input de quantidade
    try:
        quantidade_input = input("Quantos QR Codes gerar? (1-10000): ").strip()
        quantidade = int(quantidade_input)
        
        if quantidade <= 0 or quantidade > 10000:
            print("Quantidade deve estar entre 1 e 10.000")
            return
            
    except ValueError:
        print("Valor inválido. Digite um número entre 1 e 10.000")
        return
    except KeyboardInterrupt:
        print("\nOperação cancelada")
        return
    
    # Input de data (opcional)
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    print(f"\nData de criação (deixe vazio para usar hoje: {data_hoje})")
    data_input = input("Data (YYYY-MM-DD): ").strip()
    data_criacao = data_input if data_input else None
    
    # Validar data se fornecida
    if data_criacao:
        try:
            datetime.strptime(data_criacao, '%Y-%m-%d')
        except ValueError:
            print("Data inválida. Use formato YYYY-MM-DD (ex: 2026-04-15)")
            return
    
    # Input de formatos
    print("\nFormatos a gerar:")
    print("   1 - Apenas CSV (importar no banco)")
    print("   2 - Apenas PDF (enviar para gráfica)")
    print("   3 - Ambos (CSV + PDF) [padrão]")
    
    try:
        formato_opcao = input("   Escolha (1/2/3) [3]: ").strip() or "3"
        
        if formato_opcao == "1":
            formatos = ["csv"]
        elif formato_opcao == "2":
            formatos = ["pdf"]
        else:
            formatos = ["csv", "pdf"]
            
    except KeyboardInterrupt:
        print("\nOperação cancelada")
        return
    
    # Calcular resumo
    fim = proximo_id + quantidade - 1
    data_exibir = data_criacao or data_hoje
    
    # Mostrar resumo
    print("\n" + "="*60)
    print("RESUMO DA GERAÇÃO:")
    print("="*60)
    print(f"   Intervalo: BAG-{proximo_id:05d} até BAG-{fim:05d}")
    print(f"   Quantidade: {quantidade} QR Codes")
    print(f"   Data: {data_exibir}")
    print(f"   Formatos: {', '.join(formatos).upper()}")
    print("="*60 + "\n")
    
    # Confirmação final
    try:
        confirmacao = input("Confirmar geração? (S/N): ").strip().upper()
    except KeyboardInterrupt:
        print("\nOperação cancelada")
        return
    
    if confirmacao != 'S':
        print("\nGeração cancelada pelo usuário")
        return
    
    # GERAR QR CODES!
    print("\nGerando QR Codes...\n")
    
    try:
        resultado = gerar_lote_qrcodes(
            quantidade=quantidade,
            secret_key=SECRET_KEY,
            data_criacao=data_criacao,
            formatos=formatos
        )
        
        # Sucesso!
        print("\n" + "="*60)
        print("GERAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print(f"Quantidade: {resultado['quantidade']} QR Codes")
        print(f"Intervalo: {resultado['intervalo']}")
        print(f"Data: {resultado['data_criacao']}")
        print(f"Próximo ID: BAG-{resultado['fim'] + 1:05d}")
        print()
        print("Arquivos gerados:")
        
        if resultado['arquivos']['csv']:
            print(f"CSV: {resultado['arquivos']['csv']}")
        
        if resultado['arquivos']['pdf']:
            print(f"PDF: {resultado['arquivos']['pdf']}")
        
        print()
        print("Próximos passos:")
        print("1. Importar CSV no sistema via API:")
        print("  POST /api/admin/lotes/importar")
        print("2. Enviar PDF para gráfica")
        print("="*60 + "\n")
        
    except ValueError as e:
        print(f"\nERRO: {e}")
    except Exception as e:
        print(f"\nERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()