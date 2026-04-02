"""
Bag+ API - Sistema de Fidelização Sustentável
Arquivo principal com configuração do FastAPI e inclusão de routers
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models

# Importar routers
from routers import clientes, sacolas, admin_lotes, admin_suspensao, admin_alertas, admin_relatorios, admin_sacolas, admin_exportar

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

# Configurar aplicação
app = FastAPI(
    title="Bag+ API",
    version="1.0.0",
    description="""
    Sistema de gerenciamento de sacolas reutilizáveis com programa de fidelidade.
    
    ## Módulos Públicos (15 endpoints)
    
    **Clientes (8):** Cadastro, busca por nome, validação de CPF, listagem de sacolas, 
    estatísticas, histórico completo, exclusão restritiva.
    
    **Sacolas (7):** Ativação, registro de uso, devolução, consulta, listagem, 
    histórico de uso, verificação de QR Code.
    
    ## Módulos Administrativos (17 endpoints)
    
    **Lotes (2):** Importação de lotes, listagem com distribuição por status.
    
    **Clientes (3):** Suspensão, reativação, listagem de clientes suspensos/bloqueados.
    
    **Alertas (2):** Listagem de alertas detectados, resolução com observações.
    
    **Relatórios (3):** Dashboard geral, relatório de vendas por período, estatísticas consolidadas.
    
    **Sacolas (4):** Sacolas próximas do limite, consulta de estoque, transferência entre clientes, 
    reset de contador.
    
    **Exportação (3):** Exportar clientes, sacolas e registros de uso para CSV.
    
    ## Segurança
    
    QR Codes com checksum SHA256, validação de intervalo mínimo entre usos (4h), 
    detecção automática de fraudes, sistema de suspensão, limite de 40 usos por sacola.
    
    ## Total: 32 endpoints funcionais
    
    Suporte: jean06soares@gmail.com
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
app.include_router(admin_exportar.router)

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
        "endpoints": 32,
        "docs": "/docs",
        "message": "Sua sacola vale mais."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)