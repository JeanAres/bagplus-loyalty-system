# backend/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db, init_db
from models import Cliente, Sacola, RegistroUso

# Criar aplicação FastAPI
app = FastAPI(
    title="Bag+ API",
    description="Sistema de fidelização com EcoBags sustentáveis",
    version="1.0.0"
)

# CORS - Permite que frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar banco de dados ao subir servidor
@app.on_event("startup")
def startup_event():
    print("Iniciando Bag+ API...")
    init_db()
    print("API pronta!")

# Endpoint raiz - Teste básico
@app.get("/")
def root():
    return {
        "message": "Bag+ API funcionando!",
        "version": "1.0.0",
        "status": "online"
    }

# Endpoint: Criar cliente
@app.post("/api/clientes")
def criar_cliente(cpf: str, nome: str, db: Session = Depends(get_db)):
    """Cria um novo cliente no sistema"""
    
    # Verificar se cliente já existe
    cliente_existente = db.query(Cliente).filter(Cliente.cpf == cpf).first()
    if cliente_existente:
        raise HTTPException(status_code=400, detail="Cliente já cadastrado")
    
    # Criar cliente
    cliente = Cliente(cpf=cpf, nome=nome)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    
    return {
        "sucesso": True,
        "mensagem": "Cliente criado com sucesso",
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "data_adesao": cliente.data_adesao
        }
    }

# Endpoint: Criar sacola
@app.post("/api/sacolas")
def criar_sacola(sacola_id: str, cpf_cliente: str, db: Session = Depends(get_db)):
    """Cria uma nova sacola vinculada a um cliente"""
    
    # Verificar se cliente existe
    cliente = db.query(Cliente).filter(Cliente.cpf == cpf_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Verificar se sacola já existe
    sacola_existente = db.query(Sacola).filter(Sacola.id == sacola_id).first()
    if sacola_existente:
        raise HTTPException(status_code=400, detail="Sacola já cadastrada")
    
    # Criar sacola
    sacola = Sacola(id=sacola_id, cpf_cliente=cpf_cliente)
    db.add(sacola)
    db.commit()
    db.refresh(sacola)
    
    return {
        "sucesso": True,
        "mensagem": "Sacola criada com sucesso",
        "sacola": {
            "id": sacola.id,
            "cpf_cliente": sacola.cpf_cliente,
            "data_compra": sacola.data_compra
        }
    }

# Endpoint: Buscar sacola por ID
@app.get("/api/sacolas/{sacola_id}")
def buscar_sacola(sacola_id: str, db: Session = Depends(get_db)):
    """Busca informações de uma sacola pelo ID"""
    
    sacola = db.query(Sacola).filter(Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    cliente = db.query(Cliente).filter(Cliente.cpf == sacola.cpf_cliente).first()
    
    # Calcular dias de uso
    dias_uso = (datetime.now() - sacola.data_compra).days
    
    return {
        "sacola": {
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "dias_de_uso": dias_uso,
            "status": sacola.status,
            "ultima_utilizacao": sacola.ultima_utilizacao
        },
        "cliente": {
            "nome": cliente.nome,
            "cpf": cliente.cpf
        }
    }

# Endpoint: Buscar sacolas por CPF
@app.get("/api/clientes/{cpf}/sacolas")
def buscar_sacolas_por_cpf(cpf: str, db: Session = Depends(get_db)):
    """Lista todas as sacolas ativas de um cliente"""
    
    cliente = db.query(Cliente).filter(Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    sacolas = db.query(Sacola).filter(
        Sacola.cpf_cliente == cpf,
        Sacola.status == "ativo"
    ).all()
    
    resultado = []
    for sacola in sacolas:
        dias_uso = (datetime.now() - sacola.data_compra).days
        resultado.append({
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "dias_de_uso": dias_uso,
            "status": sacola.status
        })
    
    return {
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome
        },
        "total_sacolas": len(resultado),
        "sacolas": resultado
    }

# Endpoint: Registrar uso de sacola
@app.post("/api/sacolas/registrar-uso")
def registrar_uso(sacola_id: str, db: Session = Depends(get_db)):
    """Registra o uso de uma sacola"""
    
    sacola = db.query(Sacola).filter(Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    # Validações
    if sacola.status != "ativo":
        raise HTTPException(status_code=400, detail="Sacola não está ativa")
    
    if sacola.utilizacoes >= 40:
        raise HTTPException(status_code=400, detail="Limite de utilizações atingido")
    
    dias_uso = (datetime.now() - sacola.data_compra).days
    if dias_uso >= 90:
        raise HTTPException(status_code=400, detail="Prazo de 90 dias expirado")
    
    # Registrar uso
    sacola.utilizacoes += 1
    sacola.ultima_utilizacao = datetime.now()
    sacola.dias_de_uso = dias_uso
    
    # Criar registro
    registro = RegistroUso(sacola_id=sacola_id)
    db.add(registro)
    
    db.commit()
    db.refresh(sacola)
    
    return {
        "sucesso": True,
        "mensagem": "Uso registrado com sucesso",
        "sacola": {
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "dias_de_uso": sacola.dias_de_uso
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)