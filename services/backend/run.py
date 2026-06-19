"""
Launcher para iniciar o servidor Bag+ API
"""
import sys
import os

# Adicionar backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from app.main import app
    from scripts.dev_setup import criar_admin_padrao, exibir_token_dev
    from app.db.session import SessionLocal
    import uvicorn
    
    # Setup de desenvolvimento
    environment = os.getenv("ENVIRONMENT", "development")
    if environment in ["development", "local"]:
        admin = criar_admin_padrao(SessionLocal)
        exibir_token_dev(admin)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)