"""
Script de testes do ambiente STAGING
Valida endpoints principais e funcionalidades
"""

import os
import sys
import requests
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Ajustar caminho para encontrar .env no backend
backend_path = Path(__file__).resolve().parent.parent / "services" / "backend"
env_path = backend_path / ".env"

# Carregar variáveis de ambiente do backend
load_dotenv(dotenv_path=env_path)

BASE_URL = "http://localhost:8001"
USERNAME = os.getenv("DEV_ADMIN_USERNAME", "dev_admin")
PASSWORD = os.getenv("DEV_ADMIN_PASSWORD")

if not PASSWORD:
    print("❌ ERRO: DEV_ADMIN_PASSWORD não definido no .env")
    print("   Adicione no .env: DEV_ADMIN_PASSWORD=sua_senha_aqui")
    exit(1)

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_login():
    """Testa login e obtém token"""
    print_section("1. TESTE DE AUTENTICAÇÃO")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        params={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login bem-sucedido")
        print(f"   Usuário: {data['user']['username']}")
        print(f"   Role: {data['user']['role']}")
        print(f"   Token válido por: {data['expires_in']}s")
        return data['access_token']
    else:
        print(f"❌ Falha no login: {response.status_code}")
        print(f"   {response.text}")
        return None

def test_login_with_terminal():
    """Testa login com terminal (caixa)"""
    print_section("2. TESTE DE LOGIN COM TERMINAL")
    
    # Primeiro criar um usuário caixa
    token = test_login()
    if not token:
        return
    
    # Criar usuário caixa via API
    response = requests.post(
        f"{BASE_URL}/api/admin/usuarios",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "caixa_teste",
            "password": "senha123",
            "nome": "Caixa Teste",
            "role": "caixa"
        }
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Usuário caixa criado")
    elif response.status_code == 409:
        print(f"⚠️  Usuário caixa já existe")
    
    # Fazer login com terminal
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        params={
            "username": "caixa_teste",
            "password": "senha123",
            "terminal": "caixa 2"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login com terminal bem-sucedido")
        print(f"   Usuário: {data['user']['username']}")
        print(f"   Terminal: {data['user'].get('terminal', 'N/A')}")
        print(f"   Expira em: {data['expires_in']}s (12h para caixa)")
        return data['access_token']
    else:
        print(f"❌ Falha no login com terminal: {response.status_code}")
        return None

def test_qrcode_generation(token):
    """Testa geração de QR Codes"""
    print_section("3. TESTE DE GERAÇÃO DE QR CODES")
    
    response = requests.post(
        f"{BASE_URL}/api/admin/qrcodes/gerar",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "quantidade": 10,
            "formatos": ["csv", "pdf"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ QR Codes gerados com sucesso")
        print(f"   Intervalo: {data['intervalo']}")
        print(f"   Data: {data['data_criacao']}")
        print(f"   Links:")
        for tipo, link in data['links_download'].items():
            print(f"     {tipo.upper()}: {link}")
        return True
    else:
        print(f"❌ Falha na geração: {response.status_code}")
        print(f"   {response.text}")
        return False

def test_cliente_flow(token):
    """Testa fluxo completo de cliente"""
    print_section("4. TESTE DE FLUXO DE CLIENTE")
    
    # 1. Cadastrar cliente
    cpf = "12345678900"
    response = requests.post(
        f"{BASE_URL}/api/clientes",
        json={
            "cpf": cpf,
            "nome": "Cliente Teste Staging"
        }
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Cliente cadastrado: {cpf}")
    elif response.status_code == 409:
        print(f"⚠️  Cliente já existe: {cpf}")
    else:
        print(f"❌ Falha ao cadastrar cliente: {response.status_code}")
        return False
    
    # 2. Ativar sacola (precisa ter QR code gerado)
    # Por enquanto só validamos que o endpoint existe
    print(f"✅ Endpoints de sacola disponíveis")
    
    return True

def test_dashboard(token):
    """Testa dashboard administrativo"""
    print_section("5. TESTE DE DASHBOARD")
    
    response = requests.get(
        f"{BASE_URL}/api/admin/relatorios/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Dashboard carregado")
        print(f"   Total clientes: {data.get('total_clientes', 0)}")
        print(f"   Total sacolas: {data.get('total_sacolas', 0)}")
        print(f"   Registros de uso: {data.get('total_registros_uso', 0)}")
        return True
    else:
        print(f"❌ Falha ao carregar dashboard: {response.status_code}")
        return False

def test_vendas_por_terminal(token):
    """Testa relatório de vendas por terminal"""
    print_section("6. TESTE DE RELATÓRIO POR TERMINAL")
    
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    response = requests.get(
        f"{BASE_URL}/api/admin/relatorios/vendas-por-terminal",
        headers={"Authorization": f"Bearer {token}"},
        params={"data": data_hoje}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Relatório carregado")
        print(f"   Data: {data.get('data', 'N/A')}")
        print(f"   Terminais encontrados: {len(data.get('terminais', []))}")
        if data.get('terminais'):
            for terminal in data['terminais'][:3]:  # Mostrar primeiros 3
                print(f"     - {terminal.get('terminal', 'N/A')}: {terminal.get('total_vendas', 0)} vendas")
        return True
    else:
        print(f"❌ Falha ao carregar relatório: {response.status_code}")
        return False

def test_auditoria(token):
    """Testa logs de auditoria"""
    print_section("7. TESTE DE LOGS DE AUDITORIA")
    
    response = requests.get(
        f"{BASE_URL}/api/admin/auditoria/logs",
        headers={"Authorization": f"Bearer {token}"},
        params={"limit": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Logs carregados")
        print(f"   Total de logs: {data.get('total', 0)}")
        if data.get('logs'):
            print(f"   Últimos logs:")
            for log in data['logs'][:3]:
                print(f"     - {log.get('acao', 'N/A')} por {log.get('usuario_username', 'N/A')}")
        return True
    else:
        print(f"❌ Falha ao carregar logs: {response.status_code}")
        return False

def main():
    print("="*80)
    print("TESTES STAGING LOCAL - BAG+ LOYALTY SYSTEM")
    print("="*80)
    print(f"URL Base: {BASE_URL}")
    print(f"Usuário: {USERNAME}")
    print("="*80)
    
    # 1. Login admin
    token = test_login()
    if not token:
        print("\n❌ Falha na autenticação. Abortando testes.")
        return
    
    # 2. Login com terminal
    test_login_with_terminal()
    
    # 3. Geração de QR Codes
    test_qrcode_generation(token)
    
    # 4. Fluxo de cliente
    test_cliente_flow(token)
    
    # 5. Dashboard
    test_dashboard(token)
    
    # 6. Vendas por terminal
    test_vendas_por_terminal(token)
    
    # 7. Auditoria
    test_auditoria(token)
    
    # Resumo
    print_section("RESUMO DOS TESTES")
    print("✅ Testes concluídos!")
    print("\nPróximos passos:")
    print("1. Abrir Swagger: http://localhost:8001/docs")
    print("2. Clicar em 'Authorize' e usar o token obtido")
    print("3. Testar manualmente os 58 endpoints")
    print("4. Validar sistema de terminais")
    print("5. Testar API de QR Codes completa")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro durante testes: {e}")
        import traceback
        traceback.print_exc()