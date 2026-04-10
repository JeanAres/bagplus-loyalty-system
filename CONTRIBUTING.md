# Como Contribuir

## Sobre o Projeto

Este é um **monorepo** que contém:
- **Backend** (FastAPI) em `services/backend/`
- **4 Frontends** em `apps/` (caixa, gestor, admin, cliente)
- **Scripts** auxiliares em `scripts/`
- **Infraestrutura** em `infra/`
- **Storage** de arquivos em `storage/`

---

## Estratégia de Branches

### Branches Principais

- **`main`**: Código em produção (releases estáveis)
- **`dev`**: Desenvolvimento ativo (branch padrão)

### Fluxo de Trabalho

1. Todo desenvolvimento acontece em `dev`
2. Features são desenvolvidas em branches `feature/*`
3. Merge para `dev` via Pull Request
4. Quando `dev` estiver estável → merge para `main` (release)

**IMPORTANTE:** Atualmente estamos trabalhando 100% em `dev`. A branch `main` só receberá merge quando o backend estiver 100% completo (v1.0-backend).

---

## Fluxo de Contribuição

1. **Clone o repositório**
   ```bash
   git clone https://github.com/JeanAres/bagplus-loyalty-system.git
   cd bagplus-loyalty-system
   ```

2. **Certifique-se de estar em `dev`**
   ```bash
   git checkout dev
   git pull origin dev
   ```

3. **Crie uma branch para sua feature**
   ```bash
   git checkout -b feature/MinhaFeature
   ```

4. **Faça suas alterações**
   - Siga os padrões de código
   - Teste suas mudanças
   - Documente quando necessário

5. **Commit seguindo convenções**
   ```bash
   git add .
   git commit -m "feat(backend): adiciona validação de CPF"
   ```

6. **Push para o repositório**
   ```bash
   git push origin feature/MinhaFeature
   ```

7. **Abra um Pull Request**
   - Base: `dev` (não `main`)
   - Descreva claramente as mudanças
   - Referencie issues relacionadas

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

---

## Exemplos de Commits Corretos

```bash
# Backend
git commit -m "feat(backend): implementa sistema de notificações"
git commit -m "fix(api): corrige endpoint de exportação CSV"
git commit -m "refactor(auth): simplifica middleware JWT"

# Frontend
git commit -m "feat(caixa): adiciona tela de cadastro de cliente"
git commit -m "fix(gestor): corrige gráfico de vendas MoM"
git commit -m "style(admin): aplica tema dark mode"

# Infraestrutura
git commit -m "chore(deps): atualiza dependencies do backend"
git commit -m "ci(github): configura deploy automático"
git commit -m "docs(contributing): atualiza guia de contribuição"

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
# Bom
from typing import Optional
from fastapi import HTTPException
from app.db.models import Cliente

def criar_cliente(cpf: str, nome: str) -> Cliente:
    """Cria um novo cliente no sistema."""
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
│   ├── core/           # Lógica de negócio
│   ├── db/             # Models e sessão
│   └── middleware/     # Middleware customizado
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

### Checklist do Autor

- [ ] Testei localmente
- [ ] Código está formatado
- [ ] Removi console.logs/debugs
- [ ] Atualizei documentação relevante
- [ ] Branch está atualizada com `dev`

---

## Comandos Úteis

```bash
# Atualizar sua branch com dev
git checkout dev
git pull origin dev
git checkout feature/MinhaFeature
git merge dev

# Testar backend localmente
cd services/backend
python run.py

# Gerar QR Codes
cd scripts/qrcodes
python gerar_qrcodes.py

# Ver estrutura do projeto
tree /A
```

---

## Regras de Pull Request

1. **Base branch:** Sempre `dev` (não `main`)
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

## Como Testar
1. [Passo 1]
2. [Passo 2]

## Screenshots (se aplicável)
[Cole imagens aqui]

## Checklist
- [ ] Código segue convenções
- [ ] Testei localmente
- [ ] Documentação atualizada
```

---

**Última atualização:** 08/04/2026  
**Versão:** 2.0 (Atualizado para Monorepo)