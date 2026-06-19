"""
Script de inicialização do servidor STAGING local
Usa banco staging_bagplus.db zerado
Porta: 8001
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# Configurar variáveis de ambiente para STAGING
os.environ["ENVIRONMENT"] = "staging"
os.environ["DATABASE_URL"] = "sqlite:///./data/staging_bagplus.db"
os.environ["API_PORT"] = "8001"

# Importar após configurar ambiente
import uvicorn
from app.main import app
from app.db.session import get_db
from app.db import models
from app.core.security import hash_password

def criar_usuario_admin():
    """Cria usuário dev_admin se não existir"""
    db = next(get_db())
    
    # Obter credenciais do .env
    username = os.getenv("DEV_ADMIN_USERNAME", "dev_admin")
    password = os.getenv("DEV_ADMIN_PASSWORD")
    
    if not password:
        print("❌ ERRO: DEV_ADMIN_PASSWORD não definido no .env")
        print("   Adicione no .env: DEV_ADMIN_PASSWORD=sua_senha_aqui")
        db.close()
        sys.exit(1)
    
    # Verificar se já existe
    existing = db.query(models.Usuario).filter(
        models.Usuario.username == username
    ).first()
    
    if existing:
        print(f"✅ Usuário {username} já existe")
        db.close()
        return
    
    # Criar admin
    admin = models.Usuario(
        username=username,
        password_hash=hash_password(password),
        nome="Admin Desenvolvimento Staging",
        role="admin",
        ativo=True
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    print(f"✅ Usuário criado: {admin.username} (ID: {admin.id}, Role: {admin.role})")
    db.close()

def main():
    print("=" * 80)
    print("STAGING LOCAL - BAG+ LOYALTY SYSTEM")
    print("=" * 80)
    print(f"Ambiente: STAGING")
    print(f"Banco: data/staging_bagplus.db")
    print(f"Porta: 8001")
    print(f"URL: http://localhost:8001/docs")
    print("=" * 80)
    
    # Criar tabelas se não existirem
    from app.db.session import engine
    models.Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas/verificadas")
    
    # Criar usuário admin
    criar_usuario_admin()
    
    print("=" * 80)
    print("🚀 Iniciando servidor STAGING...")
    print("=" * 80)
    
    # Iniciar servidor
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()