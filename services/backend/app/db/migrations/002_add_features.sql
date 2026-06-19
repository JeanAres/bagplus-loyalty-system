-- ============================================
-- MIGRATION 002: FEATURES COMPLETAS
-- Lotes, Alertas, Notificações e campos extras
-- ============================================

-- 1. CRIAR TABELA LOTES
CREATE TABLE IF NOT EXISTS lotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_fabricacao TEXT NOT NULL,
    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quantidade INTEGER NOT NULL,
    inicio INTEGER NOT NULL,
    fim INTEGER NOT NULL,
    arquivo_csv TEXT
);

-- 2. CRIAR TABELA ALERTAS
CREATE TABLE IF NOT EXISTS alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('valores_diferentes', 'abuso_valor_minimo', 'padrao_valores_repetidos')),
    gravidade TEXT NOT NULL CHECK(gravidade IN ('baixa', 'media', 'alta')),
    cliente_cpf TEXT NOT NULL,
    descricao TEXT NOT NULL,
    data_deteccao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolvido BOOLEAN DEFAULT 0,
    observacao TEXT,
    data_resolucao TIMESTAMP,
    FOREIGN KEY (cliente_cpf) REFERENCES clientes(cpf) ON DELETE CASCADE
);

-- 3. CRIAR TABELA NOTIFICACOES
CREATE TABLE IF NOT EXISTS notificacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_cpf TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('sacola_proximo_limite', 'sacola_expirada', 'desconto_disponivel', 'novo_lote', 'suspensao_conta')),
    titulo TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    lida BOOLEAN DEFAULT 0,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_leitura TIMESTAMP,
    FOREIGN KEY (cliente_cpf) REFERENCES clientes(cpf) ON DELETE CASCADE
);

-- 4. CRIAR TABELA REGISTROS_USO
CREATE TABLE IF NOT EXISTS registros_uso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sacola_id TEXT NOT NULL,
    data_uso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valor_compra REAL NOT NULL,
    FOREIGN KEY (sacola_id) REFERENCES sacolas(id) ON DELETE CASCADE
);

-- 5. ADICIONAR CAMPOS EXTRAS EM CLIENTES
ALTER TABLE clientes ADD COLUMN status_beneficios TEXT DEFAULT 'ativo' CHECK(status_beneficios IN ('ativo', 'suspenso', 'bloqueado'));
ALTER TABLE clientes ADD COLUMN motivo_suspensao TEXT;
ALTER TABLE clientes ADD COLUMN data_suspensao TIMESTAMP;

-- 6. ADICIONAR CAMPOS EXTRAS EM SACOLAS
ALTER TABLE sacolas ADD COLUMN checksum TEXT;
ALTER TABLE sacolas ADD COLUMN status TEXT DEFAULT 'estoque' CHECK(status IN ('estoque', 'ativo', 'devolvido'));
ALTER TABLE sacolas ADD COLUMN lote_id INTEGER REFERENCES lotes(id);
ALTER TABLE sacolas ADD COLUMN data_vinculacao TIMESTAMP;
ALTER TABLE sacolas ADD COLUMN utilizacoes INTEGER DEFAULT 0;
ALTER TABLE sacolas ADD COLUMN ultima_utilizacao TIMESTAMP;
ALTER TABLE sacolas ADD COLUMN data_devolucao TIMESTAMP;

-- 7. ADICIONAR CAMPOS EXTRAS EM USUARIOS
ALTER TABLE usuarios ADD COLUMN ultimo_login TIMESTAMP;

-- ============================================
-- FIM MIGRATION 002
-- ============================================