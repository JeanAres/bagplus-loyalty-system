"""
Metadados e configuração da documentação da API
"""

TITLE = "Bag+ API"
VERSION = "0.94-beta"

DESCRIPTION = """
**Solução integrada para gestão de sacolas reutilizáveis e fidelização sustentável.**

A API Bag+ fornece um ecossistema completo para operações de balcão e gestão administrativa de alto nível, construída como plataforma **SaaS multi-tenant** — múltiplos estabelecimentos e filiais operando de forma independente na mesma infraestrutura.

**IMPORTANTE:** Todos os endpoints requerem autenticação JWT. Sistema protegido por roles: Admin, Gerente e Caixa.

### Pilares do Sistema
*   **Operacional:** Ciclo completo da sacola (Ativação via QR Code, Uso e Devolução) e gestão de clientes.
*   **Multi-Tenant:** Entidades, unidades, descontos por estabelecimento e isolamento de dados por unidade.
*   **Inteligência:** Dashboards analíticos, relatórios de crescimento, vendas por unidade/entidade e exportação de dados (CSV).
*   **Segurança:** Detecção automática de fraudes, logs de auditoria e autenticação JWT com contexto multi-tenant (Admin/Gerente/Caixa).
*   **Comunicação:** Sistema de notificações push e broadcast para engajamento.

---
**Suporte Técnico:** [jean06soares@gmail.com](mailto:jean06soares@gmail.com) | **Total:** 73 endpoints operacionais.
"""

CONTACT = {
    "name": "Bag+ Suporte",
    "email": "jean06soares@gmail.com",
}

LICENSE_INFO = {
    "name": "Proprietário",
    "url": "https://github.com/JeanAres/bagplus-loyalty-system",
}

TAGS_METADATA = [
    {
        "name": "Sistema",
        "description": "**Informações gerais da API** - Endpoint raiz com status do sistema"
    },
    {
        "name": "Clientes",
        "description": "**Gestão de Clientes** - Cadastro, edição, busca, validação de CPF, estatísticas e histórico completo"
    },
    {
        "name": "Sacolas",
        "description": "**Gestão de Sacolas** - Ativação via QR Code, registro de uso, devolução, consulta de status"
    },
    {
        "name": "Autenticação",
        "description": "**Autenticação JWT** - Login, informações do usuário, token de desenvolvimento"
    },
    {
        "name": "Notificações",
        "description": "**Notificações para Clientes** - Sistema de notificações push para app mobile (futuro)"
    },
    {
        "name": "Auditoria",
        "description": "**Auditoria do Caixa** - Resumo do turno e últimas ações do operador logado | *Requer: Caixa*"
    },
    {
        "name": "Admin - Lotes",
        "description": "**Gestão de Lotes** - Importação de lotes, listagem, estatísticas de distribuição | *Requer: Admin ou Gerente*"
    },
    {
        "name": "Admin - Suspensão",
        "description": "**Suspensão de Clientes** - Suspender, reativar, listar clientes suspensos | *Requer: Admin*"
    },
    {
        "name": "Admin - Alertas",
        "description": "**Sistema de Fraudes** - Detecção automática de padrões suspeitos, resolução de alertas | *Requer: Admin ou Gerente*"
    },
    {
        "name": "Admin - Relatórios",
        "description": "**Dashboard e Analytics** - Relatórios de vendas, estatísticas, crescimento MoM, vendas por unidade e por entidade | *Requer: Admin ou Gerente*"
    },
    {
        "name": "Admin - Sacolas",
        "description": "**Operações Avançadas** - Transferência, reset de contador, identificação de riscos | *Requer: Admin ou Gerente*"
    },
    {
        "name": "Admin - Exportação",
        "description": "**Exportar Dados** - Exportação de clientes, sacolas e usos para CSV (UTF-8 BOM) | *Requer: Admin ou Gerente*"
    },
    {
        "name": "Admin - Usuários",
        "description": "**Gestão de Usuários** - Criar, editar, desativar usuários, sistema de roles | *Requer: Admin*"
    },
    {
        "name": "Admin - Auditoria",
        "description": "**Logs de Auditoria** - Rastreamento completo de ações administrativas | *Requer: Admin ou Gerente*"
    },
    {
        "name": "Admin - Notificações",
        "description": "**Gestão de Notificações** - Broadcast, limpeza de antigas, estatísticas | *Requer: Admin ou Gerente*"
    },
    {
        "name": "Admin - QR Codes",
        "description": "**Geração de QR Codes** - Lotes sequenciais, download CSV/PDF, histórico de geração | *Requer: Admin*"
    },
    {
        "name": "Admin - Entidades",
        "description": "**Gestão de Entidades** - Cadastro de estabelecimentos, metas de desconto, listagem de unidades | *Requer: Admin*"
    },
    {
        "name": "Admin - Unidades",
        "description": "**Gestão de Unidades** - Filiais de cada entidade, endereços, ativação/desativação | *Requer: Admin*"
    }
]

SWAGGER_UI_PARAMETERS = {
    "defaultModelsExpandDepth": -1,
    "docExpansion": "none",
    "filter": True,
    "showRequestHeaders": True,
    "syntaxHighlight.theme": "monokai"
}