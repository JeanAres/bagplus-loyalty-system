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

class Lote(Base):
    """Lote de sacolas fabricadas"""
    __tablename__ = "lotes"
    
    id = Column(Integer, primary_key=True, index=True)
    data_fabricacao = Column(String, nullable=False)  # Data impressa no QR Code
    data_importacao = Column(DateTime, default=datetime.now)
    quantidade = Column(Integer, nullable=False)
    inicio = Column(Integer, nullable=False)  # BAG-00001 = 1
    fim = Column(Integer, nullable=False)     # BAG-00005 = 5
    arquivo_csv = Column(String, nullable=True)
    
    # Relacionamento
    sacolas = relationship("Sacola", back_populates="lote")

class Cliente(Base):
    """Cliente cadastrado no sistema"""
    __tablename__ = "clientes"
    
    cpf = Column(String, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    data_cadastro = Column(DateTime, default=datetime.now)
    
    # Relacionamento
    sacolas = relationship("Sacola", back_populates="cliente")

class Sacola(Base):
    """Sacola reutilizável do programa"""
    __tablename__ = "sacolas"
    
    id = Column(String, primary_key=True, index=True)  # BAG-00001
    data_criacao = Column(String, nullable=False)  # Data de fabricação (do QR Code)
    checksum = Column(String, nullable=False)  # Código de verificação
    status = Column(Enum(StatusSacola), default=StatusSacola.estoque, nullable=False)
    
    # Relacionamento com lote
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=True)
    lote = relationship("Lote", back_populates="sacolas")
    
    # Relacionamento com cliente (só preenchido quando status = ativo)
    cliente_cpf = Column(String, ForeignKey("clientes.cpf"), nullable=True)
    cliente = relationship("Cliente", back_populates="sacolas")
    
    # Controle de uso
    data_vinculacao = Column(DateTime, nullable=True)  # Quando foi ativada
    utilizacoes = Column(Integer, default=0)
    ultima_utilizacao = Column(DateTime, nullable=True)
    data_devolucao = Column(DateTime, nullable=True)
    
    # Relacionamento
    registros = relationship("RegistroUso", back_populates="sacola")

class RegistroUso(Base):
    """Registro de cada uso da sacola"""
    __tablename__ = "registros_uso"
    
    id = Column(Integer, primary_key=True, index=True)
    sacola_id = Column(String, ForeignKey("sacolas.id"))
    data_uso = Column(DateTime, default=datetime.now)
    
    # Relacionamento
    sacola = relationship("Sacola", back_populates="registros")