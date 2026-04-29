"""
Bag+ API - Sistema de Fidelização Sustentável
Arquivo principal - Inicialização da aplicação
"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRoute

# Database
from app.db.session import engine
from app.db import models

# Configurações para o rate limit
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limiter import limiter

# Middleware de segurança
from app.middleware.security_headers import SecurityHeadersMiddleware

# Routers
from app.routers import clientes, sacolas, auth, notificacoes
from app.routers.admin import (
    lotes, suspensao, alertas, relatorios,
    sacolas as admin_sacolas, exportar, usuarios,
    auditoria, qrcodes, notificacoes as admin_notificacoes,
    entidades, unidades
)

# Configuração Swagger
from docs.swagger.config.metadata import (
    TITLE, VERSION, DESCRIPTION, CONTACT,
    LICENSE_INFO, TAGS_METADATA, SWAGGER_UI_PARAMETERS
)
from docs.swagger.config.setup import configure_swagger_ui

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

# Rate Limiting
from app.core.event_logger import security_logger

app.state.limiter = limiter

# Handler customizado para rate limit com logging
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handler que registra rate limit excedido antes de retornar erro."""
    # Registrar no log de segurança
    security_logger.rate_limit_exceeded(
        endpoint=request.url.path,
        ip=request.client.host if request.client else "unknown",
        limit=str(exc.detail) if hasattr(exc, 'detail') else "unknown"
    )
    # Chamar handler padrão
    return _rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Montar arquivos estáticos (CSS do Swagger)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_path = os.path.join(BASE_DIR, "docs", "swagger", "styles")
app.mount("/swagger-styles", StaticFiles(directory=static_path), name="swagger-styles")

# Configurar Swagger UI customizado
configure_swagger_ui(app)

# Configuração CORS
origins = [
    # Desenvolvimento local
    "http://localhost:3000",      # Admin React (dev)
    "http://localhost:8000",      # Backend local
    "http://localhost:5173",      # Vite dev server
    "http://localhost:5500",      # Live Server (caixa HTML)
    
    # Produção
    "https://api.bagplus.com.br",
    "https://caixa.bagplus.com.br",
    "https://admin.bagplus.com.br",
    
    # Staging (backend + frontends)
    "https://staging.bagplus.com.br",           # Backend staging
    "https://caixa-staging.bagplus.com.br",     # Frontend caixa staging
    "https://admin-staging.bagplus.com.br",     # Frontend admin staging
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Security Headers
app.add_middleware(SecurityHeadersMiddleware)

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
app.include_router(entidades.router)
app.include_router(unidades.router)


def count_api_endpoints() -> int:
    """Conta dinamicamente apenas os endpoints da API (prefixo /api)."""
    return sum(
        1
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api")
    )


@app.get(
    "/",
    tags=["Sistema"],
    summary="Informações da API",
    description="Retorna informações básicas sobre a API Bag+"
)
def read_root():
    """Endpoint raiz com informações da API"""
    import os
    environment = os.getenv("ENVIRONMENT", "local")
    
    response = {
        "api": "Bag+ - Sistema de Fidelização Sustentável",
        "version": VERSION,
        "status": "online",
        "endpoints": count_api_endpoints(),
        "message": "Sua sacola vale mais."
    }
    
    # Mostrar docs apenas em ambientes de desenvolvimento
    if environment in ["local", "staging"]:
        response["docs"] = "/docs"
        response["redoc"] = "/redoc"
    
    return response