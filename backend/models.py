# backend/models.py
from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, Enum
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