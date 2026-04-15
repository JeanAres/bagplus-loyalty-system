# Bag+ - Sistema de Fidelização Sustentável

> **AVISO IMPORTANTE:** Este é um projeto comercial. O código está disponível 
> para avaliação e portfólio, mas **uso comercial requer licença**. 
> Entre em contato para implementação: jean06soares@gmail.com

Sistema completo de gerenciamento de sacolas reutilizáveis com programa de recompensas, autenticação JWT com roles, sistema de terminais, QR Codes com segurança anti-falsificação, detecção automática de fraudes, sistema de suspensão de clientes, relatórios gerenciais avançados, logs de auditoria e exportação de dados.

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
- **Sistema JWT completo** - Autenticação com tokens (12h caixa, 24h admin/gerente)
- **Sistema de terminais** - Rastreamento por caixa (terminal no token JWT)
- **Gestão de usuários** - Criar, editar, listar e desativar usuários
- **Sistema de roles** - Admin, Gerente, Caixa com permissões granulares
- **35 endpoints protegidos** - Controle de acesso por role
- **Logs de auditoria** - Rastreamento completo: quem, quando, onde (terminal), de onde (IP)
- **Token de desenvolvimento** - Gerado automaticamente ao iniciar servidor
- **Middleware de autenticação** - Validação automática em todos endpoints admin

### Sistema de Terminais
- **Identificação por caixa** - 5 terminais configurados (Caixa 1-5)
- **Terminal no login** - Campo obrigatório para caixas
- **Terminal no token JWT** - Informação anexada ao payload do token
- **Rastreabilidade completa** - Logs capturam terminal + IP + usuário
- **Expiração diferenciada** - 12h para caixas, 24h para admin/gerente
- **Relatórios por terminal** - Endpoint vendas-por-terminal com totais, ticket médio, usuários
- **Autenticação obrigatória** - Registro de uso requer token JWT válido

### Geração e Gestão de QR Codes
- **API REST completa** - 4 endpoints para geração e gerenciamento
- **Módulo reutilizável** - Lógica compartilhada entre API e CLI
- **Sequência sincronizada** - API e script CLI compartilham ultimo_id.txt
- **Geração via Swagger** - Interface web para não-técnicos
- **Script CLI** - Geração via terminal para admins avançados
- **Controle de acesso** - Apenas admins podem gerar QR codes
- **Auditoria automática** - Logs registram quem gerou, quando, quantos
- **Download direto** - CSV e PDF via endpoints dedicados
- **Histórico de lotes** - Rastreamento completo de todos os lotes gerados
- **Formatos flexíveis** - CSV (importação), PDF (gráfica) ou ambos

### Segurança e Validação
- **QR Codes com Checksum SHA256** - Proteção anti-falsificação
- **Validação de intervalo** - Mínimo 4 horas entre usos da mesma sacola
- **Valor mínimo de compra** - R$ 15,00 por transação
- **Validação de checksum dupla** - No QR Code e no banco de dados
- **Validação de CPF** - Formato e dígitos verificadores com validate-docbr

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
- **Validação de CPF** - Verificar formato e dígitos verificadores (validate-docbr)
- **Validação de existência** - Verificar se cliente existe sem criar cadastro
- **Estatísticas por cliente** - Total gasto, valor médio, total de usos
- **Exclusão restritiva** - DELETE protegido por role admin

### Sistema de Descontos
- **Desconto por Fidelidade** - Marcos: 10, 20, 30, 40 usos
- **Desconto por Devolução** - Baseado no estado da sacola
  - Verde (0-15 usos, até 60 dias): R$ 40,00
  - Amarelo (16-25 usos, até 80 dias): R$ 20,00
  - Vermelho (26-40 usos, até 90 dias): R$ 10,00

### Gerenciamento de Lotes
- **Geração em massa de QR Codes** - Até 10.000 sacolas por lote
- **Importação de lotes** - Via API com recalculo automático de checksums
- **Rastreamento completo** - Data de fabricação, intervalo de IDs, quantidade
- **Controle de estoque** - Consulta de disponibilidade por lote
- **Estatísticas por lote** - Distribuição, taxa de utilização, status

### Relatórios e Analytics
- **Dashboard administrativo** - Visão geral completa do negócio
- **Relatórios de vendas** - Por período com detalhamento diário
- **Vendas por terminal** - Total, ticket médio, usuários por caixa
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
- **Rastreamento completo** - Usuário, terminal, IP, timestamp
- **Consulta de logs** - Filtros por data, usuário (busca parcial), ação, entidade
- **Detalhes em JSON** - Informações completas sobre cada operação
- **Filtro username** - Busca parcial case-insensitive (ex: "joão" encontra "joão.silva")

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
# Acessar: https://staging.bagplus.com.br/docs
# Testar com dados FAKE

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
# Acessar: https://api.bagplus.com.br/docs
# Clientes podem usar!
```

---

## 🐳 Comandos Docker Úteis

```bash
# Ver containers rodando
docker-compose ps

# Ver logs
docker-compose logs backend-prod      # Produção
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

---

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

**Com terminal (caixas):**
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=caixa_teste&password=senha123&terminal=caixa 2
```

**Sem terminal (admin/gerente):**
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
  "expires_in": 43200,
  "user": {
    "id": 2,
    "username": "caixa_teste",
    "nome": "Caixa Teste",
    "role": "caixa",
    "terminal": "caixa 2",
    "ativo": true
  }
}
```

### Usar Token nos Endpoints Protegidos

```http
POST /api/sacolas/registrar-uso
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "sacola_id": "BAG-00001",
  "valor_compra": "125,50"
}
```

### Sistema de Roles e Permissões

#### 🔴 Admin (Acesso Total)
- ✅ Todos os endpoints administrativos
- ✅ Criar, editar e desativar usuários
- ✅ Gerar QR Codes (API)
- ✅ Suspender e reativar clientes
- ✅ Transferir sacolas entre clientes
- ✅ Resetar contador de utilizações
- ✅ Todos relatórios e exportações
- ✅ Ver logs de auditoria

#### 🟡 Gerente (Acesso Gerencial)
- ✅ Dashboard e relatórios
- ✅ Relatório vendas-por-terminal
- ✅ Importar e gerenciar lotes
- ✅ Download de QR Codes gerados
- ✅ Histórico de lotes de QR Codes
- ✅ Listar e resolver alertas
- ✅ Exportar dados (CSV)
- ✅ Consultar estoque
- ✅ Listar usuários (read-only)
- ✅ Ver logs de auditoria
- ✅ Suspender/reativar clientes
- ✅ Transferir sacolas
- ✅ Resetar contador
- ❌ Criar/editar usuários
- ❌ Gerar QR Codes

#### 🟢 Caixa (Operacional Apenas)
- ✅ Cadastrar clientes
- ✅ Ativar sacolas
- ✅ Registrar uso de sacolas (com autenticação obrigatória)
- ✅ Devolver sacolas
- ✅ Buscar clientes e sacolas
- ✅ Login com terminal
- ❌ Nenhum acesso a endpoints admin

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
│       │   │   ├── admin/   # Endpoints administrativos (10 módulos)
│       │   │   │   ├── lotes.py
│       │   │   │   ├── suspensao.py
│       │   │   │   ├── alertas.py
│       │   │   │   ├── relatorios.py
│       │   │   │   ├── sacolas.py
│       │   │   │   ├── exportar.py
│       │   │   │   ├── usuarios.py
│       │   │   │   ├── auditoria.py
│       │   │   │   ├── notificacoes.py
│       │   │   │   └── qrcodes.py
│       │   │   ├── clientes.py
│       │   │   ├── sacolas.py
│       │   │   ├── notificacoes.py
│       │   │   └── auth.py
│       │   ├── core/         # Lógica central
│       │   │   ├── security.py
│       │   │   ├── audit.py
│       │   │   ├── helpers.py
│       │   │   ├── notifications.py
│       │   │   └── qrcode_generator.py
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
│   │   ├── gerar_qrcodes.py  # Script CLI (usa módulo core)
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
- **validate-docbr** - Validação de CPF e CNPJ

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

## API Endpoints (57 total)

> **Documentação completa e interativa:**
> - Produção: `https://api.bagplus.com.br/docs`
> - Staging: `https://staging.bagplus.com.br/docs`
> - Local: `http://localhost:8000/docs`

### Clientes (9 endpoints - Públicos)
### Sacolas (7 endpoints - Públicos)
### Autenticação (3 endpoints - Públicos)
### Admin - Lotes (3 endpoints - Admin + Gerente)
### Admin - Clientes (3 endpoints - Variado)
### Admin - Alertas (2 endpoints - Admin + Gerente)
### Admin - Relatórios (5 endpoints - Admin + Gerente)
### Admin - Sacolas (6 endpoints - Variado)
### Admin - Exportação (3 endpoints - Admin + Gerente)
### Admin - Usuários (5 endpoints - Variado)
### Admin - Auditoria (1 endpoint - Admin + Gerente)
### Admin - Notificações (3 endpoints - Admin + Gerente)
### Admin - QR Codes (4 endpoints - Admin/Gerente)

*(Detalhamento completo dos 57 endpoints disponível em `/docs` de cada ambiente)*

---

## Banco de Dados

### Tabelas (8 total)

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
- entidade_tipo (Cliente/Sacola/Usuario/Alerta/Lote/QRCode)
- entidade_id (string)
- detalhes (JSON) - Inclui terminal, IP, dados específicos
- ip_address
- data_hora

#### notificacoes
- id (PK)
- cliente_cpf (FK)
- tipo (enum)
- titulo
- mensagem
- lida (bool)
- data_criacao

---

## Gerando QR Codes

### Opção 1: Via API (Recomendado)

#### 1. Fazer login como admin
```http
POST /api/auth/login
username: dev_admin
password: ProjetoBag+2026
```

#### 2. Gerar lote via Swagger
```http
POST /api/admin/qrcodes/gerar
Authorization: Bearer {token}

{
  "quantidade": 100,
  "formatos": ["csv", "pdf"]
}
```

**Response:**
```json
{
  "sucesso": true,
  "mensagem": "Lote de 100 QR Codes gerado com sucesso",
  "intervalo": "BAG-00001 até BAG-00100",
  "data_criacao": "2026-04-15",
  "links_download": {
    "csv": "/api/admin/qrcodes/download/csv/lote_00001-00100.csv",
    "pdf": "/api/admin/qrcodes/download/pdf/lote_00001-00100_IMPRESSAO.pdf"
  }
}
```

#### 3. Download dos arquivos
```http
GET /api/admin/qrcodes/download/csv/lote_00001-00100.csv
GET /api/admin/qrcodes/download/pdf/lote_00001-00100_IMPRESSAO.pdf
```

#### 4. Importar no Sistema
```http
POST /api/admin/lotes/importar
Authorization: Bearer {token}

data_fabricacao: 2026-03-31
inicio: 1
fim: 100
```

---

### Opção 2: Via Script CLI

#### 1. Executar script
```bash
cd scripts/qrcodes
python gerar_qrcodes.py
```

#### 2. Seguir prompts interativos
```
 Quantos QR Codes gerar? (1-10000): 100
 Data de criação [2026-04-15]: 
 Formatos: 1-CSV, 2-PDF, 3-Ambos [3]: 3
 Confirmar geração? (S/N): S
```

#### 3. Arquivos gerados
```
storage/qrcodes/
├── csv/lote_00001-00100.csv
├── pdf/lote_00001-00100_IMPRESSAO.pdf
└── ultimo_id.txt (atualizado para 100)
```

#### 4. Importar via API
```http
POST /api/admin/lotes/importar
data_fabricacao: 2026-03-31
inicio: 1
fim: 100
```

> **Sincronização:** API e CLI compartilham o mesmo `ultimo_id.txt`, garantindo sequência única!

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
username: caixa_teste
password: senha123
terminal: caixa 2
```

#### 1. Autorizar no Swagger
```
1. Abrir http://localhost:8000/docs
2. Clicar em "Authorize" (cadeado)
3. Colar: Bearer {token}
4. Clicar em "Authorize"
```

#### 2. Gerar QR Codes (Admin)
```http
POST /api/admin/qrcodes/gerar
{
  "quantidade": 5,
  "formatos": ["csv", "pdf"]
}
```

#### 3. Importar Lote
```http
POST /api/admin/lotes/importar
data_fabricacao: 2026-04-15
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
qr_code: BAG-00001:2026-04-15:757314  # Do CSV
cpf_cliente: 12345678900
```

#### 6. Registrar Uso (Caixa)
```http
POST /api/sacolas/registrar-uso
Authorization: Bearer {token_caixa_com_terminal}

sacola_id: BAG-00001
valor_compra: 125,50
```

#### 7. Ver Relatório por Terminal
```http
GET /api/admin/relatorios/vendas-por-terminal?data=2026-04-15
```

#### 8. Ver Dashboard
```http
GET /api/admin/relatorios/dashboard
```

#### 9. Consultar Logs de Auditoria
```http
GET /api/admin/auditoria/logs?usuario_username=caixa_teste
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
   - Autenticação obrigatória para registrar uso

3. **Controle de Acesso**
   - Sistema de suspensão de clientes
   - Bloqueio permanente quando necessário
   - Registro de motivos e datas

4. **Autenticação e Autorização**
   - JWT com expiração diferenciada (12h caixa, 24h admin/gerente)
   - Hash de senhas com bcrypt (custo 12)
   - Controle granular por roles (admin/gerente/caixa)
   - 35 endpoints protegidos
   - Middleware de autenticação automática
   - Sistema de terminais para rastreabilidade

5. **Auditoria Completa**
   - Histórico completo de eventos
   - Logs de todas ações administrativas
   - Rastreamento: quem, quando, onde (terminal), de onde (IP)
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
- Verificar formato: `BAG-00001:2026-04-15:checksum`

#### Erro: "Valor mínimo R$ 15,00"
- Sistema não aceita valores abaixo de R$ 15,00 (proteção anti-fraude)

#### Erro: "Not authenticated" ou "Insufficient permissions"
- Verificar se token JWT está sendo enviado no header Authorization
- Verificar se token não expirou (12h caixa, 24h admin/gerente)
- Verificar se usuário tem a role necessária para o endpoint
- Caixas precisam incluir terminal no login

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

**Versão:** v0.92-beta  
**Endpoints:** 57 funcionais  
**Atualizado:** 15/04/2026  
**Arquitetura:** Modular Monorepo + Docker  
**Status:** 🟢 Produção Online (AWS São Paulo)