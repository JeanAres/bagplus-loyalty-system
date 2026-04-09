# Bag+ - Sistema de Fidelização Sustentável

> **AVISO IMPORTANTE:** Este é um projeto comercial. O código está disponível 
> para avaliação e portfólio, mas **uso comercial requer licença**. 
> Entre em contato para implementação: jean06soares@gmail.com

Sistema completo de gerenciamento de sacolas reutilizáveis com programa de recompensas, autenticação JWT com roles, QR Codes com segurança anti-falsificação, detecção automática de fraudes, sistema de suspensão de clientes, relatórios gerenciais avançados, logs de auditoria e exportação de dados.

> Para entender o conceito e proposta do negócio, veja [PROPOSTA.md](PROPOSTA.md)

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

### Pré-requisitos

- Python 3.8+
- SQLite (já incluso no Python)
- Navegador moderno (Chrome/Firefox/Edge)

### Instalação
```bash
# 1. Clonar repositório
git clone https://github.com/JeanAres/bagplus-loyalty-system.git
cd bagplus-loyalty-system

# 2. Navegar para backend
cd services/backend

# 3. Criar ambiente virtual Python
python -m venv venv

# 4. Ativar ambiente virtual
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# 5. Instalar dependências
pip install -r requirements.txt

# 6. Configurar variáveis de ambiente
# Copiar .env.example para .env e configurar SECRET_KEY
cp .env.example .env
notepad .env  # Adicionar SECRET_KEY única

# 7. Iniciar servidor
python run.py
```

O servidor estará rodando em `http://localhost:8000`

**Token JWT de desenvolvimento será exibido no console!**

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

#### Admin (Acesso Total)
-  Todos os endpoints administrativos
-  Criar, editar e desativar usuários
-  Suspender e reativar clientes
-  Transferir sacolas entre clientes
-  Resetar contador de utilizações
-  Todos relatórios e exportações
-  Ver logs de auditoria

####  Gerente (Acesso Gerencial)
-  Dashboard e relatórios
-  Importar e gerenciar lotes
-  Listar e resolver alertas
-  Exportar dados (CSV)
-  Consultar estoque
-  Listar usuários (read-only)
-  Ver logs de auditoria
-  Suspender/reativar clientes
-  Transferir sacolas
-  Resetar contador
-  Criar/editar usuários

####  Caixa (Operacional Apenas)
-  Cadastrar clientes
-  Ativar sacolas
-  Registrar uso de sacolas
-  Devolver sacolas
-  Buscar clientes e sacolas
-  Nenhum acesso a endpoints admin

---

## Acessar Sistema

- **Documentação API (Swagger)**: `http://localhost:8000/docs`
- **Interface do Caixa**: `frontend-caixa/index.html` (em desenvolvimento)

---

## Estrutura do Projeto
````
bagplus-loyalty-system/
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
│       │   └── swagger/
│       │       ├── config/
│       │       └── styles/
│       ├── scripts/          # Scripts de desenvolvimento
│       │   └── dev_setup.py
│       ├── data/             # Banco de dados
│       │   └── bagplus.db
│       ├── run.py            # Launcher principal
│       ├── requirements.txt
│       └── .env
├── apps/                      # Frontends (preparado)
│   └── shared/               # Componentes compartilhados
├── storage/                   # Arquivos gerados
│   └── qrcodes/
│       ├── csv/              # CSVs dos lotes
│       ├── pdf/              # PDFs para impressão
│       └── ultimo_id.txt     # Controle de sequência
├── scripts/                   # Scripts auxiliares
│   ├── qrcodes/
│   │   ├── gerar_qrcodes.py
│   │   └── limpar_qrcodes.py
│   └── database/
│       └── seed_data.py
├── infra/                    # Infraestrutura
│   └── database/
├── docs/                     # Documentação geral
│   └── SCANNER-REMOTE-KEYBOARD.md
├── tests/                    # Testes (preparado)
├── README.md
├── PROPOSTA.md
├── CONTRIBUTING.md
└── .gitignore
````

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

### Segurança
- **hashlib** - SHA256 para checksums
- **SECRET_KEY** - Chave secreta compartilhada

---

## API Endpoints (45 total)

### Clientes (8 endpoints - Públicos)

#### Criar Cliente
```http
POST /api/clientes
Query Parameters:
  - cpf: string (11 dígitos)
  - nome: string (min 3 caracteres)
```

#### Listar Clientes
```http
GET /api/clientes
Response: Lista de clientes com sacolas ativas e status
```

#### Buscar Cliente por Nome
```http
GET /api/clientes/buscar?nome=joão
Response: Lista de clientes que correspondem ao termo (parcial, case-insensitive)
```

#### Validar CPF
```http
GET /api/clientes/{cpf}/validar
Response: Verifica se cliente existe sem criar cadastro
```

#### Listar Sacolas do Cliente
```http
GET /api/clientes/{cpf}/sacolas
Response: Sacolas ativas do cliente com estatísticas
```

#### Estatísticas do Cliente
```http
GET /api/clientes/{cpf}/estatisticas
Response: Total gasto, valor médio, total de usos
```

#### Histórico Completo do Cliente
```http
GET /api/clientes/{cpf}/historico-completo
Response: Timeline completa com eventos, compras, alertas, suspensões
```

#### Excluir Cliente (Restritivo)
```http
DELETE /api/clientes/{cpf}
Validações: Bloqueia se cliente tem histórico (sacolas/alertas)
```

---

### Sacolas (7 endpoints - Públicos)

#### Buscar Sacola
```http
GET /api/sacolas/{sacola_id}
Response: Informações completas, descontos, estado, fidelidade
```

#### Listar Sacolas Ativas
```http
GET /api/sacolas/ativas
Response: Todas as sacolas em uso
```

#### Ativar Sacola
```http
POST /api/sacolas/ativar
Query Parameters:
  - qr_code: string (formato: BAG-00001:2026-03-31:checksum)
  - cpf_cliente: string
Validações:
  - Checksum SHA256
  - Status deve ser "estoque"
  - Cliente deve existir
```

#### Registrar Uso
```http
POST /api/sacolas/registrar-uso
Query Parameters:
  - sacola_id: string
  - valor_compra: string (aceita vírgula ou ponto)
Validações:
  - Intervalo mínimo 4 horas desde último uso
  - Valor mínimo R$ 15,00
  - Cliente não pode estar suspenso
  - Máximo 40 utilizações
Ações Automáticas:
  - Detecta padrões suspeitos
  - Gera alertas se necessário
```

#### Devolver Sacola
```http
POST /api/sacolas/devolver
Query Parameters:
  - sacola_id: string
Response: Desconto concedido baseado no estado
```

#### Histórico de Uso
```http
GET /api/sacolas/{sacola_id}/historico
Response: Histórico completo com valores, total gasto, valor médio
```

#### Verificar QR Code
```http
POST /api/sacolas/verificar-qr
Query Parameters:
  - qr_code: string
Response: Valida checksum sem ativar sacola
```

---

### Autenticação (3 endpoints - Públicos)

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username: string
password: string

Response: JWT token + dados do usuário
```

#### Informações do Usuário Logado
```http
GET /api/auth/me
Authorization: Bearer {token}

Response: Dados do usuário autenticado
```

#### Token de Desenvolvimento (Dev Only)
```http
GET /api/auth/dev-token

Response: Token JWT válido para testes (apenas em ENVIRONMENT=development)
```

---

### Admin - Lotes (3 endpoints - Admin + Gerente)

#### Importar Lote
```http
POST /api/admin/lotes/importar
Authorization: Bearer {token}
Query Parameters:
  - data_fabricacao: string (YYYY-MM-DD)
  - inicio: int (ex: 1 para BAG-00001)
  - fim: int (ex: 5000 para BAG-05000)
Ação: Cria sacolas em status "estoque" com checksums
```

#### Listar Lotes
```http
GET /api/admin/lotes
Authorization: Bearer {token}
Response: Todos lotes com distribuição (estoque/ativas/devolvidas)
```

#### Estatísticas do Lote
```http
GET /api/admin/lotes/{lote_id}/estatisticas
Authorization: Bearer {token}
Response: Distribuição detalhada por status, taxa de utilização
```

---

### Admin - Clientes (3 endpoints - Variado)

#### Suspender Cliente
```http
POST /api/admin/clientes/{cpf}/suspender
Authorization: Bearer {token}
Permissão: Admin apenas
Query Parameters:
  - cpf: string
  - motivo: string (min 10 caracteres)
Ação: Registra log de auditoria
```

#### Reativar Cliente
```http
POST /api/admin/clientes/{cpf}/reativar
Authorization: Bearer {token}
Permissão: Admin apenas
Query Parameters:
  - cpf: string
Ação: Registra log de auditoria
```

#### Listar Clientes Suspensos
```http
GET /api/admin/clientes/suspensos
Authorization: Bearer {token}
Permissão: Admin + Gerente
Response: Clientes suspensos ou bloqueados com motivos
```

---

### Admin - Alertas (2 endpoints - Admin + Gerente)

#### Listar Alertas
```http
GET /api/admin/alertas
Authorization: Bearer {token}
Query Parameters (opcionais):
  - resolvido: bool
  - gravidade: string (baixa/media/alta)
  - tipo: string
Response: Alertas detectados automaticamente
```

#### Resolver Alerta
```http
POST /api/admin/alertas/{alerta_id}/resolver
Authorization: Bearer {token}
Query Parameters:
  - alerta_id: int
  - observacao: string (min 10 caracteres)
Ação: Registra log de auditoria
```

---

### Admin - Relatórios (4 endpoints - Admin + Gerente)

#### Dashboard Administrativo
```http
GET /api/admin/relatorios/dashboard
Authorization: Bearer {token}
Response: Visão geral do negócio (totais, financeiro, alertas, top performers, crescimento)
```

#### Relatório de Vendas
```http
GET /api/admin/relatorios/vendas
Authorization: Bearer {token}
Query Parameters:
  - data_inicio: string (YYYY-MM-DD)
  - data_fim: string (YYYY-MM-DD)
Response: Resumo geral, detalhamento diário, top performers do período
```

#### Estatísticas Gerais
```http
GET /api/admin/relatorios/estatisticas
Authorization: Bearer {token}
Response: Taxa devolução, tempo médio uso, recordes, performance financeira, crescimento
```

#### Análise de Crescimento Month-over-Month
```http
GET /api/admin/relatorios/crescimento
Authorization: Bearer {token}
Query Parameters (opcionais):
  - meses: int (padrão 6, últimos N meses)
Response: Análise comparativa mês a mês (novos clientes, sacolas ativadas, total gasto)
```

---

### Admin - Sacolas (6 endpoints - Variado)

#### Sacolas Próximas do Limite
```http
GET /api/admin/sacolas/proximo-limite?limite=35
Authorization: Bearer {token}
Permissão: Admin + Gerente
Response: Sacolas com 35+ usos (perto de expirar)
```

#### Consultar Estoque
```http
GET /api/admin/sacolas/estoque?lote_id=1
Authorization: Bearer {token}
Permissão: Admin + Gerente
Response: Sacolas disponíveis (nunca distribuídas)
```

#### Transferir Sacola
```http
POST /api/admin/sacolas/{sacola_id}/transferir
Authorization: Bearer {token}
Permissão: Admin apenas
Query Parameters:
  - cpf_origem: string
  - cpf_destino: string
  - motivo: string (min 10 caracteres)
Ação: Transfere propriedade preservando histórico + log de auditoria
```

#### Resetar Contador
```http
POST /api/admin/sacolas/{sacola_id}/resetar-contador
Authorization: Bearer {token}
Permissão: Admin apenas
Query Parameters:
  - motivo: string (min 15 caracteres)
Ação: Reseta utilizações para 0 (operação sensível) + log de auditoria
```

#### Identificar Sacolas em Risco
```http
GET /api/admin/sacolas/em-risco
Authorization: Bearer {token}
Permissão: Admin + Gerente
Response: 
  - prolongado_sem_uso: Sacolas ativas sem uso há 30+ dias
  - uso_intensivo: Sacolas com 25+ usos (próximo do limite)
  - multiplas_perto_limite: Clientes com 2+ sacolas acima de 30 usos
```

---

### Admin - Exportação (3 endpoints - Admin + Gerente)

#### Exportar Clientes
```http
GET /api/admin/exportar/clientes
Authorization: Bearer {token}
Query Parameters (opcionais):
  - status: string (ativo/suspenso/bloqueado)
  - data_inicio: string (YYYY-MM-DD)
  - data_fim: string (YYYY-MM-DD)
Response: CSV com CPF, Nome, Status, Sacolas Ativas, Total Gasto (UTF-8 BOM para Excel)
```

#### Exportar Sacolas
```http
GET /api/admin/exportar/sacolas
Authorization: Bearer {token}
Query Parameters (opcionais):
  - status: string (estoque/ativo/devolvido)
  - lote_id: int
Response: CSV com ID, Status, Cliente, Utilizações, Estado, Lote (UTF-8 BOM)
```

#### Exportar Usos
```http
GET /api/admin/exportar/usos
Authorization: Bearer {token}
Query Parameters (opcionais):
  - data_inicio: string (YYYY-MM-DD)
  - data_fim: string (YYYY-MM-DD)
  - cpf: string
Response: CSV com Data/Hora, Sacola, Cliente, Valor (UTF-8 BOM)
```

---

### Admin - Usuários (5 endpoints - Variado)

#### Criar Usuário
```http
POST /api/admin/usuarios
Authorization: Bearer {token}
Permissão: Admin apenas
Query Parameters:
  - username: string (único, min 3 caracteres)
  - password: string (min 6 caracteres)
  - nome: string
  - role: string (admin/gerente/caixa)
Ação: Hash bcrypt da senha + log de auditoria
```

#### Listar Usuários
```http
GET /api/admin/usuarios
Authorization: Bearer {token}
Permissão: Admin + Gerente
Query Parameters (opcionais):
  - ativo: bool
  - role: string
Response: Lista de usuários (senha omitida)
```

#### Buscar Usuário
```http
GET /api/admin/usuarios/{usuario_id}
Authorization: Bearer {token}
Permissão: Admin + Gerente
Response: Dados do usuário (senha omitida)
```

#### Editar Usuário
```http
PUT /api/admin/usuarios/{usuario_id}
Authorization: Bearer {token}
Permissão: Admin apenas
Query Parameters (opcionais):
  - nome: string
  - role: string
  - password: string (se fornecido, será re-hasheado)
Ação: Log de auditoria
```

#### Desativar Usuário
```http
DELETE /api/admin/usuarios/{usuario_id}
Authorization: Bearer {token}
Permissão: Admin apenas
Ação: Marca usuário como inativo (soft delete) + log de auditoria
```

---

### Admin - Auditoria (1 endpoint - Admin + Gerente)

#### Consultar Logs de Auditoria
```http
GET /api/admin/auditoria/logs
Authorization: Bearer {token}
Query Parameters (opcionais):
  - data_inicio: string (YYYY-MM-DD)
  - data_fim: string (YYYY-MM-DD)
  - usuario_id: int
  - usuario_username: string
  - acao: string
  - entidade_tipo: string (Cliente/Sacola/Usuario/Alerta/Lote)
  - entidade_id: string
  - limit: int (padrão 100, máx 1000)
Response: Logs com usuário, ação, entidade, detalhes JSON, timestamp, IP
```

> **Documentação completa e interativa:** `http://localhost:8000/docs`

---

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

#### usuarios (NOVO - Sprint 6)
- id (PK)
- username (único)
- password_hash (bcrypt)
- nome
- role (admin/gerente/caixa)
- ativo (bool)
- data_criacao
- ultimo_login

#### logs_auditoria (NOVO - Sprint 6)
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
python main.py

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
DATABASE_URL=sqlite:///./bagplus.db

# Segurança (OBRIGATÓRIO)
SECRET_KEY=sua_chave_secreta_unica_aqui_256bits

# Autenticação JWT
JWT_SECRET_KEY=outra_chave_secreta_para_jwt_256bits
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Usuário Admin de Desenvolvimento (criado automaticamente)
DEV_ADMIN_USERNAME=xxxxxxx
DEV_ADMIN_PASSWORD=xxxxxxx

# Servidor
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
```

> **IMPORTANTE:** 
> - A mesma `SECRET_KEY` deve estar no servidor e no script de geração de QR Codes
> - `DEV_ADMIN_USERNAME` e `DEV_ADMIN_PASSWORD` são criados automaticamente em modo development
> - Em produção, definir `ENVIRONMENT=production` desativa criação automática

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

4. **Autenticação e Autorização** (NOVO - Sprint 6)
   - JWT com expiração de 24h
   - Hash de senhas com bcrypt (custo 12)
   - Controle granular por roles (admin/gerente/caixa)
   - 31 endpoints protegidos
   - Middleware de autenticação automática

5. **Auditoria Completa** (NOVO - Sprint 6)
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
pip install -r backend/requirements.txt
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

**Versão:** v0.90-beta | **52 endpoints funcionais** | **Atualizado:** 08/04/2026 | **Arquitetura:** Modular Monorepo