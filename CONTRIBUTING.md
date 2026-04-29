# Como Contribuir

## Sobre o Projeto

Este é um **monorepo** que contém:
- **Backend** (FastAPI) em `services/backend/`
- **4 Frontends** em `apps/` (caixa, gestor, admin, cliente)
- **Scripts** auxiliares em `scripts/`
- **Infraestrutura** em `infra/`
- **Storage** de arquivos em `storage/`

---

## Ambientes

### **Produção**
- **URL:** https://api.bagplus.com.br/docs
- **Branch:** `main`
- **Banco:** bagplus_prod.db (dados reais)
- **Deploy:** Manual após validação em staging
- **Container:** bagplus_backend_prod

### **Staging**
- **URL:** https://staging.bagplus.com.br/docs
- **Branch:** `dev`
- **Banco:** bagplus_staging.db (dados fake para testes)
- **Deploy:** Manual após merge em dev
- **Container:** bagplus_backend_staging

### **Local**
- **URL:** http://localhost:8000/docs
- **Branch:** `dev`
- **Banco:** bagplus.db (local)
- **Container:** bagplus_backend_local (opcional)

---

## Estratégia de Branches

### Branches Principais

- **`main`**: Código em produção
  - Deploy: https://api.bagplus.com.br
  - Sempre estável e testado
  - Apenas código validado em staging
  - Merge apenas via Pull Request

- **`dev`**: Desenvolvimento ativo
  - Deploy: https://staging.bagplus.com.br
  - Branch padrão para desenvolvimento
  - Testes e validação antes de produção
  - Aceita features via Pull Request

### Fluxo de Trabalho

```
1. Desenvolver em feature/* branch
   ↓
2. PR para dev
   ↓
3. Deploy em staging (teste com dados fake)
   ↓
4. Validação em staging
   ↓
5. PR de dev para main
   ↓
6. Deploy em produção (dados reais)
```

**IMPORTANTE:** 
- Todo desenvolvimento começa em `dev`
- Produção (`main`) só recebe código testado em staging
- NUNCA fazer commit direto em `main`

---

## Fluxo de Contribuição

### 1. **Clone o repositório**
```bash
git clone https://github.com/JeanAres/bagplus-loyalty-system.git
cd bagplus-loyalty-system
```

### 2. **Certifique-se de estar em `dev`**
```bash
git checkout dev
git pull origin dev
```

### 3. **Crie uma branch para sua feature**
```bash
git checkout -b feature/MinhaFeature
```

### 4. **Faça suas alterações**
- Siga os padrões de código
- Teste suas mudanças localmente
- Documente quando necessário

### 5. **Commit seguindo convenções**
```bash
git add .
git commit -m "feat(backend): adiciona validação de CPF"
```

### 6. **Push para o repositório**
```bash
git push origin feature/MinhaFeature
```

### 7. **Abra um Pull Request**
- Base: `dev` (não `main`)
- Descreva claramente as mudanças
- Referencie issues relacionadas
- Aguarde review

### 8. **Após merge em dev: Deploy em Staging**
```bash
# SSH no servidor
ssh -i <sua-chave>.pem <usuario>@<ip-servidor>

# Atualizar código
cd bagplus-loyalty-system
git checkout dev
git pull origin dev

# Rebuild container de staging
sudo docker-compose up -d --build backend-staging

# Verificar logs
sudo docker-compose logs -f backend-staging
```

### 9. **Testar em staging**
- Acessar: https://staging.bagplus.com.br/docs
- Testar funcionalidade nova com dados fake
- Verificar se não quebrou nada

### 10. **Se OK: Deploy em Produção**
```bash
# No seu PC: Merge dev → main
git checkout main
git pull origin main
git merge dev
git push origin main

# SSH no servidor
ssh -i <sua-chave>.pem <usuario>@<ip-servidor>

# Atualizar código
cd bagplus-loyalty-system
git checkout main
git pull origin main

# Rebuild container de produção
sudo docker-compose up -d --build backend-prod

# Verificar logs
sudo docker-compose logs -f backend-prod
```

---

## Deploy

### Deploy em Staging

**Quando:** Após merge de feature em `dev`

**Passos:**
1. SSH no servidor AWS
2. Ir para pasta do projeto
3. Atualizar branch `dev`
4. Rebuild container de staging
5. Testar no Swagger de staging

**Comandos:**
```bash
ssh -i <sua-chave>.pem <usuario>@<ip-servidor>
cd bagplus-loyalty-system
git checkout dev
git pull origin dev
sudo docker-compose up -d --build backend-staging
```

**Verificar:**
```bash
sudo docker-compose ps
sudo docker-compose logs backend-staging
```

**Testar:**
- URL: https://staging.bagplus.com.br/docs
- Usar dados fake
- Verificar novos endpoints
- Testar fluxos completos

---

### Deploy em Produção

**Quando:** Após validação bem-sucedida em staging

**Pré-requisitos:**
- Testado em staging
- Sem erros nos logs
- Aprovação do time
- Dados fake funcionaram

**Passos:**

#### No seu PC:
```bash
# Certifique-se que dev está atualizado
git checkout dev
git pull origin dev

# Merge para main
git checkout main
git pull origin main
git merge dev

# Resolver conflitos se houver
# Testar localmente se possível

# Push para GitHub
git push origin main
```

#### No servidor AWS:
```bash
# SSH no servidor
ssh -i <sua-chave>.pem <usuario>@<ip-servidor>

# Ir para projeto
cd bagplus-loyalty-system

# Atualizar main
git checkout main
git pull origin main

# Rebuild produção
sudo docker-compose up -d --build backend-prod

# Verificar logs
sudo docker-compose logs -f backend-prod
```

**Verificar:**
```bash
# Status dos containers
sudo docker-compose ps

# Logs de produção
sudo docker-compose logs backend-prod --tail=100

# Logs de staging (não deve afetar)
sudo docker-compose logs backend-staging --tail=50
```

**Testar:**
- URL: https://api.bagplus.com.br/docs
- Testar endpoints críticos
- Verificar se staging ainda funciona
- Monitorar por 5-10 minutos

---

### Rollback (Se algo der errado)

**Se produção quebrou:**

```bash
# No seu PC
git checkout main
git log --oneline  # Ver commits recentes
git revert <commit-hash-do-problema>
git push origin main

# No servidor
ssh -i <sua-chave>.pem <usuario>@<ip-servidor>
cd bagplus-loyalty-system
git checkout main
git pull origin main
sudo docker-compose up -d --build backend-prod
```

**Ou voltar para versão anterior:**
```bash
# No servidor
git checkout main
git reset --hard <commit-hash-que-funcionava>
git push origin main --force
sudo docker-compose up -d --build backend-prod
```

---

## Convenção de Commits

Este projeto segue o padrão **Conventional Commits**.

### Formato

```
<tipo>(<escopo>): <descrição>

[corpo opcional]

[rodapé opcional]
```

### Tipos de Commit

| Tipo | Quando usar | Exemplo |
|------|-------------|---------|
| **feat** | Nova funcionalidade | `feat(backend): adiciona rate limiting` |
| **fix** | Correção de bug | `fix(caixa): corrige validação de CPF` |
| **refactor** | Refatoração (sem mudar comportamento) | `refactor(backend): reorganiza routers` |
| **docs** | Alterações na documentação | `docs(readme): atualiza instruções` |
| **style** | Formatação de código | `style(backend): aplica Black formatter` |
| **test** | Adição/modificação de testes | `test(backend): adiciona testes de autenticação` |
| **chore** | Manutenção, dependências | `chore(deps): atualiza FastAPI para 0.109.0` |
| **perf** | Melhorias de performance | `perf(backend): otimiza query de relatórios` |
| **ci** | CI/CD | `ci(github): adiciona workflow de testes` |
| **build** | Sistema de build | `build(docker): configura container de produção` |

---

## Escopos (Monorepo)

### Backend
- `backend` - Código geral do backend
- `api` - Endpoints específicos
- `auth` - Autenticação/autorização
- `database` - Banco de dados e models
- `core` - Lógica de negócio central
- `qrcodes` - Sistema de QR Codes

### Frontends
- `caixa` - Interface do operador de caixa
- `gestor` - Dashboard gerencial
- `admin` - Painel administrativo
- `cliente` - App do cliente (mobile/web)
- `shared` - Componentes compartilhados

### Infraestrutura
- `infra` - Configurações de infraestrutura
- `scripts` - Scripts auxiliares
- `docker` - Configurações Docker
- `ci` - CI/CD pipelines

### Documentação
- `docs` - Documentação geral
- `readme` - Arquivo README
- `roadmap` - Roadmap do projeto
- `contributing` - Guia de contribuição

---

## Exemplos de Commits Corretos

```bash
# Backend
git commit -m "feat(backend): implementa sistema de notificações"
git commit -m "fix(api): corrige endpoint de exportação CSV"
git commit -m "refactor(auth): simplifica middleware JWT"
git commit -m "feat(backend): adiciona validação de CPF"
git commit -m "feat(qrcodes): implementa API de geração de QR Codes"

# Frontend
git commit -m "feat(caixa): adiciona tela de cadastro de cliente"
git commit -m "fix(gestor): corrige gráfico de vendas MoM"
git commit -m "style(admin): aplica tema dark mode"

# Infraestrutura
git commit -m "chore(deps): atualiza dependencies do backend"
git commit -m "ci(github): configura deploy automático"
git commit -m "docs(contributing): atualiza guia de contribuição"
git commit -m "build(docker): adiciona ambiente de staging"

# Estrutura
git commit -m "refactor: reestrutura projeto em monorepo enterprise-grade"
```

---

## Padrões de Código

### Backend (Python)
- Seguir PEP 8
- Usar type hints
- Docstrings em funções complexas
- Imports organizados (padrão, terceiros, locais)

```python
# Bom ✅
from typing import Optional
from fastapi import HTTPException
from app.db.models import Cliente

def criar_cliente(cpf: str, nome: str) -> Cliente:
    """Cria um novo cliente no sistema."""
    ...

# Ruim ❌
def criar_cliente(cpf, nome):
    ...
```

### Frontend (JavaScript/React)
- Usar ES6+
- Componentes funcionais
- Props com PropTypes ou TypeScript
- CSS Modules ou Tailwind

---

## Testes (Futuro)

Quando implementarmos testes:
- Todos os PRs devem passar nos testes
- Cobertura mínima: 70%
- Testes unitários obrigatórios para lógica de negócio
- Testes de integração para endpoints críticos

---

## Estrutura de Pastas para Novos Arquivos

### Backend
```
services/backend/
├── app/
│   ├── routers/        # Novos endpoints aqui
│   │   ├── admin/      # Endpoints administrativos
│   │   │   ├── qrcodes.py
│   │   │   ├── relatorios.py
│   │   │   ├── usuarios.py
│   │   │   ├── entidades.py     
│   │   │   ├── unidades.py     
│   │   │   └── ...
│   │   ├── clientes.py
│   │   ├── sacolas.py
│   │   └── auth.py
│   ├── core/
│   │   ├── security.py
│   │   ├── audit.py
│   │   ├── helpers.py
│   │   └── qrcode_generator.py
│   ├── db/
│   │   ├── models.py            
│   │   ├── session.py
│   │   ├── migration_runner.py  
│   │   └── migrations/          
│   │       ├── 001_initial_schema.sql
│   │       ├── 002_add_features.sql
│   │       └── 003_add_multi_tenancy.sql
│   └── middleware/
│       └── auth.py              
```

### Frontend Caixa
```
apps/caixa/
├── src/
│   ├── components/     # Componentes React
│   ├── pages/          # Páginas
│   └── utils/          # Utilitários
```

---

## Review de Pull Request

### Checklist do Revisor

- [ ] Código segue convenções do projeto
- [ ] Commit messages seguem padrão Conventional Commits
- [ ] Código está documentado (quando necessário)
- [ ] Não quebra funcionalidades existentes
- [ ] Testes passam (quando aplicável)
- [ ] README/docs atualizados (se necessário)
- [ ] Branch está atualizada com base

### Checklist do Autor

- [ ] Testei localmente
- [ ] Código está formatado
- [ ] Removi console.logs/debugs
- [ ] Atualizei documentação relevante
- [ ] Branch está atualizada com `dev`
- [ ] Não commitei arquivos sensíveis (.env, *.pem)

---

## Comandos Úteis

### Git
```bash
# Atualizar sua branch com dev
git checkout dev
git pull origin dev
git checkout feature/MinhaFeature
git merge dev

# Ver histórico de commits
git log --oneline --graph --all

# Ver mudanças não commitadas
git status
git diff
```

### Backend Local
```bash
# Testar backend localmente (Python direto)
cd services/backend
python run.py

# Testar backend localmente (Docker)
docker-compose up backend

# Ver logs
docker-compose logs -f backend
```

### QR Codes
```bash
# Gerar via API (recomendado para produção)
# Usar Swagger: POST /api/admin/qrcodes/gerar
# Requer autenticação como admin

# Gerar via script CLI (desenvolvimento)
cd scripts/qrcodes
python gerar_qrcodes.py

# Limpar QR Codes antigos
python limpar_qrcodes.py

# Verificar último ID gerado
# Arquivo: storage/qrcodes/ultimo_id.txt
```

### Docker
```bash
# Ver containers rodando
docker-compose ps

# Ver logs
docker-compose logs backend-prod
docker-compose logs backend-staging

# Rebuild container específico
sudo docker-compose up -d --build backend-staging
sudo docker-compose up -d --build backend-prod

# Entrar no container
docker exec -it bagplus_backend_prod bash
docker exec -it bagplus_backend_staging bash

# Parar todos containers
docker-compose down

# Limpar containers e volumes
docker-compose down -v
docker system prune -a
```

### Utilitários
```bash
# Ver estrutura do projeto (Windows)
tree /A

# Ver estrutura do projeto (Linux/Mac)
tree

# Buscar texto em arquivos
grep -r "texto" services/backend/
```

---

## Regras de Pull Request

### Geral
1. **Base branch:** 
   - Features → `dev`
   - Releases → `main` (apenas de `dev`)
2. **Título:** Claro e descritivo
3. **Descrição:** Explicar O QUE e POR QUÊ
4. **Screenshots:** Se mudanças visuais (frontend)
5. **Issues:** Referenciar com `#numero` se aplicável
6. **Reviewers:** Marcar pelo menos 1 revisor
7. **Labels:** Usar labels apropriadas (bug, feature, docs, etc)

### Template de PR

```markdown
## Descrição
[Descreva o que foi feito]

## Motivação
[Por que essa mudança é necessária?]

## Tipo de Mudança
- [ ] Bug fix
- [ ] Nova feature
- [ ] Refatoração
- [ ] Documentação
- [ ] Deploy/Infraestrutura

## Como Testar
1. [Passo 1]
2. [Passo 2]
3. [Passo 3]

## Ambiente de Teste
- [ ] Local
- [ ] Staging
- [ ] Produção (após staging)

## Screenshots (se aplicável)
[Cole imagens aqui]

## Checklist
- [ ] Código segue convenções
- [ ] Testei localmente
- [ ] Testei em staging (se deploy)
- [ ] Documentação atualizada
- [ ] Não commitei arquivos sensíveis
```

---

### Verificar antes de Push:

```bash
# Ver o que será commitado
git status

# Ver conteúdo dos arquivos staged
git diff --cached

# Se commitou por engano
git reset HEAD <arquivo>
```

---

**Última atualização:** 29/04/2026  
**Versão:** 3.2 (Adicionada estrutura multi-tenancy)