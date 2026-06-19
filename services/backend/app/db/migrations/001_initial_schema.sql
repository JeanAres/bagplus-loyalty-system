-- ============================================
-- MIGRATION 001: SCHEMA INICIAL
-- Sprint 1-9 - Estrutura base do sistema
-- ============================================

-- TABELA CLIENTES
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cpf TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    telefone TEXT,
    ativo BOOLEAN DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABELA SACOLAS
CREATE TABLE IF NOT EXISTS sacolas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    qrcode TEXT UNIQUE NOT NULL,
    cliente_id INTEGER NOT NULL,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vida_util_dias INTEGER DEFAULT 365,
    ativo BOOLEAN DEFAULT 1,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
);

-- TABELA USUARIOS
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nome TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'gerente', 'caixa')),
    ativo BOOLEAN DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABELA TERMINAIS
CREATE TABLE IF NOT EXISTS terminais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL,
    descricao TEXT,
    ativo BOOLEAN DEFAULT 1,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TABELA USOS_SACOLA
CREATE TABLE IF NOT EXISTS usos_sacola (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sacola_id INTEGER NOT NULL,
    terminal_id INTEGER,
    usuario_id INTEGER,
    valor_compra REAL,
    desconto_aplicado REAL DEFAULT 0,
    tipo_desconto TEXT,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sacola_id) REFERENCES sacolas(id) ON DELETE CASCADE,
    FOREIGN KEY (terminal_id) REFERENCES terminais(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- TABELA LOGS_AUDITORIA
CREATE TABLE IF NOT EXISTS logs_auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    terminal_id INTEGER,
    acao TEXT NOT NULL,
    tabela TEXT,
    registro_id INTEGER,
    detalhes TEXT,
    ip TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (terminal_id) REFERENCES terminais(id)
);

-- ============================================
-- FIM MIGRATION 001
-- ============================================