# Manual do Operador - Bag+ Caixa

Guia de uso do sistema de caixa para operadores do programa Bag+.

---

## Login

1. Acesse o sistema pelo navegador
2. Informe seu **usuário**, **senha** e **terminal** (ex: Caixa 1)
3. Clique em **Entrar**

> O sistema encerra a sessão automaticamente ao fechar ou recarregar a página (F5). Faça login novamente quando necessário.

---

## Home — Tela Inicial

A tela inicial tem dois blocos principais:

### Leitura Rápida

Escaneie ou digite o QR Code da sacola. O sistema identifica o status e redireciona automaticamente:


| Status da Sacola | O que acontece                                     |
| ---------------- | -------------------------------------------------- |
| Em estoque       | Vai para **Ativar Sacola**                         |
| Ativa            | Vai para **Registrar Uso** (com opção de devolver) |
| Devolvida        | Exibe mensagem informativa                         |


### Resumo do Turno

Exibe os contadores do dia atual (ativações, usos registrados e devoluções) e as últimas 5 operações realizadas por você.

---

## Clientes

### Cadastrar Cliente

1. Acesse **Clientes → Cadastrar**
2. Preencha CPF, nome completo e telefone (opcional)
3. Clique em **Cadastrar**

### Buscar Cliente

1. Acesse **Clientes → Buscar**
2. Escolha busca por **CPF** ou **Nome**
3. Selecione o cliente na lista

**Aba Dados:** exibe telefone, data de cadastro e sacolas ativas. Clique no lápis (✏️) para editar nome ou telefone.

**Aba Histórico:** exibe estatísticas do cliente (total gasto, valor médio, usos) e a linha do tempo completa de eventos.

---

## Sacolas

### Ativar Sacola

Vincula uma sacola nova a um cliente.

1. Acesse **Sacolas → Ativar** (ou use a Leitura Rápida na Home)
2. **Passo 1:** Escaneie ou digite o QR Code da sacola
3. **Passo 2:** Informe o CPF do cliente
4. Clique em **Ativar Sacola**

### Registrar Uso

Registra uma compra realizada com a sacola.

1. Acesse **Sacolas → Registrar Uso** (ou use a Leitura Rápida na Home)
2. **Passo 1:** Escaneie ou digite o QR Code da sacola
3. **Passo 2:** Verifique os dados exibidos (cliente, utilizações, estado) e informe o valor da compra
4. Digite o valor diretamente (ex: `2599` vira `25,99` automaticamente)
5. Clique em **Registrar Uso**

> Valor mínimo: **R$ 15,00**. Intervalo mínimo entre usos da mesma sacola: **4 horas**.

### Devolver Sacola

Processa a devolução da sacola ao programa.

1. Acesse **Sacolas → Devolução** (ou use a opção sugerida em Registrar Uso)
2. **Passo 1:** Escaneie ou digite o QR Code da sacola
3. **Passo 2:** Confira os dados e o desconto de devolução calculado
4. Clique em **Confirmar Devolução**

> O desconto de devolução deve ser aplicado no próximo cupom do cliente.

**Tabela de descontos por estado da sacola:**


| Estado      | Critério                  | Desconto |
| ----------- | ------------------------- | -------- |
| 🟢 Verde    | Até 15 usos / até 60 dias | R$ 40,00 |
| 🟡 Amarelo  | Até 25 usos / até 80 dias | R$ 20,00 |
| 🔴 Vermelho | Até 40 usos / até 90 dias | R$ 10,00 |
| ⚫ Expirado  | Acima dos limites         | R$ 0,00  |


### Verificar QR Code

Consulta o status de uma sacola **sem ativar nem registrar nada**.

1. Acesse **Sacolas → Verificar QR**
2. Escaneie ou digite o QR Code
3. O sistema exibe se é válido, o ID da sacola e o status atual

### Histórico de Usos

Consulta todos os usos registrados de uma sacola.

1. Acesse **Sacolas → Histórico**
2. Escaneie o QR Code ou digite o ID da sacola (ex: `BAG-00001`)
3. O sistema exibe total de usos, total gasto, valor médio e a lista cronológica

---

## Dúvidas Frequentes

**O cliente não está no sistema.**
Cadastre o cliente antes de ativar a sacola em **Clientes → Cadastrar**.

**A sacola está como "já vinculada".**
Ela já pertence a outro cliente. Consulte em **Sacolas → Verificar QR** para ver o status.

**Erro "Intervalo mínimo não atingido".**
A sacola já foi usada há menos de 4 horas. Aguarde o intervalo ou oriente o cliente.

**O valor mínimo não está sendo aceito.**
O sistema exige compras de no mínimo R$ 15,00.

**A sessão encerrou sozinha.**
O sistema usa sessão temporária por segurança. Faça login novamente.