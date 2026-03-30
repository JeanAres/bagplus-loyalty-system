# Como Contribuir

## Fluxo de Trabalho

1. Faça um fork do projeto ou clone o repositório
2. Crie uma branch para sua feature: `git checkout -b feature/MinhaFeature`
3. Faça commit das suas alterações seguindo as convenções abaixo
4. Faça push para a branch: `git push origin feature/MinhaFeature`
5. Abra um Pull Request descrevendo claramente as mudanças

## Convenção de Commits

Este projeto segue o padrão **Conventional Commits**. Todos os commits devem seguir o formato:

```
<tipo>(<escopo>): <descrição>

[corpo opcional]

[rodapé opcional]
```

### Tipos de Commit

- **feat**: Nova funcionalidade
  - Exemplo: `feat(auth): adiciona autenticação JWT`
  
- **fix**: Correção de bug
  - Exemplo: `fix(bag): corrige cálculo de utilizações`
  
- **refactor**: Refatoração de código (sem alterar funcionalidade)
  - Exemplo: `refactor(database): reorganiza queries do banco`
  
- **docs**: Alterações na documentação
  - Exemplo: `docs(readme): atualiza instruções de instalação`
  
- **style**: Alterações de formatação (espaços, ponto e vírgula, etc)
  - Exemplo: `style(api): formata código com prettier`
  
- **test**: Adição ou modificação de testes
  - Exemplo: `test(bag): adiciona testes unitários para ciclo de vida`
  
- **chore**: Tarefas de manutenção, configuração, dependências
  - Exemplo: `chore(deps): atualiza dependências do projeto`
  
- **perf**: Melhorias de performance
  - Exemplo: `perf(query): otimiza consulta de histórico de utilizações`
  
- **ci**: Alterações em CI/CD
  - Exemplo: `ci(github): adiciona workflow de testes automáticos`
  
- **build**: Alterações no sistema de build
  - Exemplo: `build(webpack): configura bundle de produção`

### Escopo (opcional)

O escopo especifica qual parte do código foi afetada:
- `auth` - autenticação
- `bag` - lógica das sacolas
- `rewards` - sistema de recompensas
- `api` - endpoints da API
- `database` - banco de dados
- `ui` - interface do usuário

### Exemplos de Commits

```bash
# Boa prática
git commit -m "feat(rewards): adiciona cálculo de descontos progressivos"
git commit -m "fix(bag): corrige validação de prazo de 90 dias"
git commit -m "refactor(api): simplifica endpoint de devolução"
git commit -m "docs(contributing): adiciona guia de convenção de commits"

# Evite
git commit -m "alterações"
git commit -m "fix bug"
git commit -m "update"
```

## Regras de Pull Request

- Todas as alterações devem passar por Pull Request
- PRs precisam de aprovação antes de merge
- Descreva claramente as mudanças no PR
- Referencie issues relacionadas (se houver)
- Mantenha o código limpo e bem documentado
- Certifique-se de que os testes passam (quando aplicável)

## Padrões de Branch

- `feature/nome-da-feature` - Novas funcionalidades
- `fix/nome-do-bug` - Correções de bugs
- `refactor/nome-da-refatoracao` - Refatorações
- `docs/nome-da-doc` - Documentação
