"""
Models do Bag+ Sistema de Fidelização
Multi-Tenancy SaaS
"""
from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, Enum, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# ============================================
# ENUMS
# ============================================

class StatusSacola(str, enum.Enum):
    """Status da sacola no sistema"""
    estoque = "estoque"  
    ativo = "ativo"      
    devolvido = "devolvido"

class StatusBeneficios(str, enum.Enum):
    """Status dos benefícios do cliente"""
    ativo = "ativo"
    suspenso = "suspenso"
    bloqueado = "bloqueado"

class TipoAlerta(str, enum.Enum):
    """Tipos de alertas de fraude"""
    valores_diferentes = "valores_diferentes"
    abuso_valor_minimo = "abuso_valor_minimo"
    padrao_valores_repetidos = "padrao_valores_repetidos"

class GravidadeAlerta(str, enum.Enum):
    """Gravidade do alerta"""
    baixa = "baixa"
    media = "media"
    alta = "alta"

class UserRole(str, enum.Enum):
    """Roles de usuários do sistema"""
    admin = "admin"      # Admin global (vê tudo, entidade_id=NULL)
    gerente = "gerente"  # Gerente de unidade específica
    caixa = "caixa"      # Operador de caixa/terminal

class TipoNotificacao(str, enum.Enum):
    """Tipos de notificações para clientes"""
    sacola_proximo_limite = "sacola_proximo_limite"
    sacola_expirada = "sacola_expirada"
    desconto_disponivel = "desconto_disponivel"
    novo_lote = "novo_lote"
    suspensao_conta = "suspensao_conta"


# ============================================
# MODELS MULTI-TENANCY (Sprint 10)
# ============================================

class Entidade(Base):
    """
    Entidade = Estabelecimento (Zaffari, Mercadinho João, etc)
    Cada entidade pode ter múltiplas unidades (filiais)
    """
    __tablename__ = "entidades"
    
    id = Column(Integer, primary_key=True, index=True)
    nome_comercial = Column(String, nullable=False)
    cnpj = Column(String, unique=True, nullable=False)
    meta_desconto_percentual = Column(Float, nullable=False)
    meta_desconto_quantidade_usos = Column(Integer, nullable=False)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    
    # Relationships
    unidades = relationship("Unidade", back_populates="entidade")
    usuarios = relationship("Usuario", back_populates="entidade")
    terminais = relationship("Terminal", back_populates="entidade")
    usos = relationship("UsoSacola", back_populates="entidade")
    descontos = relationship("DescontoClienteEntidade", back_populates="entidade")
    logs = relationship("LogAuditoria", back_populates="entidade")


class Unidade(Base):
    """
    Unidade = Filial/Loja física de uma entidade
    Ex: Zaffari Iguatemi, Zaffari Cavalhada, etc
    """
    __tablename__ = "unidades"
    
    id = Column(Integer, primary_key=True, index=True)
    entidade_id = Column(Integer, ForeignKey("entidades.id"), nullable=False)
    nome = Column(String, nullable=False)  # "Iguatemi", "Cavalhada"
    endereco = Column(String, nullable=True)
    cidade = Column(String, nullable=True)
    estado = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    
    # Relationships
    entidade = relationship("Entidade", back_populates="unidades")
    usuarios = relationship("Usuario", back_populates="unidade")
    terminais = relationship("Terminal", back_populates="unidade")
    usos = relationship("UsoSacola", back_populates="unidade")
    logs = relationship("LogAuditoria", back_populates="unidade")


class DescontoClienteEntidade(Base):
    """
    Rastreia progresso de desconto de cada cliente em cada entidade
    Ex: Jean tem 5 usos no Zaffari, 2 no Mercadinho
    """
    __tablename__ = "descontos_cliente_entidade"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(String, ForeignKey("clientes.cpf"), nullable=False)
    entidade_id = Column(Integer, ForeignKey("entidades.id"), nullable=False)
    usos_count = Column(Integer, default=0)
    proximo_desconto_percentual = Column(Float, default=0)
    ultima_atualizacao = Column(DateTime, default=datetime.now)
    
    # Relationships
    cliente = relationship("Cliente", back_populates="descontos")
    entidade = relationship("Entidade", back_populates="descontos")


class Terminal(Base):
    """
    Terminal = Caixa/PDV de uma unidade
    Ex: Terminal 001 do Zaffari Iguatemi
    """
    __tablename__ = "terminais"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, nullable=False)
    descricao = Column(String, nullable=True)
    entidade_id = Column(Integer, ForeignKey("entidades.id"), nullable=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=True)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    
    # Relationships
    entidade = relationship("Entidade", back_populates="terminais")
    unidade = relationship("Unidade", back_populates="terminais")
    usos = relationship("UsoSacola", back_populates="terminal")
    logs = relationship("LogAuditoria", back_populates="terminal")


# ============================================
# MODELS CORE
# ============================================

class Cliente(Base):
    """Cliente cadastrado no sistema (compartilhado entre entidades)"""
    __tablename__ = "clientes"
    
    cpf = Column(String, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=True)
    data_cadastro = Column(DateTime, default=datetime.now)
    
    # Campos de suspensão
    status_beneficios = Column(Enum(StatusBeneficios), default=StatusBeneficios.ativo, nullable=False)
    motivo_suspensao = Column(String, nullable=True)
    data_suspensao = Column(DateTime, nullable=True)
    
    # Relationships
    sacolas = relationship("Sacola", back_populates="cliente")
    notificacoes = relationship("Notificacao", back_populates="cliente")
    descontos = relationship("DescontoClienteEntidade", back_populates="cliente")


class Lote(Base):
    """Lote de sacolas fabricadas"""
    __tablename__ = "lotes"
    
    id = Column(Integer, primary_key=True, index=True)
    data_fabricacao = Column(String, nullable=False)
    data_importacao = Column(DateTime, default=datetime.now)
    quantidade = Column(Integer, nullable=False)
    inicio = Column(Integer, nullable=False)
    fim = Column(Integer, nullable=False)
    arquivo_csv = Column(String, nullable=True)
    
    # Relationships
    sacolas = relationship("Sacola", back_populates="lote")


class Sacola(Base):
    """Sacola reutilizável do programa (compartilhada entre entidades)"""
    __tablename__ = "sacolas"
    
    id = Column(String, primary_key=True, index=True)
    qrcode = Column(String, unique=True, nullable=False)
    data_criacao = Column(String, nullable=False)
    checksum = Column(String, nullable=True)
    status = Column(Enum(StatusSacola), default=StatusSacola.estoque, nullable=False)
    vida_util_dias = Column(Integer, default=365)
    ativo = Column(Boolean, default=True)
    
    # Relacionamento com lote
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=True)
    lote = relationship("Lote", back_populates="sacolas")
    
    # Relacionamento com cliente
    cliente_cpf = Column(String, ForeignKey("clientes.cpf"), nullable=True)
    cliente = relationship("Cliente", back_populates="sacolas")
    
    # Controle de uso
    data_vinculacao = Column(DateTime, nullable=True)
    utilizacoes = Column(Integer, default=0)
    ultima_utilizacao = Column(DateTime, nullable=True)
    data_devolucao = Column(DateTime, nullable=True)
    
    # Relationships
    registros = relationship("RegistroUso", back_populates="sacola")
    usos = relationship("UsoSacola", back_populates="sacola")


class RegistroUso(Base):
    """Registro simplificado de uso da sacola (tabela legada)"""
    __tablename__ = "registros_uso"
    
    id = Column(Integer, primary_key=True, index=True)
    sacola_id = Column(String, ForeignKey("sacolas.id"))
    data_uso = Column(DateTime, default=datetime.now)
    valor_compra = Column(Float, nullable=False)
    
    # Relationships
    sacola = relationship("Sacola", back_populates="registros")


class UsoSacola(Base):
    """
    Registro completo de uso da sacola (multi-tenant)
    Registra entidade + unidade onde foi usado
    """
    __tablename__ = "usos_sacola"
    
    id = Column(Integer, primary_key=True, index=True)
    sacola_id = Column(String, ForeignKey("sacolas.id"), nullable=False)
    entidade_id = Column(Integer, ForeignKey("entidades.id"), nullable=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=True)
    terminal_id = Column(Integer, ForeignKey("terminais.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    valor_compra = Column(Float, nullable=True)
    desconto_aplicado = Column(Float, default=0)
    tipo_desconto = Column(String, nullable=True)  # 'meta' ou 'devolucao'
    data_hora = Column(DateTime, default=datetime.now)
    
    # Relationships
    sacola = relationship("Sacola", back_populates="usos")
    entidade = relationship("Entidade", back_populates="usos")
    unidade = relationship("Unidade", back_populates="usos")
    terminal = relationship("Terminal", back_populates="usos")
    usuario = relationship("Usuario", back_populates="usos")


# ============================================
# MODELS SISTEMA
# ============================================

class Usuario(Base):
    """
    Usuários do sistema com autenticação
    Admin: entidade_id=NULL, unidade_id=NULL (vê tudo)
    Gerente/Caixa: vinculados a entidade e unidade específica
    """
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    nome = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    
    # Multi-tenancy (NULL para admins globais)
    entidade_id = Column(Integer, ForeignKey("entidades.id"), nullable=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=True)
    
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.now)
    ultimo_login = Column(DateTime, nullable=True)
    
    # Relationships
    entidade = relationship("Entidade", back_populates="usuarios")
    unidade = relationship("Unidade", back_populates="usuarios")
    usos = relationship("UsoSacola", back_populates="usuario")
    logs = relationship("LogAuditoria", back_populates="usuario")


class LogAuditoria(Base):
    """
    Logs de auditoria de ações administrativas
    Registra entidade e unidade do contexto
    """
    __tablename__ = "logs_auditoria"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    
    # Multi-tenancy
    entidade_id = Column(Integer, ForeignKey("entidades.id"), nullable=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=True)
    terminal_id = Column(Integer, ForeignKey("terminais.id"), nullable=True)
    
    acao = Column(String, nullable=False)
    tabela = Column(String, nullable=True)
    registro_id = Column(Integer, nullable=True)
    detalhes = Column(Text, nullable=True)
    ip = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    
    # Relationships
    usuario = relationship("Usuario", back_populates="logs")
    entidade = relationship("Entidade", back_populates="logs")
    unidade = relationship("Unidade", back_populates="logs")
    terminal = relationship("Terminal", back_populates="logs")


# ============================================
# MODELS ALERTAS E NOTIFICAÇÕES
# ============================================

class Alerta(Base):
    """Alertas de fraude detectados automaticamente"""
    __tablename__ = "alertas"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum(TipoAlerta), nullable=False)
    gravidade = Column(Enum(GravidadeAlerta), nullable=False)
    cliente_cpf = Column(String, ForeignKey("clientes.cpf"), nullable=False)
    descricao = Column(Text, nullable=False)
    data_deteccao = Column(DateTime, default=datetime.now)
    resolvido = Column(Boolean, default=False)
    observacao = Column(Text, nullable=True)
    data_resolucao = Column(DateTime, nullable=True)


class Notificacao(Base):
    """Notificações para clientes"""
    __tablename__ = "notificacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_cpf = Column(String, ForeignKey("clientes.cpf"), nullable=False)
    tipo = Column(Enum(TipoNotificacao), nullable=False)
    titulo = Column(String, nullable=False)
    mensagem = Column(Text, nullable=False)
    lida = Column(Boolean, default=False)
    data_criacao = Column(DateTime, default=datetime.now)
    data_leitura = Column(DateTime, nullable=True)
    
    # Relationships
    cliente = relationship("Cliente", back_populates="notificacoes")