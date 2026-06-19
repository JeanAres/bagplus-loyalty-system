"""
Utilitários para ambiente de desenvolvimento
"""
from app.db.models import Usuario
from app.core.security import hash_password, create_access_token
import os

def criar_admin_padrao(db_session_class):
    """Cria usuário admin padrão se não existir (apenas em desenvolvimento)"""
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment not in ["development", "local"]:
        return None
    
    dev_username = os.getenv("DEV_ADMIN_USERNAME")
    dev_password = os.getenv("DEV_ADMIN_PASSWORD")
    
    if not dev_username or not dev_password:
        print("\nAVISO: DEV_ADMIN_USERNAME e DEV_ADMIN_PASSWORD não configurados no .env")
        print("Configure estas variáveis para criar usuário admin de desenvolvimento\n")
        return None
    
    db = db_session_class()
    
    try:
        admin = db.query(Usuario).filter(Usuario.username == dev_username).first()
        
        if not admin:
            admin = Usuario(
                username=dev_username,
                password_hash=hash_password(dev_password),
                nome="Administrador de Desenvolvimento",
                role="admin",
                ativo=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"Usuário admin '{dev_username}' criado com sucesso!")
        
        return admin
        
    finally:
        db.close()

def exibir_token_dev(admin):
    """Exibe token de desenvolvimento no console"""
    if not admin:
        return
    
    dev_username = os.getenv("DEV_ADMIN_USERNAME")
    dev_password = os.getenv("DEV_ADMIN_PASSWORD")
    
    token = create_access_token(data={"sub": admin.username, "role": admin.role})
    
    print("\n" + "=" * 80)
    print("TOKEN DE DESENVOLVIMENTO")
    print("=" * 80)
    print(f"\nBearer {token}\n")
    print("Como usar no Swagger:")
    print("1. Abra http://localhost:8000/docs")
    print("2. Clique no botão 'Authorize' (cadeado)")
    print("3. Cole o token acima (com 'Bearer')")
    print("4. Clique em 'Authorize'\n")
    print(f"Credenciais de login (alternativa):")
    print(f"  Username: {dev_username}")
    print(f"  Password: {dev_password}\n")
    print("Válido por: 24 horas")
    print("=" * 80 + "\n")