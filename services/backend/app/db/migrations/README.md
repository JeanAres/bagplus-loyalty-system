---

## 📜 Regras de Migrations:

### FAZER:
1. Sempre criar nova migration para mudanças
2. Nomear: `XXX_descricao.sql` (ordem numérica crescente)
3. Testar localmente ANTES de staging/prod
4. Commitar migrations junto com código que as usa
5. Usar `IF NOT EXISTS` para segurança
6. Documentar o que cada migration faz (comentários SQL)

### NUNCA:
1. Editar migrations já aplicadas em produção
2. Deletar migrations antigas
3. Mudar ordem das migrations
4. Fazer ALTER TABLE sem considerar dados existentes
5. Esquecer de rodar em staging antes de produção

---

## 🔄 Workflow de Deploy:

### Desenvolvimento (Local):
```bash
1. Criar nova migration: XXX_descricao.sql
2. Apagar banco local: rm data/bagplus.db
3. Rodar migrations: python app/db/migration_runner.py
4. Testar código com novo schema
5. Commitar: git add + git commit
```

### Deploy Staging:
```bash
1. SSH no servidor
2. cd bagplus-loyalty-system
3. git pull origin dev
4. Rodar migrations no servidor (dentro do container ou antes do build)
5. sudo docker-compose build backend-staging
6. sudo docker-compose up -d backend-staging
7. Testar endpoints
```

### Deploy Produção:
```bash
1. Merge dev → main
2. SSH no servidor
3. git checkout main && git pull
4. BACKUP do banco de produção primeiro!
5. Rodar migrations
6. Build e deploy
7. Monitorar logs
```

---

## 🚨 Rollback (Emergência):

Se migration quebrar produção:

```bash
1. Restaurar backup do banco
2. Reverter código (git revert)
3. Rebuild container
4. Investigar problema
5. Criar migration de correção
```

---

**Última atualização:** - Multi-Tenancy (Abril 2026)