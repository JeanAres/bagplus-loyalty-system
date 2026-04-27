-- ============================================
-- MIGRATION 003: MULTI-TENANCY
-- Sprint 10 - Reestruturação para SaaS
-- ============================================

-- 1. CRIAR TABELA ENTIDADES
CREATE TABLE IF NOT EXISTS entidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_comercial TEXT NOT NULL,
    cnpj TEXT UNIQUE NOT NULL,
    meta_desconto_percentual REAL NOT NULL,
    meta_desconto_quantidade_usos INTEGER NOT NULL,
    ativo BOOLEAN DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. CRIAR TABELA UNIDADES
CREATE TABLE IF NOT EXISTS unidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entidade_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    endereco TEXT,
    cidade TEXT,
    estado TEXT,
    ativo BOOLEAN DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entidade_id) REFERENCES entidades(id) ON DELETE CASCADE,
    UNIQUE(entidade_id, nome)
);

-- 3. CRIAR TABELA DESCONTOS_CLIENTE_ENTIDADE
CREATE TABLE IF NOT EXISTS descontos_cliente_entidade (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    entidade_id INTEGER NOT NULL,
    usos_count INTEGER DEFAULT 0,
    proximo_desconto_percentual REAL DEFAULT 0,
    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
    FOREIGN KEY (entidade_id) REFERENCES entidades(id) ON DELETE CASCADE,
    UNIQUE(cliente_id, entidade_id)
);

-- 4. ADICIONAR COLUNAS EM USUARIOS
ALTER TABLE usuarios ADD COLUMN entidade_id INTEGER REFERENCES entidades(id);
ALTER TABLE usuarios ADD COLUMN unidade_id INTEGER REFERENCES unidades(id);

-- 5. ADICIONAR COLUNAS EM TERMINAIS
ALTER TABLE terminais ADD COLUMN entidade_id INTEGER REFERENCES entidades(id);
ALTER TABLE terminais ADD COLUMN unidade_id INTEGER REFERENCES unidades(id);

-- 6. ADICIONAR COLUNAS EM USOS_SACOLA
ALTER TABLE usos_sacola ADD COLUMN entidade_id INTEGER REFERENCES entidades(id);
ALTER TABLE usos_sacola ADD COLUMN unidade_id INTEGER REFERENCES unidades(id);

-- 7. ADICIONAR COLUNAS EM LOGS_AUDITORIA  
ALTER TABLE logs_auditoria ADD COLUMN entidade_id INTEGER REFERENCES entidades(id);
ALTER TABLE logs_auditoria ADD COLUMN unidade_id INTEGER REFERENCES unidades(id);

-- ============================================
-- FIM MIGRATION 003
-- ============================================