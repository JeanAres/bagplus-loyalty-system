# Bag+ - Sistema de Fidelização Sustentável

> **AVISO IMPORTANTE:** Este é um projeto comercial. O código está disponível 
> para avaliação e portfólio, mas **uso comercial requer licença**. 
> Entre em contato para implementação: jean06soares@gmail.com

Sistema completo de gerenciamento de sacolas reutilizáveis com programa de recompensas, autenticação JWT com roles, QR Codes com segurança anti-falsificação, detecção automática de fraudes, sistema de suspensão de clientes, relatórios gerenciais avançados, logs de auditoria e exportação de dados.

> Para entender o conceito e proposta do negócio, veja [PROPOSTA.md](PROPOSTA.md)

---

## Ambientes Disponíveis

### **Produção (Clientes)**
```
URL: https://api.bagplus.com.br/docs
Servidor: AWS EC2 (São Paulo - sa-east-1)
Banco: bagplus_prod.db (dados reais)
Branch: main
Status: 🟢 Online 24/7
```

### **Staging (Testes)**
```
URL: https://staging.bagplus.com.br/docs
Servidor: AWS EC2 (São Paulo - sa-east-1)
Banco: bagplus_staging.db (dados fake)
Branch: dev
Status: 🟢 Online 24/7
```

### **Local (Desenvolvimento)**
```
URL: http://localhost:8000/docs
Banco: bagplus.db (local)
Branch: dev
Status: Quando rodando
```

---

## Infraestrutura

### **Servidor**
- **Provedor:** Amazon Web Services (AWS)
- **Região:** São Paulo (sa-east-1) - Compliance LGPD
- **Tipo:** EC2 t2.micro (1GB RAM, 1 vCPU, 30GB SSD)
- **SO:** Ubuntu 24.04 LTS

### **Domínio**
- **Provedor:** Registro.br
- **Domínio:** bagplus.com.br

### **SSL/HTTPS**
- **Provedor:** Let's Encrypt (Certbot)
- **Renovação:** Automática

### **Containerização**
- **Docker** - Isolamento de ambientes
- **Docker Compose** - Orquestração
- **Nginx** - Proxy reverso e SSL termination

---

## Funcionalidades Implementadas

### Autenticação e Controle de Acesso
- **Sistema JWT completo** - Autenticação com tokens de 24h
- **Gestão de usuários** - Criar, editar, listar e desativar usuários
- **Sistema de roles** - Admin, Gerente, Caixa com permissões granulares
- **31 endpoints protegidos** - Controle de acesso por role
- **Logs de auditoria** - Rastreamento completo de ações administrativas
- **Token de desenvolvimento** - Gerado automaticamente ao iniciar servidor
- **Middleware de autenticação** - Validação automática em todos endpoints admin

### Segurança e Validação
- **QR Codes com Checksum SHA256** - Proteção anti-falsificação
- **Validação de intervalo** - Mínimo 4 horas entre usos da mesma sacola
- **Valor mínimo de compra** - R$ 15,00 por transação
- **Validação de checksum dupla** - No QR Code e no banco de dados

### Detecção Automática de Fraudes
- **Valores diferentes no mesmo dia** - Alerta se cliente usa múltiplas sacolas com valores variados
- **Abuso de valor mínimo** - Alerta se cliente usa 8+ sacolas com R$ 15,00 no mesmo dia
- **Padrão de valores repetidos** - Alerta se cliente sempre compra mesmo valor em dias diferentes
- **Sistema de alertas** - Gravidade baixa/média/alta com resolução manual

### Gestão de Clientes
- **Sistema de suspensão** - Suspender/reativar clientes com motivo registrado
- **Bloqueio de uso** - Clientes suspensos não podem usar sacolas
- **Histórico completo** - Timeline de eventos do cliente
- **Busca por nome** - Busca parcial e case-insensitive
- **Validação de CPF** - Verificar existência sem criar cadastro
- **Estatísticas por cliente** - Total gasto, valor médio, total de usos

### Sistema de Descontos
- **Desconto por Fidelidade** - Marcos: 10, 20, 30, 40 usos
- **Desconto por Devolução** - Baseado no estado da sacola
  - Verde (0-15 usos, até 60 dias): R$ 40,00
  - Amarelo (16-25 usos, até 80 dias): R$ 20,00
  - Vermelho (26-40 usos, até 90 dias): R$ 10,00

### Gerenciamento de Lotes
- **Geração em massa de QR Codes** - Até 5.000 sacolas por lote
- **Importação de lotes** - Via API com recalculo automático de checksums
- **Rastreamento completo** - Data de fabricação, intervalo de IDs, quantidade
- **Controle de estoque** - Consulta de disponibilidade por lote
- **Estatísticas por lote** - Distribuição, taxa de utilização, status

### Relatórios e Analytics
- **Dashboard administrativo** - Visão geral completa do negócio
- **Relatórios de vendas** - Por período com detalhamento diário
- **Estatísticas gerais** - Taxa de devolução, recordes, crescimento
- **Análise Month-over-Month** - Crescimento com python-dateutil
- **Top performers** - Clientes que mais usam e mais gastam
- **Sacolas em risco** - 3 categorias de análise de risco
- **Exportação CSV** - Clientes, sacolas e usos para análise externa com UTF-8 BOM

### Operações Especiais
- **Transferência de sacolas** - Entre clientes com rastreamento e log
- **Reset de contador** - Correção de erros com validação rigorosa e log
- **Sacolas próximas do limite** - Identificar sacolas perto de expirar
- **Resolver alertas** - Marcar alertas como resolvidos com observação

### Auditoria e Compliance
- **Logs automáticos** - Todas ações admin registradas automaticamente
- **Rastreamento de usuário** - Quem fez o quê, quando e por quê
- **Consulta de logs** - Filtros por data, usuário, ação, entidade
- **Detalhes em JSON** - Informações completas sobre cada operação

---

## Início Rápido

### Opção 1: Docker (Recomendado)

#### Pré-requisitos
- Docker
- Docker Compose
- Git

#### Instalação
```bash
# 1. Clonar repositório
git clone https://github.com/JeanAres/bagplus-loyalty-system.git
cd bagplus-loyalty-system

# 2. Criar arquivo .env (copiar do template)
cp .env.example .env

# 3. Editar .env e configurar SECRET_KEY e JWT_SECRET_KEY
# Gerar chaves seguras com:
openssl rand -hex 32

# 4. Subir container
docker-compose up -d

# 5. Ver logs
docker-compose logs -f backend
```

O servidor estará rodando em `http://localhost:8000`

---

### Opção 2: Python Direto

#### Pré-requisitos
- Python 3.11+
- SQLite (incluso no Python)

#### Instalação
```bash
# 1. Clonar repositório
git clone https://github.com/JeanAres/bagplus-loyalty-system.git
cd bagplus-loyalty-system

# 2. Navegar para backend
cd services/backend

# 3. Criar ambiente virtual
python -m venv venv

# 4. Ativar ambiente virtual
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# 5. Instalar dependências
pip install -r requirements.txt

# 6. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env e adicionar SECRET_KEY e JWT_SECRET_KEY

# 7. Iniciar servidor
python run.py
```

O servidor estará rodando em `http://localhost:8000`

**Token JWT de desenvolvimento será exibido no console!**

---

## Workflow de Deploy

### **Desenvolvimento → Staging → Produção**

```bash
# ==========================================
# FASE 1: DESENVOLVIMENTO LOCAL
# ==========================================

# 1. Criar feature nova
git checkout dev
# ... desenvolver código ...

# 2. Testar localmente
python run.py
# Acessar: http://localhost:8000/docs

# 3. Commit e push
git add .
git commit -m "feat: nova funcionalidade X"
git push origin dev

# ==========================================
# FASE 2: DEPLOY EM STAGING (Testes)
# ==========================================

# 4. SSH no servidor AWS
ssh -i <sua-chave>.pem <usuario>@<ip-servidor>

# 5. Atualizar código
cd bagplus-loyalty-system
git checkout dev
git pull origin dev

# 6. Rebuild container de staging
sudo docker-compose up -d --build backend-staging

# 7. Testar em staging
 Acessar: https://staging.bagplus.com.br/docs
 Testar com dados FAKE

# ==========================================
# FASE 3: APROVAÇÃO PARA PRODUÇÃO
# ==========================================

# 8. Se staging OK, mergear para main
git checkout main
git merge dev
git push origin main

# ==========================================
# FASE 4: DEPLOY EM PRODUÇÃO (Clientes)
# ==========================================

# 9. SSH no servidor AWS
ssh -i <sua-chave>.pem <usuario>@<ip-servidor>

# 10. Atualizar código
cd bagplus-loyalty-system
git checkout main
git pull origin main

# 11. Rebuild container de produção
sudo docker-compose up -d --build backend-prod

# 12. Verificar em produção
 Acessar: https://api.bagplus.com.br/docs
 Clientes podem usar!
```

---

## 🐳 Comandos Docker Úteis

```bash
# Ver containers rodando
docker-compose ps

# Ver logs
docker-compose logs backend           # Produção
docker-compose logs backend-staging   # Staging

# Parar containers
docker-compose down

# Rebuild completo
docker-compose up -d --build

# Entrar no container
docker exec -it bagplus_backend_prod bash
docker exec -it bagplus_backend_staging bash

# Limpar tudo e recomeçar
docker-compose down
docker system prune -a
docker-compose up -d --build
```

## Autenticação JWT

### Token Automático (Desenvolvimento)

Ao iniciar o servidor em modo desenvolvimento, um token JWT válido é gerado e exibido automaticamente:

```
================================================================================
TOKEN DE DESENVOLVIMENTO
================================================================================

Bearer eyJ...

Como usar no Swagger:
1. Abra http://localhost:8000/docs
2. Clique no botão 'Authorize' (cadeado verde, canto superior direito)
3. Cole o token acima (inclui 'Bearer')
4. Clique em 'Authorize'
5. Pronto! Agora pode testar todos endpoints protegidos

Credenciais de login (alternativa ao token):
  Username: DEV_ADMIN_USERNAME
  Password: DEV_ADMIN_PASSWORD

Válido por: 24 horas
================================================================================
```

### Fazer Login Manualmente

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=DEV_ADMIN_USERNAME&password=DEV_ADMIN_PASSWORD
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 1,
    "username": "DEV_ADMIN_USERNAME",
    "nome": "Administrador de Desenvolvimento",
    "role": "admin",
    "ativo": true
  }
}
```

### Usar Token nos Endpoints Protegidos

```http
GET /api/admin/usuarios
Authorization: Bearer eyJ...
```

### Sistema de Roles e Permissões

#### 🔴 Admin (Acesso Total)
- Todos os endpoints administrativos
- Criar, editar e desativar usuários
- Suspender e reativar clientes
- Transferir sacolas entre clientes
- Resetar contador de utilizações
- Todos relatórios e exportações
- Ver logs de auditoria

#### 🟡 Gerente (Acesso Gerencial)
- Dashboard e relatórios
- Importar e gerenciar lotes
- Listar e resolver alertas
- Exportar dados (CSV)
- Consultar estoque
- Listar usuários (read-only)
- Ver logs de auditoria
- Suspender/reativar clientes
- Transferir sacolas
- Resetar contador
- Criar/editar usuários

#### 🟢 Caixa (Operacional Apenas)
- Cadastrar clientes
- Ativar sacolas
- Registrar uso de sacolas
- Devolver sacolas
- Buscar clientes e sacolas
- Nenhum acesso a endpoints admin

---

## Acessar Sistema

- **Produção:** `https://api.bagplus.com.br/docs`
- **Staging:** `https://staging.bagplus.com.br/docs`
- **Local:** `http://localhost:8000/docs`
- **Interface do Caixa:** `apps/caixa/index.html` (em desenvolvimento)

---

## Estrutura do Projeto

```
bagplus-loyalty-system/
├── Dockerfile                  # Receita da imagem Docker
├── docker-compose.yml          # Orquestração de containers
├── .env                        # Variáveis de ambiente (NÃO commitar!)
├── .env.example                # Template de variáveis
├── .gitignore
├── README.md
├── PROPOSTA.md
├── CONTRIBUTING.md
│
├── services/                   # Backend
│   └── backend/               # API FastAPI
│       ├── app/              # Aplicação modular
│       │   ├── main.py       # Configuração FastAPI
│       │   ├── routers/      # Endpoints da API
│       │   │   ├── admin/   # Endpoints administrativos (9 módulos)
│       │   │   │   ├── lotes.py
│       │   │   │   ├── suspensao.py
│       │   │   │   ├── alertas.py
│       │   │   │   ├── relatorios.py
│       │   │   │   ├── sacolas.py
│       │   │   │   ├── exportar.py
│       │   │   │   ├── usuarios.py
│       │   │   │   ├── auditoria.py
│       │   │   │   └── notificacoes.py
│       │   │   ├── clientes.py
│       │   │   ├── sacolas.py
│       │   │   ├── notificacoes.py
│       │   │   └── auth.py
│       │   ├── core/         # Lógica central
│       │   │   ├── security.py
│       │   │   ├── audit.py
│       │   │   ├── helpers.py
│       │   │   └── notifications.py
│       │   ├── db/           # Banco de dados
│       │   │   ├── models.py
│       │   │   └── session.py
│       │   └── middleware/   # Middlewares
│       │       └── auth.py
│       ├── docs/             # Documentação Swagger
│       ├── scripts/          # Scripts de desenvolvimento
│       ├── data/             # Banco de dados SQLite
│       │   └── bagplus.db
│       ├── run.py            # Launcher principal
│       ├── requirements.txt
│       └── .env
│
├── apps/                      # Frontends (preparado)
│   └── shared/               # Componentes compartilhados
│
├── storage/                   # Arquivos gerados
│   ├── qrcodes/
│   │   ├── csv/              # CSVs dos lotes
│   │   ├── pdf/              # PDFs para impressão
│   │   └── ultimo_id.txt     # Controle de sequência
│   ├── storage-prod/         # Uploads produção (Docker)
│   └── storage-staging/      # Uploads staging (Docker)
│
├── scripts/                   # Scripts auxiliares
│   ├── qrcodes/
│   │   ├── gerar_qrcodes.py
│   │   └── limpar_qrcodes.py
│   └── database/
│       └── seed_data.py
│
├── infra/                    # Infraestrutura
│   └── database/
│
├── docs/                     # Documentação geral
│   └── SCANNER-REMOTE-KEYBOARD.md
│
└── tests/                    # Testes (preparado)
```

---

## Tecnologias

### Backend
- **FastAPI** - Framework web Python moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **SQLite** - Banco de dados relacional
- **Uvicorn** - Servidor ASGI
- **Pydantic** - Validação de dados
- **Python-dotenv** - Gerenciamento de variáveis de ambiente
- **python-dateutil** - Cálculos de datas para analytics MoM

### Autenticação e Segurança
- **python-jose[cryptography]** - Tokens JWT
- **passlib[bcrypt]** - Hash de senhas
- **python-multipart** - Suporte a formulários de login

### Geração de QR Codes
- **qrcode** - Geração de QR Codes
- **Pillow** - Manipulação de imagens
- **ReportLab** - Geração de PDFs

### Infraestrutura
- **Docker** - Containerização
- **Docker Compose** - Orquestração de containers
- **Nginx** - Proxy reverso e SSL termination
- **Let's Encrypt (Certbot)** - Certificados SSL gratuitos

### Segurança
- **hashlib** - SHA256 para checksums
- **SECRET_KEY** - Chave secreta compartilhada

---

## API Endpoints (52 total)

> **Documentação completa e interativa:**
> - Produção: `https://api.bagplus.com.br/docs`
> - Staging: `https://staging.bagplus.com.br/docs`
> - Local: `http://localhost:8000/docs`

### Clientes (8 endpoints - Públicos)
### Sacolas (7 endpoints - Públicos)
### Autenticação (3 endpoints - Públicos)
### Admin - Lotes (3 endpoints - Admin + Gerente)
### Admin - Clientes (3 endpoints - Variado)
### Admin - Alertas (2 endpoints - Admin + Gerente)
### Admin - Relatórios (4 endpoints - Admin + Gerente)
### Admin - Sacolas (6 endpoints - Variado)
### Admin - Exportação (3 endpoints - Admin + Gerente)
### Admin - Usuários (5 endpoints - Variado)
### Admin - Auditoria (1 endpoint - Admin + Gerente)

*(Detalhamento completo dos 52 endpoints disponível em `/docs` de cada ambiente)*

---
<!-- PARTE 3 DE 3 -->
<!-- CONTINUAÇÃO DA PARTE 2 -->

## Banco de Dados

### Tabelas (7 total)

#### clientes
- cpf (PK)
- nome
- data_cadastro
- status_beneficios (ativo/suspenso/bloqueado)
- motivo_suspensao
- data_suspensao

#### sacolas
- id (PK) - Formato: BAG-00001
- data_criacao
- checksum - SHA256 para validação
- status (estoque/ativo/devolvido)
- lote_id (FK)
- cliente_cpf (FK)
- data_vinculacao
- utilizacoes
- ultima_utilizacao
- data_devolucao

#### registros_uso
- id (PK)
- sacola_id (FK)
- data_uso
- valor_compra

#### lotes
- id (PK)
- data_fabricacao
- data_importacao
- quantidade
- inicio, fim - Range de IDs

#### alertas
- id (PK)
- tipo (enum)
- gravidade (baixa/media/alta)
- cliente_cpf (FK)
- descricao
- data_deteccao
- resolvido
- observacao
- data_resolucao

#### usuarios
- id (PK)
- username (único)
- password_hash (bcrypt)
- nome
- role (admin/gerente/caixa)
- ativo (bool)
- data_criacao
- ultimo_login

#### logs_auditoria
- id (PK)
- usuario_id (FK)
- usuario_username
- acao (string)
- entidade_tipo (Cliente/Sacola/Usuario/Alerta/Lote)
- entidade_id (string)
- detalhes (JSON)
- ip_address
- data_hora

---

## Gerando QR Codes

### 1. Configurar Quantidade
```bash
cd scripts
notepad gerar_qrcodes.py
```

Modificar última linha:
```python
gerar_lote(quantidade=5000)  # Alterar quantidade desejada
```

### 2. Executar Script
```bash
cd scripts/qrcodes
python gerar_qrcodes.py
```

**Confirmar com 'S'**

### 3. Arquivos Gerados
```
storage/qrcodes/
├── csv/
│   └── lote_00001-05000.csv
├── pdf/
│   └── lote_00001-05000_IMPRESSAO.pdf
└── ultimo_id.txt
```

### 4. Importar no Sistema
```http
POST /api/admin/lotes/importar
Authorization: Bearer {seu_token_jwt}
data_fabricacao: 2026-03-31
inicio: 1
fim: 5000
```

> **Otimização:** Não gera PNGs individuais (economia de 50MB e 5.000 arquivos)

---

## Testando o Sistema

### Fluxo Completo de Teste

#### 0. Obter Token JWT
```bash
# Iniciar servidor
python run.py

# Copiar token exibido no console
# OU fazer login via API
```

```http
POST /api/auth/login
username: DEV_ADMIN_USERNAME
password: DEV_ADMIN_PASSWORD
```

#### 1. Autorizar no Swagger
```
1. Abrir http://localhost:8000/docs
2. Clicar em "Authorize" (cadeado)
3. Colar: Bearer {token}
4. Clicar em "Authorize"
```

#### 2. Gerar QR Codes
```bash
cd scripts/qrcodes
python gerar_qrcodes.py
# Confirmar com S
# Resultado: CSV + PDF gerados
```

#### 3. Importar Lote
```http
POST /api/admin/lotes/importar
data_fabricacao: 2026-03-31
inicio: 1
fim: 5
```

#### 4. Cadastrar Cliente
```http
POST /api/clientes
cpf: 12345678900
nome: João Silva
```

#### 5. Ativar Sacola
```http
POST /api/sacolas/ativar
qr_code: BAG-00001:2026-03-31:757314  # Copiar do CSV
cpf_cliente: 12345678900
```

#### 6. Registrar Uso
```http
POST /api/sacolas/registrar-uso
sacola_id: BAG-00001
valor_compra: 125,50
```

#### 7. Ver Dashboard
```http
GET /api/admin/relatorios/dashboard
```

#### 8. Exportar Dados
```http
GET /api/admin/exportar/usos
```

#### 9. Consultar Logs de Auditoria
```http
GET /api/admin/auditoria/logs
```

---

## Configuração

### Variáveis de Ambiente (.env)
```env
# Banco de Dados
DATABASE_URL=sqlite:///./data/bagplus.db

# Ambiente
ENVIRONMENT=development

# API
API_HOST=0.0.0.0
API_PORT=8000

# Segurança (OBRIGATÓRIO - Gerar com: openssl rand -hex 32)
SECRET_KEY=sua_chave_secreta_unica_aqui_256bits
JWT_SECRET_KEY=outra_chave_secreta_para_jwt_256bits

# Credenciais de Desenvolvimento (criadas automaticamente)
DEV_ADMIN_USERNAME=dev_admin
DEV_ADMIN_PASSWORD=ProjetoBag+2026
```

> **IMPORTANTE:** 
> - A mesma `SECRET_KEY` deve estar no servidor e no script de geração de QR Codes
> - `DEV_ADMIN_USERNAME` e `DEV_ADMIN_PASSWORD` são criados automaticamente em modo development
> - Em produção, definir `ENVIRONMENT=production` desativa criação automática
> - NUNCA commitar .env no Git!

---

## Segurança

### Proteções Implementadas

1. **Anti-falsificação de QR Codes**
   - Checksum SHA256 único por sacola
   - Validação dupla (código + banco)
   - Impossível gerar QR Code válido sem SECRET_KEY

2. **Anti-fraude de Uso**
   - Intervalo mínimo 4 horas entre usos
   - Detecção automática de padrões suspeitos
   - Sistema de alertas com gravidade

3. **Controle de Acesso**
   - Sistema de suspensão de clientes
   - Bloqueio permanente quando necessário
   - Registro de motivos e datas

4. **Autenticação e Autorização**
   - JWT com expiração de 24h
   - Hash de senhas com bcrypt (custo 12)
   - Controle granular por roles (admin/gerente/caixa)
   - 31 endpoints protegidos
   - Middleware de autenticação automática

5. **Auditoria Completa**
   - Histórico completo de eventos
   - Logs de todas ações administrativas
   - Rastreamento de quem fez o quê e quando
   - Exportação de dados para análise
   - Rastreamento de transferências e resets
   - Detalhes completos em JSON

---

## Suporte

### Scanner de QR Code

Ver documentação completa: [docs/SCANNER-REMOTE-KEYBOARD.md](docs/SCANNER-REMOTE-KEYBOARD.md)

**Produção:** Leitor USB (pistolinha)  
**Testes:** Remote Keyboard (Android)

### Problemas Comuns

#### Erro: "Module not found"
```bash
pip install -r services/backend/requirements.txt
```

#### Erro: "QR Code inválido"
- Verificar se SECRET_KEY é a mesma no script e no backend
- Verificar formato: `BAG-00001:2026-03-31:checksum`

#### Erro: "Valor mínimo R$ 15,00"
- Sistema não aceita valores abaixo de R$ 15,00 (proteção anti-fraude)

#### Erro: "Not authenticated" ou "Insufficient permissions"
- Verificar se token JWT está sendo enviado no header Authorization
- Verificar se token não expirou (24h de validade)
- Verificar se usuário tem a role necessária para o endpoint

#### Erro: "Port already in use"
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>

# Ou trocar porta no docker-compose.yml
```

---

## Contato

**Email:** jean06soares@gmail.com  
**GitHub:** https://github.com/JeanAres/bagplus-loyalty-system

---

## Licença

Este é um projeto comercial proprietário. O código está disponível para avaliação, mas uso comercial requer licença.

---

**Bag+** - Sua sacola vale mais. 🌱♻️

---

**Versão:** v0.90-beta  
**Endpoints:** 52 funcionais  
**Atualizado:** 11/04/2026  
**Arquitetura:** Modular Monorepo + Docker  
**Status:** 🟢 Produção Online (AWS São Paulo)