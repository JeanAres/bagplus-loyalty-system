from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, engine
import models
from datetime import datetime

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bag+ API", version="1.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de marcos de fidelidade
MARCOS_FIDELIDADE = {
    10: 5.00,    # 10 usos = R$ 5,00
    20: 10.00,   # 20 usos = R$ 10,00
    30: 15.00,   # 30 usos = R$ 15,00
    40: 20.00    # 40 usos = R$ 20,00
}

def calcular_desconto_fidelidade(utilizacoes):
    """
    Calcula desconto por fidelidade baseado em marcos
    Retorna o desconto acumulado e próximo marco
    """
    desconto_acumulado = 0
    proximo_marco = None
    proximo_desconto = 0
    usos_para_proximo = 0
    
    # Somar todos os descontos dos marcos atingidos
    for marco, valor_desconto in sorted(MARCOS_FIDELIDADE.items()):
        if utilizacoes >= marco:
            desconto_acumulado = valor_desconto  # Pega o maior desconto atingido
        elif proximo_marco is None:
            # Encontrou o próximo marco não atingido
            proximo_marco = marco
            proximo_desconto = valor_desconto
            usos_para_proximo = marco - utilizacoes
            break
    
    return {
        "desconto_atual": desconto_acumulado,
        "proximo_marco": proximo_marco,
        "proximo_desconto": proximo_desconto,
        "usos_para_proximo": usos_para_proximo
    }

@app.get("/")
def read_root():
    return {"message": "Bag+ API - Sistema de Fidelização Sustentável"}

# Endpoint: Criar cliente
@app.post("/api/clientes")
def criar_cliente(cpf: str, nome: str, db: Session = Depends(get_db)):
    """Cria um novo cliente no sistema"""
    
    # Validar CPF (apenas números)
    cpf_numeros = cpf.replace('.', '').replace('-', '')
    if len(cpf_numeros) != 11 or not cpf_numeros.isdigit():
        raise HTTPException(status_code=400, detail="CPF inválido. Deve conter 11 dígitos")
    
    # Validar nome
    if len(nome.strip()) < 3:
        raise HTTPException(status_code=400, detail="Nome deve ter pelo menos 3 caracteres")
    
    # Verificar se cliente já existe
    cliente_existente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if cliente_existente:
        raise HTTPException(status_code=400, detail="Cliente já cadastrado")
    
    # Criar cliente
    cliente = models.Cliente(cpf=cpf, nome=nome.strip())
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

# Endpoint: Listar sacolas de um cliente
@app.get("/api/clientes/{cpf}/sacolas")
def listar_sacolas_cliente(cpf: str, db: Session = Depends(get_db)):
    """Lista todas as sacolas ativas de um cliente"""
    
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    sacolas = db.query(models.Sacola).filter(
        models.Sacola.cpf_cliente == cpf,
        models.Sacola.status == "ativo"
    ).all()
    
    sacolas_data = []
    for sacola in sacolas:
        dias_uso = (datetime.now() - sacola.data_compra).days
        sacolas_data.append({
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "dias_de_uso": dias_uso,
            "status": sacola.status
        })
    
    return {
        "cliente": {
            "nome": cliente.nome,
            "cpf": cliente.cpf
        },
        "total_sacolas": len(sacolas_data),
        "sacolas": sacolas_data
    }

# Endpoint: Buscar sacola por ID
@app.get("/api/sacolas/{sacola_id}")
def buscar_sacola(sacola_id: str, db: Session = Depends(get_db)):
    """Busca informações de uma sacola pelo ID"""
    
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == sacola.cpf_cliente).first()
    
    # Calcular dias de uso
    dias_uso = (datetime.now() - sacola.data_compra).days
    
    # Calcular desconto de fidelidade
    fidelidade = calcular_desconto_fidelidade(sacola.utilizacoes)
    
    # Calcular desconto de devolução (baseado em estado + mínimo de usos)
    utilizacoes = sacola.utilizacoes
    
    # Determinar desconto baseado no estado da sacola
    if utilizacoes >= 10 and utilizacoes <= 15 and dias_uso <= 60:
        # 🟢 Verde - Estado ótimo (MÍNIMO 10 usos)
        desconto_devolucao = 40.00
        estado = "verde"
    elif utilizacoes >= 16 and utilizacoes <= 25 and dias_uso <= 80:
        # 🟡 Amarelo - Estado médio (MÍNIMO 16 usos)
        desconto_devolucao = 20.00
        estado = "amarelo"
    elif utilizacoes >= 26 and utilizacoes <= 40 and dias_uso <= 90:
        # 🔴 Vermelho - Fim de vida (MÍNIMO 26 usos)
        desconto_devolucao = 10.00
        estado = "vermelho"
    else:
        # ⚫ Sem desconto (menos de 10 usos OU passou limites)
        desconto_devolucao = 0.00
        estado = "sem_desconto"
    
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
        },
        "fidelidade": fidelidade,
        "desconto_devolucao": desconto_devolucao,
        "estado": estado
    }

# Endpoint: Criar sacola
@app.post("/api/sacolas")
def criar_sacola(cpf_cliente: str, db: Session = Depends(get_db)):
    """Cria uma nova sacola para um cliente"""
    
    # Verificar se cliente existe
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Buscar último ID de sacola no banco
    ultima_sacola = db.query(models.Sacola).order_by(models.Sacola.id.desc()).first()
    
    if ultima_sacola:
        # Extrair número do último ID (BAG-00123 -> 123)
        ultimo_numero = int(ultima_sacola.id.split('-')[1])
        novo_numero = ultimo_numero + 1
    else:
        novo_numero = 1
    
    # Gerar ID no formato BAG-00001
    sacola_id = f"BAG-{novo_numero:05d}"
    
    # Criar sacola
    sacola = models.Sacola(id=sacola_id, cpf_cliente=cpf_cliente)
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

# Endpoint: Criar múltiplas sacolas de uma vez
@app.post("/api/sacolas/criar-lote")
def criar_lote_sacolas(cpf_cliente: str, quantidade: int, db: Session = Depends(get_db)):
    """Cria múltiplas sacolas para um cliente de uma vez"""
    
    # Verificar se cliente existe
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    if quantidade < 1 or quantidade > 20:
        raise HTTPException(status_code=400, detail="Quantidade deve ser entre 1 e 20")
    
    # Buscar último ID de sacola no banco
    ultima_sacola = db.query(models.Sacola).order_by(models.Sacola.id.desc()).first()
    
    if ultima_sacola:
        # Extrair número do último ID (BAG-00123 -> 123)
        ultimo_numero = int(ultima_sacola.id.split('-')[1])
    else:
        ultimo_numero = 0
    
    # Criar sacolas
    sacolas_criadas = []
    for i in range(quantidade):
        novo_numero = ultimo_numero + i + 1
        sacola_id = f"BAG-{novo_numero:05d}"
        
        sacola = models.Sacola(id=sacola_id, cpf_cliente=cpf_cliente)
        db.add(sacola)
        sacolas_criadas.append(sacola_id)
    
    db.commit()
    
    return {
        "sucesso": True,
        "mensagem": f"{quantidade} sacolas criadas com sucesso",
        "sacolas": sacolas_criadas
    }

# Endpoint: Registrar uso de sacola
@app.post("/api/sacolas/registrar-uso")
def registrar_uso(sacola_id: str, db: Session = Depends(get_db)):
    """Registra o uso de uma sacola"""
    
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    if sacola.status != "ativo":
        raise HTTPException(status_code=400, detail="Sacola não está ativa")
    
    if sacola.utilizacoes >= 40:
        raise HTTPException(status_code=400, detail="Sacola atingiu limite de 40 utilizações")
    
    # Atualizar sacola
    sacola.utilizacoes += 1
    sacola.ultima_utilizacao = datetime.now()
    
    # Criar registro de uso
    registro = models.RegistroUso(sacola_id=sacola_id)
    db.add(registro)
    
    db.commit()
    db.refresh(sacola)
    
    return {
        "sucesso": True,
        "mensagem": "Uso registrado com sucesso",
        "sacola": {
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "ultima_utilizacao": sacola.ultima_utilizacao
        }
    }

# Endpoint: Devolver sacola
@app.post("/api/sacolas/devolver")
def devolver_sacola(sacola_id: str, db: Session = Depends(get_db)):
    """Processa a devolução de uma sacola"""
    
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    if sacola.status != "ativo":
        raise HTTPException(status_code=400, detail="Sacola já foi devolvida")
    
    # Calcular dias de uso
    dias_uso = (datetime.now() - sacola.data_compra).days
    utilizacoes = sacola.utilizacoes
    
    # Calcular desconto baseado no estado da sacola (COM MÍNIMO DE USOS)
    if utilizacoes >= 10 and utilizacoes <= 15 and dias_uso <= 60:
        desconto = 40.00  # Verde
    elif utilizacoes >= 16 and utilizacoes <= 25 and dias_uso <= 80:
        desconto = 20.00  # Amarelo
    elif utilizacoes >= 26 and utilizacoes <= 40 and dias_uso <= 90:
        desconto = 10.00  # Vermelho
    else:
        desconto = 0.00   # Sem desconto
    
    # Atualizar sacola
    sacola.status = "devolvido"
    sacola.data_devolucao = datetime.now()
    
    # Criar registro de devolução
    devolucao = models.Devolucao(
        sacola_id=sacola_id,
        desconto_concedido=desconto
    )
    db.add(devolucao)
    
    db.commit()
    
    return {
        "sucesso": True,
        "mensagem": "Devolução processada com sucesso",
        "devolucao": {
            "sacola_id": sacola_id,
            "desconto_concedido": desconto,
            "data_devolucao": devolucao.data_devolucao
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)