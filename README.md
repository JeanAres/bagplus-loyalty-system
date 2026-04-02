# Bag+ - Sistema de Fidelização Sustentável

> **AVISO IMPORTANTE:** Este é um projeto comercial. O código está disponível 
> para avaliação e portfólio, mas **uso comercial requer licença**. 
> Entre em contato para implementação: jean06soares@gmail.com

Sistema completo de gerenciamento de sacolas reutilizáveis com programa de recompensas, QR Codes com segurança anti-falsificação, detecção automática de fraudes, sistema de suspensão de clientes, relatórios gerenciais e exportação de dados.

> Para entender o conceito e proposta do negócio, veja [PROPOSTA.md](PROPOSTA.md)

---

## Funcionalidades Implementadas

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

### Relatórios e Analytics
- **Dashboard administrativo** - Visão geral completa do negócio
- **Relatórios de vendas** - Por período com detalhamento diário
- **Estatísticas gerais** - Taxa de devolução, recordes, crescimento
- **Top performers** - Clientes que mais usam e mais gastam
- **Exportação CSV** - Clientes, sacolas e usos para análise externa

### Operações Especiais
- **Transferência de sacolas** - Entre clientes com rastreamento
- **Reset de contador** - Correção de erros com validação rigorosa
- **Sacolas próximas do limite** - Identificar sacolas perto de expirar

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

# 2. Criar ambiente virtual Python
python -m venv venv

# 3. Ativar ambiente virtual
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# 4. Instalar dependências
cd backend
pip install -r requirements.txt

# 5. Configurar variáveis de ambiente
# Copiar .env.example para .env e configurar SECRET_KEY
cp .env.example .env
notepad .env  # Adicionar SECRET_KEY única

# 6. Iniciar servidor
python main.py
```

O servidor estará rodando em `http://localhost:8000`

---

## Acessar Sistema

- **Documentação API (Swagger)**: `http://localhost:8000/docs`
- **Interface do Caixa**: `frontend-caixa/index.html` (em desenvolvimento)

---

## Estrutura do Projeto
```
bagplus-loyalty-system/
├── backend/                    # API FastAPI
│   ├── routers/               # Módulos da API (8 routers)
│   │   ├── clientes.py       # Endpoints públicos de clientes
│   │   ├── sacolas.py        # Endpoints públicos de sacolas
│   │   ├── admin_lotes.py    # Gestão de lotes
│   │   ├── admin_suspensao.py # Suspensão de clientes
│   │   ├── admin_alertas.py  # Sistema de alertas
│   │   ├── admin_relatorios.py # Dashboard e relatórios
│   │   ├── admin_sacolas.py  # Gestão de sacolas
│   │   └── admin_exportar.py # Exportação CSV
│   ├── main.py               # Servidor principal (32 endpoints)
│   ├── models.py             # Modelos do banco de dados
│   ├── database.py           # Configuração SQLAlchemy
│   ├── requirements.txt      # Dependências Python
│   └── .env                  # Variáveis de ambiente (SECRET_KEY)
├── scripts/                   # Scripts utilitários
│   ├── gerar_qrcodes.py      # Geração em massa de QR Codes
│   ├── limpar_qrcodes.py     # Limpeza de QR Codes antigos
│   └── seed_data.py          # Popular banco com dados de teste
├── qrcodes/                   # QR Codes gerados (ignorado no Git)
│   ├── lote_XXXXX.csv        # Dados do lote para importação
│   ├── lote_XXXXX_IMPRESSAO.pdf  # PDF para gráfica
│   └── ultimo_id.txt         # Controle de sequência
├── docs/                      # Documentação
│   └── SCANNER-REMOTE-KEYBOARD.md  # Como usar scanner
├── frontend-caixa/            # Interface web (futuro)
├── tests/                     # Testes automatizados (futuro)
├── README.md                  # Este arquivo
├── PROPOSTA.md               # Proposta de negócio
├── CONTRIBUTING.md           # Guia de contribuição
└── .gitignore                # Arquivos ignorados (qrcodes/, .env, etc)
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

### Geração de QR Codes
- **qrcode** - Geração de QR Codes
- **Pillow** - Manipulação de imagens
- **ReportLab** - Geração de PDFs

### Segurança
- **hashlib** - SHA256 para checksums
- **SECRET_KEY** - Chave secreta compartilhada

---

## API Endpoints (32 total)

### Clientes (8 endpoints)

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

### Sacolas (7 endpoints)

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

### Admin - Lotes (2 endpoints)

#### Importar Lote
```http
POST /api/admin/lotes/importar
Query Parameters:
  - data_fabricacao: string (YYYY-MM-DD)
  - inicio: int (ex: 1 para BAG-00001)
  - fim: int (ex: 5000 para BAG-05000)
Ação: Cria sacolas em status "estoque" com checksums
```

#### Listar Lotes
```http
GET /api/admin/lotes
Response: Todos lotes com distribuição (estoque/ativas/devolvidas)
```

---

### Admin - Clientes (3 endpoints)

#### Suspender Cliente
```http
POST /api/admin/clientes/{cpf}/suspender
Query Parameters:
  - cpf: string
  - motivo: string (min 10 caracteres)
```

#### Reativar Cliente
```http
POST /api/admin/clientes/{cpf}/reativar
Query Parameters:
  - cpf: string
```

#### Listar Clientes Suspensos
```http
GET /api/admin/clientes/suspensos
Response: Clientes suspensos ou bloqueados com motivos
```

---

### Admin - Alertas (2 endpoints)

#### Listar Alertas
```http
GET /api/admin/alertas
Query Parameters (opcionais):
  - resolvido: bool
  - gravidade: string (baixa/media/alta)
  - tipo: string
Response: Alertas detectados automaticamente
```

#### Resolver Alerta
```http
POST /api/admin/alertas/{alerta_id}/resolver
Query Parameters:
  - alerta_id: int
  - observacao: string (min 10 caracteres)
```

---

### Admin - Relatórios (3 endpoints)

#### Dashboard Administrativo
```http
GET /api/admin/relatorios/dashboard
Response: Visão geral do negócio (totais, financeiro, alertas, top performers, crescimento)
```

#### Relatório de Vendas
```http
GET /api/admin/relatorios/vendas
Query Parameters:
  - data_inicio: string (YYYY-MM-DD)
  - data_fim: string (YYYY-MM-DD)
Response: Resumo geral, detalhamento diário, top performers do período
```

#### Estatísticas Gerais
```http
GET /api/admin/relatorios/estatisticas
Response: Taxa devolução, tempo médio uso, recordes, performance financeira, crescimento
```

---

### Admin - Sacolas (4 endpoints)

#### Sacolas Próximas do Limite
```http
GET /api/admin/sacolas/proximo-limite?limite=35
Response: Sacolas com 35+ usos (perto de expirar)
```

#### Consultar Estoque
```http
GET /api/admin/sacolas/estoque?lote_id=1
Response: Sacolas disponíveis (nunca distribuídas)
```

#### Transferir Sacola
```http
POST /api/admin/sacolas/{sacola_id}/transferir
Query Parameters:
  - cpf_origem: string
  - cpf_destino: string
  - motivo: string (min 10 caracteres)
Ação: Transfere propriedade preservando histórico
```

#### Resetar Contador
```http
POST /api/admin/sacolas/{sacola_id}/resetar-contador
Query Parameters:
  - motivo: string (min 15 caracteres)
Ação: Reseta utilizações para 0 (operação sensível)
```

---

### Admin - Exportação (3 endpoints)

#### Exportar Clientes
```http
GET /api/admin/exportar/clientes
Query Parameters (opcionais):
  - status: string (ativo/suspenso/bloqueado)
  - data_inicio: string (YYYY-MM-DD)
  - data_fim: string (YYYY-MM-DD)
Response: CSV com CPF, Nome, Status, Sacolas Ativas, Total Gasto
```

#### Exportar Sacolas
```http
GET /api/admin/exportar/sacolas
Query Parameters (opcionais):
  - status: string (estoque/ativo/devolvido)
  - lote_id: int
Response: CSV com ID, Status, Cliente, Utilizações, Estado, Lote
```

#### Exportar Usos
```http
GET /api/admin/exportar/usos
Query Parameters (opcionais):
  - data_inicio: string (YYYY-MM-DD)
  - data_fim: string (YYYY-MM-DD)
  - cpf: string
Response: CSV com Data/Hora, Sacola, Cliente, Valor
```

> **Documentação completa e interativa:** `http://localhost:8000/docs`

---

## Banco de Dados

### Tabelas

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
python gerar_qrcodes.py
```

**Confirmar com 'S'**

### 3. Arquivos Gerados
```
qrcodes/
├── lote_00001-05000.csv              # Importar no sistema
├── lote_00001-05000_IMPRESSAO.pdf    # Enviar para gráfica
└── ultimo_id.txt                     # Controle automático
```

### 4. Importar no Sistema
```http
POST /api/admin/lotes/importar
data_fabricacao: 2026-03-31
inicio: 1
fim: 5000
```

> **Otimização:** Não gera PNGs individuais (economia de 50MB e 5.000 arquivos)

---

## Testando o Sistema

### Fluxo Completo de Teste

#### 1. Gerar QR Codes
```bash
cd scripts
python gerar_qrcodes.py
# Confirmar com S
# Resultado: CSV + PDF gerados
```

#### 2. Importar Lote
```http
POST /api/admin/lotes/importar
data_fabricacao: 2026-03-31
inicio: 1
fim: 5
```

#### 3. Cadastrar Cliente
```http
POST /api/clientes
cpf: 12345678900
nome: João Silva
```

#### 4. Ativar Sacola
```http
POST /api/sacolas/ativar
qr_code: BAG-00001:2026-03-31:757314  # Copiar do CSV
cpf_cliente: 12345678900
```

#### 5. Registrar Uso
```http
POST /api/sacolas/registrar-uso
sacola_id: BAG-00001
valor_compra: 125,50
```

#### 6. Ver Dashboard
```http
GET /api/admin/relatorios/dashboard
```

#### 7. Exportar Dados
```http
GET /api/admin/exportar/usos
```

---

## Configuração

### Variáveis de Ambiente (.env)
```env
# Banco de Dados
DATABASE_URL=sqlite:///./bagplus.db

# Segurança (OBRIGATÓRIO)
SECRET_KEY=sua_chave_secreta_unica_aqui_256bits

# Servidor
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
```

> **IMPORTANTE:** A mesma `SECRET_KEY` deve estar no servidor e no script de geração de QR Codes

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

4. **Auditoria**
   - Histórico completo de eventos
   - Exportação de dados para análise
   - Rastreamento de transferências e resets

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

---

## Roadmap

### Próximas Funcionalidades
- [ ] Interface web do caixa (HTML/CSS/JS)
- [ ] Dashboard administrativo (React/Next.js)
- [ ] Sistema de autenticação (JWT)
- [ ] App mobile cliente (React Native)
- [ ] Migração SQLite para PostgreSQL
- [ ] Testes automatizados
- [ ] Deploy em produção

---

## Contato

**Email:** jean06soares@gmail.com  
**GitHub:** https://github.com/JeanAres/bagplus-loyalty-system

---

## Licença

Este é um projeto comercial proprietário. O código está disponível para avaliação, mas uso comercial requer licença.

---

**Bag+** - Sua sacola vale mais.🌱♻️