# Bag+

> *Sua sacola vale mais.*

Sistema de fidelização sustentável com EcoBags de juta rastreáveis, incentivando a redução de sacolas plásticas através de recompensas por uso recorrente.

---

## Status do Projeto

**Backend:** 90% completo (52 endpoints operacionais)  
**Arquitetura:** Enterprise Monorepo  
**Versão:** v0.91-beta  
**Última atualização:** Abril 2026  

 **Pronto para demonstração comercial**  

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

## Como Funciona

### 1. Primeira Utilização
- Cliente adquire a **Bag+** no caixa
- Sacola é vinculada ao CPF do cliente
- QR Code único gerado com checksum SHA256
- Contador de utilizações iniciado (máximo de 40 usos)
- Prazo de 90 dias começa a contar

### 2. Uso Recorrente
- Cliente apresenta o QR Code da sacola no caixa
- Sistema valida autenticidade e vinculação ao CPF
- Cada sacola utilizada recebe +1 registro de uso
- Sistema valida compra real (valor obrigatório)
- Intervalo mínimo de 4h entre usos da mesma sacola

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
-  Intervalo mínimo de 4 horas entre utilizações da mesma sacola
-  Validação obrigatória de compra real no sistema
-  Detecção automática de 3 tipos de fraude:
  - **Tipo 1:** Múltiplas sacolas usadas simultaneamente
  - **Tipo 2:** Uso excessivo em curto período
  - **Tipo 3:** Padrão de uso suspeito
-  Alertas automáticos para comportamentos anormais
-  Sistema de auditoria completo (logs de todas ações)

### Integridade
- Uso pessoal e intransferível (vinculado ao CPF)
- Transferência entre clientes apenas via sistema admin
- Compartilhamento ou manipulação resulta em suspensão temporária
- Ultrapassar limites = perda do direito à devolução com desconto
- Sistema de gestão de usuários com 3 níveis (Admin/Gerente/Caixa)

### Responsabilidade Ambiental
- Descarte incorreto comprovado pode resultar em suspensão de benefícios
- Mercado responsável pela destinação adequada das sacolas devolvidas
- Compostagem industrial ou destinação a resíduos orgânicos
- **Relatórios de impacto ambiental:** CO₂ economizado, sacolas evitadas

## Funcionalidades Implementadas

### Para Operadores de Caixa
-  Cadastro rápido de clientes
-  Ativação de sacolas via QR Code
-  Registro de uso com validação automática
-  Processamento de devoluções
-  Busca por CPF ou código de sacola

### Para Gestores
-  Dashboard administrativo completo
-  Relatórios de vendas por período
-  Análise Month-over-Month (MoM)
-  Estatísticas gerais do sistema
-  Exportação de dados (CSV UTF-8)
-  Gestão de lotes de QR Codes
-  Sistema de alertas e notificações
-  Identificação de sacolas em risco

### Para Administradores
-  Gestão completa de usuários (criar, editar, desativar)
-  Sistema de roles (Admin/Gerente/Caixa)
-  Logs de auditoria completos
-  Transferência de sacolas entre clientes
-  Reset de contador de utilizações
-  Suspensão/reativação de clientes
-  Broadcast de notificações
-  Relatórios de impacto ambiental

### Segurança
-  Autenticação JWT (24h de validade)
-  31 endpoints protegidos por role
-  Middleware de autenticação
-  Auditoria de todas ações sensíveis
-  Validação de CPF com dígito verificador (planejado)
-  Rate limiting (planejado)

## Arquitetura Técnica

### Stack
- **Backend:** FastAPI (Python 3.11+)
- **Banco de Dados:** SQLite (migração para PostgreSQL planejada)
- **Autenticação:** JWT + bcrypt
- **API Docs:** Swagger UI com tema dark customizado
- **Estrutura:** Monorepo enterprise-grade

### Estrutura do Projeto
```
bagplus-loyalty-system/
├── apps/                    # 4 Frontends (planejados)
│   ├── caixa/              # Interface operador
│   ├── gestor/             # Dashboard gerencial
│   ├── admin/              # Painel administrativo
│   └── cliente/            # App cliente (mobile + web)
├── services/backend/       # API FastAPI (90% completo)
├── storage/                # QR Codes e arquivos
├── scripts/                # Geração de QR Codes
└── infra/                  # Infraestrutura e docs
```

### Endpoints Disponíveis
**Total:** 52 endpoints operacionais

**Públicos (15):**
- 4 endpoints de clientes
- 4 endpoints de sacolas
- 4 endpoints de notificações
- 3 endpoints de autenticação

**Admin (37):**
- 6 endpoints de relatórios
- 5 endpoints de gestão de usuários
- 6 endpoints de alertas
- 5 endpoints de lotes
- 15+ endpoints administrativos diversos

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

## Estratégia de Implementação

### 1. Fase Piloto (3-6 meses)
- Backend completo (90% pronto)
- Interface de caixa
- Dashboard administrativo
- App do cliente

### 2. Fase de Transição
- Sacolas plásticas ainda disponíveis
- Incentivos para adoção da Bag+
- Treinamento de operadores
- Campanhas de conscientização

### 3. Fase de Consolidação
- Bag+ como opção principal
- Redução gradual de plástico
- Análise de resultados
- Ajustes baseados em feedback

### 4. Fase Final
- Bag+ como única opção
- Sistema 100% sustentável
- Expansão para outros estabelecimentos
- Modelo replicável

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

### Para o Meio Ambiente
- Redução quantificada de plástico
- Material 100% biodegradável
- Descarte responsável garantido
- Economia circular implementada
- Métricas de impacto rastreáveis

## Licenciamento Comercial

Este software está disponível para licenciamento comercial.

### O que está incluído:
- Backend completo (52 endpoints)
- Sistema de autenticação e segurança
- Dashboard administrativo
- Relatórios gerenciais
- Sistema de detecção de fraudes
- Notificações automáticas
- Exportação de dados
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

### Contato para Licenciamento:

📧 **Email:** jean06soares@gmail.com  
🐙 **GitHub:** https://github.com/JeanAres/bagplus-loyalty-system

---

## Demonstração

**Acesso ao Sistema:**
- Swagger UI com tema dark profissional
- 52 endpoints documentados
- Exemplos de requisições
- Teste de autenticação e permissões

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