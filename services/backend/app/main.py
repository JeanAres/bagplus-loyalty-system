"""
Bag+ API - Sistema de Fidelização Sustentável
Arquivo principal - Inicialização da aplicação
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Database
from app.db.session import engine, SessionLocal
from app.db import models

# Routers
from app.routers import clientes, sacolas, auth, notificacoes
from app.routers.admin import (
    lotes, suspensao, alertas, relatorios,
    sacolas as admin_sacolas, exportar, usuarios,
    auditoria, qrcodes, notificacoes as admin_notificacoes
)

# Configuração Swagger
from docs.swagger.config.metadata import (
    TITLE, VERSION, DESCRIPTION, CONTACT,
    LICENSE_INFO, TAGS_METADATA, SWAGGER_UI_PARAMETERS
)
from docs.swagger.config.setup import configure_swagger_ui

# Utilitários de desenvolvimento
from scripts.dev_setup import criar_admin_padrao, exibir_token_dev

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

# Configurar aplicação
app = FastAPI(
    title=TITLE,
    version=VERSION,
    description=DESCRIPTION,
    contact=CONTACT,
    license_info=LICENSE_INFO,
    openapi_tags=TAGS_METADATA,
    swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
    docs_url=None  # Desabilita docs padrão para usar customizado
)

# Montar arquivos estáticos (CSS do Swagger)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_path = os.path.join(BASE_DIR, "docs", "swagger", "styles")
app.mount("/swagger-styles", StaticFiles(directory=static_path), name="swagger-styles")

# Configurar Swagger UI customizado
configure_swagger_ui(app)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers públicos
app.include_router(clientes.router)
app.include_router(sacolas.router)
app.include_router(auth.router)
app.include_router(notificacoes.router)

# Incluir routers admin
app.include_router(lotes.router)
app.include_router(suspensao.router)
app.include_router(alertas.router)
app.include_router(relatorios.router)
app.include_router(admin_sacolas.router)
app.include_router(exportar.router)
app.include_router(usuarios.router)
app.include_router(auditoria.router)
app.include_router(admin_notificacoes.router)
app.include_router(qrcodes.router)

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
        "version": VERSION,
        "status": "online",
        "endpoints": 52,
        "docs": "/docs",
        "redoc": "/redoc",
        "message": "Sua sacola vale mais."
    }