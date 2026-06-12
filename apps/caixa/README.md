# Frontend Caixa - Bag+

Interface operacional para caixas do sistema Bag+.

## Stack
- React 19 + TypeScript + Vite
- Tailwind CSS v4
- React Router DOM
- @bagplus/shared (workspace)

## Rotas
- `/login` — Autenticação (exclusivo role caixa)
- `/` — Home com leitura rápida e resumo do turno
- `/cadastrar-cliente` — Cadastro de novo cliente
- `/buscar-cliente` — Busca por CPF ou nome (com edição inline e histórico)
- `/ativar` — Ativar sacola via QR Code
- `/registrar-uso` — Registrar uso via QR Code
- `/devolucao` — Processar devolução
- `/verificar-qr` — Verificar QR Code sem ativar
- `/historico` — Histórico de usos da sacola

## Funcionalidades
- Login com validação de role (apenas caixa)
- Tema dark automático após 18h com toggle manual
- Preferência de tema persiste via localStorage
- Sessão via sessionStorage (logout automático no hard reload)
- Sidebar recolhível com navegação por seções
- Breadcrumb no header
- Home: leitura rápida de QR Code com redirecionamento automático conforme status da sacola (estoque → ativar, ativo → registrar uso/devolver)
- Home: resumo do turno com contadores de ativações, usos e devoluções + últimas ações
- Busca de cliente: abas Dados e Histórico (timeline completa de eventos)

## Rodar localmente
```bash
pnpm dev
```

## Build
```bash
pnpm build
```