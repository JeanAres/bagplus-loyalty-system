# Bag+ - Sistema de Fidelização Sustentável

> ⚠️ **AVISO IMPORTANTE:** Este é um projeto comercial. O código está disponível 
> para avaliação e portfólio, mas **uso comercial requer licença**. 
> Entre em contato para implementação: jean06soares@gmail.com

Sistema completo de gerenciamento de sacolas reutilizáveis com programa de recompensas.

> Para entender o conceito e proposta do negócio, veja [PROPOSTA.md](PROPOSTA.md)

## Início Rápido

### Pré-requisitos

- Python 3.8+
- Node.js (opcional, se usar npm)
- Navegador moderno

### Instalação
```bash
# 1. Clonar repositório
git clone https://github.com/SEU-USUARIO/bagplus-loyalty-system.git
cd bagplus-loyalty-system

# 2. Criar ambiente virtual Python
cd backend
python -m venv venv

# 3. Ativar ambiente virtual
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Popular banco com dados de teste
python ../scripts/seed_data.py

# 6. Iniciar servidor
python main.py
```

O servidor estará rodando em `http://localhost:8000`

### Acessar Sistema

- **Interface do Caixa**: Abra `frontend-caixa/index.html` no navegador
- **Documentação API**: `http://localhost:8000/docs`

---

## Estrutura do Projeto
```
bagplus-loyalty-system/
├── backend/              # API FastAPI
│   ├── main.py          # Servidor principal
│   ├── models.py        # Modelos do banco de dados
│   ├── database.py      # Configuração do banco
│   ├── requirements.txt # Dependências Python
│   └── .env             # Variáveis de ambiente
├── frontend-caixa/      # Interface web do caixa
│   ├── index.html       # Página principal
│   ├── style.css        # Estilos
│   └── app.js           # Lógica do frontend
├── scripts/             # Scripts utilitários
│   └── seed_data.py     # Popular banco com dados teste
├── tests/               # Testes automatizados
│   └── test_db.py       # Testes do banco
├── docs/                # Documentação adicional
├── database/            # Banco de dados (gerado automaticamente)
├── app-cliente/         # App do cliente (futuro)
├── README.md            # Este arquivo
├── PROPOSTA.md          # Proposta de negócio
└── CONTRIBUTING.md      # Guia de contribuição
```

---

## Tecnologias

### Backend
- **FastAPI** - Framework web Python moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **SQLite** - Banco de dados (desenvolvimento)
- **Uvicorn** - Servidor ASGI

### Frontend
- **HTML/CSS/JavaScript** - Interface web pura
- **Fetch API** - Comunicação com backend

### Futuro
- **PostgreSQL** - Banco para produção
- **React Native/Flutter** - App mobile do cliente

---

## API Endpoints

### Clientes

**Criar Cliente**
```http
POST /api/clientes
Query: cpf, nome
```

**Listar Sacolas do Cliente**
```http
GET /api/clientes/{cpf}/sacolas
```

### Sacolas

**Buscar Sacola**
```http
GET /api/sacolas/{sacola_id}
```

**Criar Lote de Sacolas**
```http
POST /api/sacolas/criar-lote
Query: cpf_cliente, quantidade
```

**Registrar Uso**
```http
POST /api/sacolas/registrar-uso
Query: sacola_id
```

**Devolver Sacola**
```http
POST /api/sacolas/devolver
Query: sacola_id
```

> Documentação completa: `http://localhost:8000/docs` (Swagger)

---

## Banco de Dados

### Tabelas

- **clientes** - Dados dos clientes cadastrados
- **sacolas** - Sacolas individuais rastreáveis
- **registros_uso** - Histórico de utilizações
- **devolucoes** - Histórico de devoluções

> Ver detalhes em [database/README.md](database/README.md)

---

## Testando o Sistema

### 1. Popular com Dados de Teste
```bash
python scripts/seed_data.py
```

Isso cria:
- 5 clientes fictícios
- 15 sacolas em estados variados (novas, médias, antigas)

### 2. Testar no Sistema de Caixa

1. Abra `frontend-caixa/index.html`
2. Teste busca por código: `BAG-00001`
3. Teste busca por CPF: `123.456.789-00`
4. Registre usos
5. Processe devoluções

### 3. Testar API Diretamente

Acesse `http://localhost:8000/docs` e teste os endpoints interativamente.

---

## Configuração

### Variáveis de Ambiente (.env)
```env
DATABASE_URL=sqlite:///./bagplus.db
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Deploy

### Desenvolvimento (Local)
Já está configurado! Basta seguir o "Início Rápido".

### Produção (Futuro)

1. **Migrar para PostgreSQL**
   - Alterar `DATABASE_URL` no `.env`
   
2. **Deploy Backend**
   - Railway, Heroku, AWS, ou servidor próprio
   
3. **Deploy Frontend**
   - Netlify, Vercel, ou servir via backend

4. **Adicionar Autenticação**
   - Sistema de login para operadores
   - JWT tokens

> Ver roadmap completo em [docs/README.md](docs/README.md)

---

## Troubleshooting

### Erro: "Module not found"
```bash
pip install -r backend/requirements.txt
```

### Erro: "Address already in use"
Porta 8000 já está em uso. Mate o processo:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Banco não aparece
O banco é criado automaticamente ao iniciar o servidor pela primeira vez.

---

## Contribuindo

Leia [CONTRIBUTING.md](CONTRIBUTING.md) para:
- Convenções de commits
- Padrões de código
- Processo de Pull Request

---

##Contato

jean06soares@gmail.com

---

**Bag+** - Sua sacola vale mais. 🌱