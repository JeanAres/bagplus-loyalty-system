# Manual Técnico - Bag+ Caixa Frontend

Referência técnica para desenvolvedores e suporte do app de caixa.

---

## Visão Geral

App React/TypeScript para operadores de caixa do sistema Bag+. Consome a API REST do backend FastAPI via `@bagplus/shared/api`.

**URL Staging:** https://caixa-staging.bagplus.com.br  
**Backend Staging:** https://staging.bagplus.com.br  
**Repositório:** https://github.com/JeanAres/bagplus-loyalty-system

---

## Stack

| Tecnologia | Versão | Uso |
|---|---|---|
| React | 19 | UI |
| TypeScript | 6.0.3 | Tipagem |
| Vite | 8 | Build/Dev server |
| Tailwind CSS | v4 | Estilização |
| React Router DOM | 7 | Roteamento |
| lucide-react | 0.383 | Ícones |
| pnpm workspaces | — | Monorepo |

---

## Estrutura de Pastas

```
apps/caixa/
├── src/
│   ├── components/
│   │   ├── Layout.tsx          # Sidebar + header + breadcrumb
│   │   ├── HamburgerButton.tsx # Botão animado da sidebar
│   │   └── ProtectedRoute.tsx  # Guard de autenticação
│   ├── contexts/
│   │   ├── AuthContext.tsx     # JWT via sessionStorage
│   │   └── ThemeContext.tsx    # Dark/light com auto-detecção após 18h
│   ├── pages/
│   │   ├── Home.tsx            # Leitura rápida + resumo do turno
│   │   ├── Login.tsx
│   │   ├── CadastrarCliente.tsx
│   │   ├── BuscarCliente.tsx   # Abas Dados/Histórico + edição inline
│   │   ├── AtivarSacola.tsx
│   │   ├── RegistrarUso.tsx    # Máscara monetária automática
│   │   ├── Devolucao.tsx
│   │   ├── VerificarQr.tsx
│   │   └── Historico.tsx
│   ├── lib/
│   │   └── utils.ts            # cn() helper (clsx + tailwind-merge)
│   ├── App.tsx                 # Definição de rotas
│   ├── main.tsx
│   └── index.css               # Tokens Tailwind + animação hamburger
├── docs/
│   ├── MANUAL-OPERACIONAL.md
│   └── MANUAL-TECNICO.md
├── tsconfig.app.json
├── tsconfig.node.json
├── vite.config.ts
└── package.json
```

---

## Shared Workspace (`@bagplus/shared`)

```
apps/shared/
├── api/index.ts      # Todas as funções de chamada à API
├── types/index.ts    # Interfaces TypeScript (Sacola, Cliente, etc.)
├── utils/index.ts    # formatMoney, parseMoney, formatCPF, formatDate...
└── hooks/            # (reservado)
```

### Aliases configurados em `tsconfig.app.json`

```json
"@bagplus/shared"            → ../shared/index.ts
"@bagplus/shared/api"        → ../shared/api/index.ts
"@bagplus/shared/types"      → ../shared/types/index.ts
"@bagplus/shared/utils"      → ../shared/utils/index.ts
```

---

## Autenticação

- Login via `POST /api/auth/login?username=&password=&terminal=`
- Token JWT armazenado em `sessionStorage` (chave: `bagplus_token`)
- Usuário armazenado em `sessionStorage` (chave: `bagplus_user`)
- Roles aceitas: **apenas `caixa`** — admin e gerente são bloqueados no login
- Sessão encerra automaticamente ao fechar a aba ou hard reload (Shift+F5)

---

## Rotas

| Rota | Componente | Protegida |
|---|---|---|
| `/login` | Login.tsx | Não |
| `/` | Home.tsx | Sim |
| `/cadastrar-cliente` | CadastrarCliente.tsx | Sim |
| `/buscar-cliente` | BuscarCliente.tsx | Sim |
| `/ativar` | AtivarSacola.tsx | Sim |
| `/registrar-uso` | RegistrarUso.tsx | Sim |
| `/devolucao` | Devolucao.tsx | Sim |
| `/verificar-qr` | VerificarQr.tsx | Sim |
| `/historico` | Historico.tsx | Sim |

Rotas protegidas usam `<ProtectedRoute>` que verifica o token em `sessionStorage`.

---

## Navegação com State (Pré-preenchimento)

Telas de sacola aceitam `location.state` via React Router para pular o Step 1:

```typescript
// Home → AtivarSacola
navigate('/ativar', { state: { qrCode: 'BAG-00001:2026-05-13:abc123' } });

// Home → RegistrarUso (com sugestão de devolução)
navigate('/registrar-uso', { state: { qrCode: '...', sugerirDevolucao: true } });

// RegistrarUso → Devolucao
navigate('/devolucao', { state: { qrCode: '...' } });
```

---

## Tema

- Detecta automaticamente horário >= 18h para ativar dark mode
- Toggle manual persiste por 24h via `localStorage` (`bagplus_theme_manual`)
- Preferência de tema persiste via `localStorage` (`bagplus_caixa_theme`)
- Aplica/remove classe `dark` no `<html>` para Tailwind dark mode

---

## Endpoints Consumidos

| Método | Endpoint | Tela |
|---|---|---|
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | AuthContext |
| POST | `/api/clientes/` | CadastrarCliente |
| GET | `/api/clientes/buscar` | BuscarCliente |
| GET | `/api/clientes/{cpf}/validar` | BuscarCliente |
| PUT | `/api/clientes/{cpf}` | BuscarCliente |
| GET | `/api/clientes/{cpf}/estatisticas` | BuscarCliente (aba Histórico) |
| GET | `/api/clientes/{cpf}/historico-completo` | BuscarCliente (aba Histórico) |
| GET | `/api/sacolas/{sacola_id}` | AtivarSacola, RegistrarUso, Devolucao |
| POST | `/api/sacolas/ativar` | AtivarSacola |
| POST | `/api/sacolas/registrar-uso` | RegistrarUso |
| POST | `/api/sacolas/devolver` | Devolucao |
| POST | `/api/sacolas/verificar-qr` | VerificarQr, Home |
| GET | `/api/sacolas/{sacola_id}/historico` | Historico |
| GET | `/api/auditoria/meu-turno` | Home (resumo do turno) |

---

## Detecção de Ambiente (`getBaseUrl`)

```typescript
const hostname = window.location.hostname;

if (hostname === 'localhost' || hostname === '127.0.0.1') {
  return 'http://localhost:8000';
}
if (hostname.includes('staging')) {
  return 'https://staging.bagplus.com.br';
}
return 'https://api.bagplus.com.br';
```

---

## Rodar Localmente

```bash
# Backend (Terminal 1)
cd services/backend
venv\Scripts\Activate.ps1   # Windows
python run.py

# Frontend (Terminal 2)
cd apps/caixa
pnpm dev
```

---

## Build e Deploy Staging

```bash
# Build
cd apps/caixa
pnpm build

# Upload para servidor (rodar no PC)
scp -i ~/.ssh/bagplus.pem -r dist/* ubuntu@<servidor>:~/caixa-staging-temp/

# No servidor
sudo cp -r ~/caixa-staging-temp/* /var/www/caixa-staging/
sudo rm -rf ~/caixa-staging-temp
sudo chown -R www-data:www-data /var/www/caixa-staging
```

---

## Problemas Conhecidos e Soluções

**Erro `ignoreDeprecations` no build**  
TypeScript 6.x requer `"ignoreDeprecations": "6.0"` no `tsconfig.app.json` para silenciar o aviso de `baseUrl` deprecado.

**Erro de política de execução no Windows (PowerShell)**  
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Sessão encerra inesperadamente**  
Comportamento esperado — `sessionStorage` é limpo no hard reload (Shift+F5). O usuário deve fazer login novamente.

**CORS em desenvolvimento**  
Verifique se `http://localhost:5173` está na lista `origins` em `services/backend/app/main.py`.