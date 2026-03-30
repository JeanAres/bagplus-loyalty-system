# backend/models.py
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Cliente(Base):
    """Tabela de clientes cadastrados no programa"""
    __tablename__ = "clientes"
    
    cpf = Column(String(14), primary_key=True)
    nome = Column(String(100), nullable=False)
    data_adesao = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="ativo")  # ativo, inativo

class Sacola(Base):
    """Tabela de sacolas individuais"""
    __tablename__ = "sacolas"
    
    id = Column(String(20), primary_key=True)  # BAG-00001
    cpf_cliente = Column(String(14), ForeignKey("clientes.cpf"), nullable=False)
    data_compra = Column(DateTime, default=datetime.now)
    utilizacoes = Column(Integer, default=0)
    dias_de_uso = Column(Integer, default=0)
    ultima_utilizacao = Column(DateTime, nullable=True)
    status = Column(String(20), default="ativo")  # ativo, devolvido
    data_devolucao = Column(DateTime, nullable=True)

class RegistroUso(Base):
    """Histórico de cada uso de sacola"""
    __tablename__ = "registros_uso"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sacola_id = Column(String(20), ForeignKey("sacolas.id"), nullable=False)
    data = Column(DateTime, default=datetime.now)
    valor_compra = Column(Float, nullable=True)
    observacao = Column(Text, nullable=True)

class Devolucao(Base):
    """Registro de devoluções de sacolas"""
    __tablename__ = "devolucoes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sacola_id = Column(String(20), ForeignKey("sacolas.id"), nullable=False)
    data_devolucao = Column(DateTime, default=datetime.now)
    desconto_concedido = Column(Float, default=0.0)
    observacao = Column(Text, nullable=True)