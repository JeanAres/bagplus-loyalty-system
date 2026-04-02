"""
Bag+ API - Sistema de Fidelização Sustentável
Arquivo principal com configuração do FastAPI e inclusão de routers
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models

# Importar routers
from routers import clientes, sacolas, admin_lotes, admin_suspensao, admin_alertas, admin_relatorios, admin_sacolas

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

# Configurar aplicação
app = FastAPI(
    title="Bag+ API",
    version="1.0.0",
    description="""
    Sistema completo de gerenciamento de sacolas reutilizáveis com programa de fidelidade.
    
    ## Funcionalidades
    
    * **Clientes** - Cadastro e gerenciamento de clientes
    * **Sacolas** - Ativação, uso e devolução de sacolas reutilizáveis
    * **Admin - Lotes** - Importação e gerenciamento de lotes de sacolas
    * **Admin - Suspensão** - Suspensão e reativação de clientes
    * **Admin - Alertas** - Detecção automática de padrões suspeitos
    
    ## Segurança
    
    * QR Codes com checksum SHA256 anti-falsificação
    * Validação de intervalo mínimo entre usos (4 horas)
    * Detecção automática de fraudes
    * Sistema de suspensão de clientes
    
    ## Suporte
    
    Email: jean06soares@gmail.com
    """,
    contact={
        "name": "Bag+ Suporte",
        "email": "jean06soares@gmail.com",
    },
    license_info={
        "name": "Proprietário",
        "url": "https://github.com/JeanAres/bagplus-loyalty-system",
    }
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(clientes.router)
app.include_router(sacolas.router)
app.include_router(admin_lotes.router)
app.include_router(admin_suspensao.router)
app.include_router(admin_alertas.router)
app.include_router(admin_relatorios.router)
app.include_router(admin_sacolas.router)

@app.get(
    "/",
    tags=["Sistema"],
    summary="Informações da API",
    description="Retorna informações básicas sobre a API Bag+"
)
def read_root():
    """Endpoint raiz com informações da API"""
    return {
        "api": "Bag+ - Sistema de Fidelização Sustentável",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "message": "Sua sacola vale mais. 🌱"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)