# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# Enums
class StatusSacola(str, enum.Enum):
    estoque = "estoque"  
    ativo = "ativo"      
    devolvido = "devolvido"

class StatusBeneficios(str, enum.Enum):
    """Status dos benefícios do cliente"""
    ativo = "ativo"
    suspenso = "suspenso"
    bloqueado = "bloqueado"

class TipoAlerta(str, enum.Enum):
    """Tipos de alertas de detecção"""
    valores_diferentes_mesmo_dia = "valores_diferentes_mesmo_dia"
    valor_repetido_dias_diferentes = "valor_repetido_dias_diferentes"
    abuso_valor_minimo = "abuso_valor_minimo"

class GravidadeAlerta(str, enum.Enum):
    """Gravidade dos alertas"""
    baixa = "baixa"
    media = "media"
    alta = "alta"

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
    
    sacolas = relationship("Sacola", back_populates="lote")

class Cliente(Base):
    """Cliente cadastrado no sistema"""
    __tablename__ = "clientes"
    
    cpf = Column(String, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now)
    
    # Campos de suspensão
    status_beneficios = Column(Enum(StatusBeneficios), default=StatusBeneficios.ativo, nullable=False)
    motivo_suspensao = Column(String, nullable=True)
    data_suspensao = Column(DateTime, nullable=True)
    
    sacolas = relationship("Sacola", back_populates="cliente")
    alertas = relationship("Alerta", back_populates="cliente")

class Sacola(Base):
    """Sacola reutilizável do programa"""
    __tablename__ = "sacolas"
    
    id = Column(String, primary_key=True, index=True)
    data_criacao = Column(String, nullable=False)
    checksum = Column(String, nullable=False)
    status = Column(Enum(StatusSacola), default=StatusSacola.estoque, nullable=False)
    
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=True)
    lote = relationship("Lote", back_populates="sacolas")
    
    cliente_cpf = Column(String, ForeignKey("clientes.cpf"), nullable=True)
    cliente = relationship("Cliente", back_populates="sacolas")
    
    data_vinculacao = Column(DateTime, nullable=True)
    utilizacoes = Column(Integer, default=0)
    ultima_utilizacao = Column(DateTime, nullable=True)
    data_devolucao = Column(DateTime, nullable=True)
    
    registros = relationship("RegistroUso", back_populates="sacola")

class RegistroUso(Base):
    """Registro de cada uso da sacola"""
    __tablename__ = "registros_uso"
    
    id = Column(Integer, primary_key=True, index=True)
    sacola_id = Column(String, ForeignKey("sacolas.id"))
    data_uso = Column(DateTime, default=datetime.now)
    valor_compra = Column(Float, nullable=False)
    
    sacola = relationship("Sacola", back_populates="registros")

class Alerta(Base):
    """Alertas de detecção de padrões suspeitos"""
    __tablename__ = "alertas"
    
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(Enum(TipoAlerta), nullable=False)
    gravidade = Column(Enum(GravidadeAlerta), nullable=False)
    cliente_cpf = Column(String, ForeignKey("clientes.cpf"), nullable=False)
    descricao = Column(String, nullable=False)
    data_deteccao = Column(DateTime, default=datetime.now)
    resolvido = Column(Boolean, default=False)
    observacao = Column(String, nullable=True)
    data_resolucao = Column(DateTime, nullable=True)
    
    cliente = relationship("Cliente", back_populates="alertas")

    # ========== AUTENTICAÇÃO E SEGURANÇA ==========

class RoleUsuario(str, Enum):
    """Papéis de usuário no sistema"""
    admin = "admin"
    gerente = "gerente"
    caixa = "caixa"


class Usuario(Base):
    """Usuários do sistema com autenticação"""
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nome = Column(String(100), nullable=False)
    role = Column(Enum("admin", "gerente", "caixa", name="role_usuario"), nullable=False, default="caixa")
    ativo = Column(Boolean, default=True, nullable=False)
    data_criacao = Column(DateTime, default=datetime.now, nullable=False)
    ultimo_login = Column(DateTime, nullable=True)


class LogAuditoria(Base):
    """Log de ações administrativas para auditoria"""
    __tablename__ = "logs_auditoria"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    usuario_username = Column(String(50), nullable=True)  # Guardamos username também
    acao = Column(String(50), nullable=False, index=True)
    entidade_tipo = Column(String(50), nullable=True)
    entidade_id = Column(String(50), nullable=True)
    detalhes = Column(Text, nullable=True)  # JSON em string
    ip_address = Column(String(45), nullable=True)
    data_hora = Column(DateTime, default=datetime.now, nullable=False, index=True)
    
    # Relacionamento
    usuario = relationship("Usuario")