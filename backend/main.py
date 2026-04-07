"""
Bag+ API - Sistema de Fidelização Sustentável
Arquivo principal com configuração do FastAPI e inclusão de routers
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models

# Importar routers
from routers import clientes, sacolas, auth, notificacoes
from routers.admin import lotes, suspensao, alertas, relatorios, sacolas as admin_sacolas, exportar, usuarios, auditoria, notificacoes as admin_notificacoes

# Importar utilitários de autenticação
from utils.security import hash_password, create_access_token
import os

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

def criar_admin_padrao():
    """Cria usuário admin padrão se não existir (apenas em desenvolvimento)"""
    from database import SessionLocal
    
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment != "development":
        return None
    
    # Pegar credenciais do .env
    dev_username = os.getenv("DEV_ADMIN_USERNAME")
    dev_password = os.getenv("DEV_ADMIN_PASSWORD")
    
    if not dev_username or not dev_password:
        print("\nAVISO: DEV_ADMIN_USERNAME e DEV_ADMIN_PASSWORD não configurados no .env")
        print("Configure estas variáveis para criar usuário admin de desenvolvimento\n")
        return None
    
    db = SessionLocal()
    
    try:
        # Verificar se admin já existe
        admin = db.query(models.Usuario).filter(
            models.Usuario.username == dev_username
        ).first()
        
        if not admin:
            # Criar admin padrão
            admin = models.Usuario(
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

# Configurar aplicação
app = FastAPI(
    title="Bag+ API",
    version="0.90-beta",
    description="""
Sistema de gerenciamento de sacolas reutilizáveis com programa de fidelidade e autenticação JWT.

## Módulos Públicos (15 endpoints)

### Clientes (8)
Cadastro, busca por nome, validação de CPF, listagem de sacolas, estatísticas, histórico completo, exclusão restritiva.

### Sacolas (7)
Ativação, registro de uso, devolução, consulta, listagem, histórico de uso, verificação de QR Code.

---

## Autenticação (3 endpoints)

**Auth:** Login com JWT, informações do usuário logado, token de desenvolvimento.

---

## Notificações (4 endpoints)

**Notificações:** Criar notificação, listar do cliente, marcar como lida, remover.

---

## Módulos Administrativos (30 endpoints - REQUER AUTENTICAÇÃO)

### Lotes (3)
Importação, listagem, estatísticas por lote.

### Clientes (3)
Suspensão, reativação, listagem de suspensos.

### Alertas (2)
Listagem de alertas, resolução.

### Relatórios (4)
Dashboard, vendas por período, estatísticas gerais, análise de crescimento.

### Sacolas (6)
Próximas do limite, consulta de estoque, transferência, reset de contador, identificação de riscos.

### Exportação (3)
Exportar clientes, sacolas e usos para CSV.

### Usuários (5)
Criar, listar, buscar, editar, desativar usuários.

### Auditoria (1)
Consultar logs de ações administrativas.

### Notificações (3)
Listar todas, envio em massa (broadcast), limpeza de antigas.

---

## Segurança

Autenticação JWT com tokens de 24h, sistema de roles (admin/gerente/caixa), QR Codes com checksum SHA256, validação de intervalo mínimo entre usos (4h), detecção automática de fraudes, logs de auditoria.

---

## Total: 52 endpoints funcionais

**Suporte:** jean06soares@gmail.com
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
        "version": "0.90-beta",
        "status": "online",
        "endpoints": 52,
        "docs": "/docs",
        "message": "Sua sacola vale mais."
    }

if __name__ == "__main__":
    import uvicorn
    
    # Criar admin padrão e exibir token de desenvolvimento
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "development":
        admin = criar_admin_padrao()
        
        if admin:
            # Pegar credenciais do .env
            dev_username = os.getenv("DEV_ADMIN_USERNAME")
            dev_password = os.getenv("DEV_ADMIN_PASSWORD")
            
            # Gerar token de desenvolvimento
            token = create_access_token(
                data={
                    "sub": admin.username,
                    "role": admin.role
                }
            )
            
            # Exibir no console
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
    
    uvicorn.run(app, host="0.0.0.0", port=8000)