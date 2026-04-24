# Bag+

> *Sua sacola vale mais.*

Sistema de fidelização sustentável com EcoBags de juta rastreáveis, incentivando a redução de sacolas plásticas através de recompensas por uso recorrente.

---

## Status do Projeto

**Backend:** 95% completo (58 endpoints operacionais)  
**Arquitetura:** Enterprise Monorepo  
**Versão:** v0.92-beta  
**Última atualização:** Abril 2026  

---

## Sobre o Projeto

O **Bag+** é um programa que visa substituir gradualmente as sacolas plásticas convencionais por EcoBags sustentáveis produzidas em juta - um material de origem vegetal, resistente e biodegradável.

O sistema incorpora um programa de fidelização que recompensa clientes pelo uso recorrente das sacolas, criando incentivos financeiros para práticas sustentáveis.

## Características Principais

- **Material Sustentável**: EcoBags produzidas em juta biodegradável
- **Sistema de Rastreamento**: Cada sacola vinculada ao CPF do cliente via QR Code SHA256
- **Programa de Recompensas**: Descontos progressivos baseados no número de utilizações
- **Ciclo de Vida Controlado**: 40 utilizações ou 90 dias de prazo máximo
- **Descarte Responsável**: Compostagem industrial das sacolas devolvidas
- **Detecção de Fraudes**: Sistema inteligente identifica 3 tipos de fraudes automaticamente
- **Notificações Automáticas**: 5 tipos de alertas integrados ao sistema
- **Sistema de Terminais**: Rastreamento completo por caixa com logs detalhados
- **Geração de QR Codes**: API REST + Script CLI com sincronização automática

## Como Funciona

### 1. Primeira Utilização
- Cliente adquire a **Bag+** no caixa
- Sacola é vinculada ao CPF do cliente
- QR Code único gerado com checksum SHA256
- Contador de utilizações iniciado (máximo de 40 usos)
- Prazo de 90 dias começa a contar

### 2. Uso Recorrente
- Cliente apresenta o QR Code da sacola no caixa
- Operador autenticado registra a venda (terminal identificado)
- Sistema valida autenticidade e vinculação ao CPF
- Cada sacola utilizada recebe +1 registro de uso
- Sistema valida compra real (valor obrigatório)
- Intervalo mínimo de 4h entre usos da mesma sacola
- Log completo: quem, quando, onde (terminal), de onde (IP)

### 3. Acúmulo de Benefícios
- Ao atingir número "X" de utilizações (definido pelo estabelecimento)
- Descontos liberados automaticamente
- Notificações enviadas ao cliente sobre marcos alcançados
- Devolução antecipada = descontos maiores

### 4. Devolução
- Cliente devolve a sacola ao final do ciclo
- Recebe desconto proporcional ao momento da devolução
- Sistema registra devolução e atualiza estoque
- Mercado realiza descarte adequado via compostagem

## Ciclo de Vida da Bag+

| Utilizações | Status | Notificação |
|-------------|--------|-------------|
| 0 - 15 | Estado novo | - |
| 16 - 25 | Período recomendado para troca | - |
| 26 - 35 | Estágio final para substituição | ⚠️ Alerta aos 35 usos |
| 36 - 40 | Uso crítico | 🔴 Notificação de proximidade do limite |
| 90 dias | Expiração por prazo | 📅 Alerta de expiração |

**Limites:**
- Prazo máximo: **90 dias**
- Utilizações máximas: **40 usos**

## Regras e Controle

### Segurança do Sistema
- ✅ Intervalo mínimo de 4 horas entre utilizações da mesma sacola
- ✅ Validação obrigatória de compra real no sistema
- ✅ Autenticação obrigatória para registrar vendas
- ✅ Detecção automática de 3 tipos de fraude:
  - **Tipo 1:** Múltiplas sacolas usadas simultaneamente
  - **Tipo 2:** Uso excessivo em curto período
  - **Tipo 3:** Padrão de uso suspeito
- ✅ Alertas automáticos para comportamentos anormais
- ✅ Sistema de auditoria completo (logs de todas ações)
- ✅ Rastreamento por terminal (qual caixa registrou)

### Integridade
- Uso pessoal e intransferível (vinculado ao CPF)
- Transferência entre clientes apenas via sistema admin
- Compartilhamento ou manipulação resulta em suspensão temporária
- Ultrapassar limites = perda do direito à devolução com desconto
- Sistema de gestão de usuários com 3 níveis (Admin/Gerente/Caixa)
- Tokens JWT com expiração diferenciada (12h caixa, 24h admin/gerente)

### Responsabilidade Ambiental
- Descarte incorreto comprovado pode resultar em suspensão de benefícios
- Mercado responsável pela destinação adequada das sacolas devolvidas
- Compostagem industrial ou destinação a resíduos orgânicos
- **Relatórios de impacto ambiental:** CO₂ economizado, sacolas evitadas

## Funcionalidades Implementadas

### Para Operadores de Caixa
- ✅ Cadastro rápido de clientes
- ✅ Ativação de sacolas via QR Code
- ✅ Registro de uso com validação automática
- ✅ Processamento de devoluções
- ✅ Busca por CPF ou código de sacola
- ✅ Login com identificação de terminal
- ✅ Autenticação obrigatória para vendas

### Para Gestores
- ✅ Dashboard administrativo completo
- ✅ Relatórios de vendas por período
- ✅ Relatório de vendas por terminal
- ✅ Análise Month-over-Month (MoM)
- ✅ Estatísticas gerais do sistema
- ✅ Exportação de dados (CSV UTF-8)
- ✅ Gestão de lotes de QR Codes
- ✅ Sistema de alertas e notificações
- ✅ Identificação de sacolas em risco
- ✅ Download de QR Codes gerados
- ✅ Histórico de geração de lotes

### Para Administradores
- ✅ Gestão completa de usuários (criar, editar, desativar)
- ✅ Sistema de roles (Admin/Gerente/Caixa)
- ✅ Logs de auditoria completos com terminal e IP
- ✅ Transferência de sacolas entre clientes
- ✅ Reset de contador de utilizações
- ✅ Suspensão/reativação de clientes
- ✅ Broadcast de notificações
- ✅ Relatórios de impacto ambiental
- ✅ Geração de QR Codes via API
- ✅ Controle de sequência automático

### Segurança
- ✅ Autenticação JWT (12h caixa, 24h admin/gerente)
- ✅ 35 endpoints protegidos por role
- ✅ Middleware de autenticação
- ✅ Auditoria de todas ações sensíveis
- ✅ Sistema de terminais para rastreabilidade
- ✅ Validação de CPF com dígito verificador
- ⏳ Rate limiting (planejado)

### Geração de QR Codes
- ✅ API REST completa (4 endpoints)
- ✅ Script CLI interativo
- ✅ Sincronização automática de sequência
- ✅ Geração em lote (até 10.000 por vez)
- ✅ Formatos: CSV (importação) + PDF (gráfica)
- ✅ Download direto via API
- ✅ Histórico de lotes gerados
- ✅ Auditoria completa (quem, quando, quantos)
- ✅ Controle de acesso (apenas admins)

## Arquitetura Técnica

### Stack
- **Backend:** FastAPI (Python 3.11+)
- **Banco de Dados:** SQLite (migração para PostgreSQL planejada)
- **Autenticação:** JWT + bcrypt
- **API Docs:** Swagger UI com tema dark customizado
- **Estrutura:** Monorepo enterprise-grade
- **QR Codes:** qrcode + ReportLab + SHA256

### Estrutura do Projeto
```
bagplus-loyalty-system/
├── apps/                    # 4 Frontends (planejados)
│   ├── caixa/              # Interface operador
│   ├── gestor/             # Dashboard gerencial
│   ├── admin/              # Painel administrativo
│   └── cliente/            # App cliente (mobile + web)
├── services/backend/       # API FastAPI (95% completo)
│   ├── app/
│   │   ├── routers/       # 14 módulos de endpoints
│   │   ├── core/          # Lógica central + QR Code generator
│   │   ├── middleware/    # Autenticação + terminais
│   │   └── db/            # SQLAlchemy models
├── storage/                # QR Codes e arquivos
│   └── qrcodes/
│       ├── csv/           # Lotes para importação
│       ├── pdf/           # PDFs para gráfica
│       └── ultimo_id.txt  # Controle de sequência
├── scripts/                # Geração de QR Codes (CLI)
└── infra/                  # Infraestrutura e docs
```

### Endpoints Disponíveis
**Total:** 58 endpoints de API operacionais (`/api`) + 3 rotas auxiliares (`/`, `/docs`, `/redoc`) = **61 rotas HTTP**

**Públicos (24):**
- 9 endpoints de clientes
- 8 endpoints de sacolas
- 4 endpoints de notificações
- 3 endpoints de autenticação

**Admin (34):**
- 5 endpoints de relatórios
- 5 endpoints de gestão de usuários
- 2 endpoints de alertas
- 3 endpoints de lotes
- 3 endpoints de suspensão
- 4 endpoints de QR Codes
- 5 endpoints de gestão de sacolas
- 3 endpoints de exportação
- 3 endpoints de notificações
- 1 endpoint de auditoria

## Público-Alvo

### Fase 1 (Atual)
- **Supermercados e Hipermercados**
  - Redes como Zaffari, Carrefour, SuperMix
  - Mercados regionais e locais

### Fase 2 (Expansão)
- **Farmácias:** Droga Raia, São João, Panvel
- **Lojas de Varejo:** C&A, Renner, Magazine Luiza
- **Fast Food:** McDonald's, Burger King, Subway

### Fase 3 (Longo Prazo)
- Shopping centers
- Feiras e eventos
- E-commerce (embalagens reutilizáveis)

## Impacto Ambiental

### Métricas Calculadas pelo Sistema
- **Sacolas plásticas evitadas:** 1 sacola por uso registrado
- **CO₂ economizado:** 33g por sacola evitada
- **Petróleo economizado:** 11ml por sacola evitada
- **Equivalente em árvores:** Absorção de CO₂ calculada

### Relatórios Disponíveis
- Dashboard de impacto em tempo real
- Relatórios mensais para marketing
- Comparativo MoM de crescimento
- Exportação de dados para campanhas
- Análise por terminal (qual caixa vende mais)

## Estratégia de Implementação

### 1. Fase Piloto (3-6 meses)
- Backend completo (95% pronto)
- Interface de caixa
- Dashboard administrativo
- App do cliente
- Sistema de terminais configurado
- Geração de QR Codes via API

### 2. Fase de Transição
- Sacolas plásticas ainda disponíveis
- Incentivos para adoção da Bag+
- Treinamento de operadores
- Campanhas de conscientização
- Monitoramento por terminal

### 3. Fase de Consolidação
- Bag+ como opção principal
- Redução gradual de plástico
- Análise de resultados por caixa
- Ajustes baseados em feedback
- Otimização de processos

### 4. Fase Final
- Bag+ como única opção
- Sistema 100% sustentável
- Expansão para outros estabelecimentos
- Modelo replicável
- Franquia do sistema

## Benefícios

### Para o Cliente
- Descontos progressivos em compras
- Contribuição mensurável para sustentabilidade
- Sacolas resistentes (40 usos garantidos)
- Notificações sobre benefícios
- App para acompanhamento (futuro)
- Visualização de impacto ambiental pessoal

### Para o Estabelecimento
- Imagem sustentável fortalecida
- Redução de custos com sacolas plásticas
- Fidelização comprovada por dados
- Diferencial competitivo real
- Relatórios gerenciais completos
- Dashboard administrativo profissional
- Sistema de detecção de fraudes
- ROI mensurável
- Rastreamento por terminal
- Controle total sobre geração de QR Codes

### Para o Meio Ambiente
- Redução quantificada de plástico
- Material 100% biodegradável
- Descarte responsável garantido
- Economia circular implementada
- Métricas de impacto rastreáveis

## Licenciamento Comercial

Este software está disponível para licenciamento comercial.

### O que está incluído:
- Backend completo (58 endpoints de API)
- Sistema de autenticação e segurança
- Sistema de terminais
- Dashboard administrativo
- Relatórios gerenciais
- API de geração de QR Codes
- Script CLI para QR Codes
- Sistema de detecção de fraudes
- Notificações automáticas
- Exportação de dados
- Logs de auditoria completos
- Documentação técnica completa
- Suporte técnico
- Atualizações de segurança
- Treinamento de operadores

### Opcionais:
- Customização de interface
- App mobile personalizado
- Integração com ERPs existentes
- Relatórios customizados
- Hospedagem em nuvem
- Impressão de QR Codes personalizada

### Contato para Licenciamento:

**Email:** jean06soares@gmail.com  
**GitHub:** https://github.com/JeanAres/bagplus-loyalty-system

---

## Demonstração

**Acesso ao Sistema:**
- Swagger UI com tema dark profissional
- 58 endpoints documentados
- Exemplos de requisições
- Teste de autenticação e permissões
- Geração de QR Codes via interface
- Simulação de vendas por terminal

**Instruções:**
Consulte o [README.md](./README.md) para instruções de instalação e teste local.

---

## Documentação

- **README.md** - Guia de instalação e uso
- **CONTRIBUTING.md** - Guia para desenvolvedores
- **LICENSE.txt** - Termos de licenciamento
- **Swagger UI** - Documentação interativa da API

---

**Bag+ - Sistema de Fidelização Sustentável**  
*Sua sacola vale mais.*

Copyright © 2026 Jean Soares. Todos os direitos reservados.