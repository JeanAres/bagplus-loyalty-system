from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db, engine
import models
from datetime import datetime, timedelta
import os
import hashlib

# Criar tabelas
models.Base.metadata.create_all(bind=engine)

# ========== FUNÇÕES AUXILIARES ==========

def validar_qrcode_checksum(qr_code: str):
    """
    Valida formato e checksum de um QR Code
    
    Retorna: (valido: bool, sacola_id: str, data_criacao: str, erro: str)
    """
    
    # 1. VALIDAR FORMATO
    partes = qr_code.split(':')
    if len(partes) != 3:
        return False, None, None, "Formato inválido. Esperado: BAG-00001:2026-03-31:abc123"
    
    sacola_id = partes[0]
    data_criacao = partes[1]
    checksum_recebido = partes[2]
    
    # 2. VALIDAR ID
    if not sacola_id.startswith('BAG-'):
        return False, None, None, "ID deve começar com BAG-"
    
    try:
        numero = int(sacola_id.split('-')[1])
        if numero < 1:
            return False, None, None, "Número do ID inválido"
    except:
        return False, None, None, "Formato de ID inválido"
    
    # 3. VALIDAR DATA
    try:
        datetime.strptime(data_criacao, '%Y-%m-%d')
    except:
        return False, None, None, "Data inválida. Formato esperado: AAAA-MM-DD"
    
    # 4. VALIDAR CHECKSUM
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        return False, None, None, "Erro de configuração do servidor"
    
    texto = f"{sacola_id}{data_criacao}{SECRET_KEY}"
    hash_completo = hashlib.sha256(texto.encode()).hexdigest()
    checksum_correto = hash_completo[:6]
    
    if checksum_recebido != checksum_correto:
        return False, None, None, "QR Code inválido ou falsificado"
    
    # TUDO VÁLIDO
    return True, sacola_id, data_criacao, None

# ========== FUNÇÕES DE DETECÇÃO DE PADRÕES ==========

def detectar_valores_diferentes_mesmo_dia(cliente_cpf: str, db: Session):
    """
    Detecta uso de múltiplas sacolas com valores diferentes no mesmo dia
    
    Lógica: Se é rancho, todos os valores devem ser iguais.
    Se tem 4+ sacolas com valores diferentes = SUSPEITO
    """
    hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Buscar registros de hoje
    registros_hoje = db.query(models.RegistroUso).join(
        models.Sacola
    ).filter(
        models.Sacola.cliente_cpf == cliente_cpf,
        models.RegistroUso.data_uso >= hoje_inicio
    ).all()
    
    if len(registros_hoje) < 4:
        return  # Poucos usos, normal
    
    # Verificar quantos valores únicos existem
    valores = [r.valor_compra for r in registros_hoje]
    valores_unicos = len(set(valores))
    
    # Se tem mais de 2 valores diferentes = suspeito
    if valores_unicos > 2:
        # Verificar se alerta já existe hoje
        alerta_existe = db.query(models.Alerta).filter(
            models.Alerta.cliente_cpf == cliente_cpf,
            models.Alerta.tipo == models.TipoAlerta.valores_diferentes_mesmo_dia,
            models.Alerta.data_deteccao >= hoje_inicio,
            models.Alerta.resolvido == False
        ).first()
        
        if not alerta_existe:
            alerta = models.Alerta(
                tipo=models.TipoAlerta.valores_diferentes_mesmo_dia,
                gravidade=models.GravidadeAlerta.alta,
                cliente_cpf=cliente_cpf,
                descricao=f"Cliente usou {len(registros_hoje)} sacolas hoje com {valores_unicos} valores diferentes (esperado: valor único em rancho)"
            )
            db.add(alerta)
            db.commit()

def detectar_valor_repetido_dias_diferentes(cliente_cpf: str, db: Session):
    """
    Detecta se cliente sempre compra mesmo valor em dias separados
    
    Lógica: Se em 5+ dias diferentes sempre usa mesmo valor = SUSPEITO
    """
    trinta_dias_atras = datetime.now() - timedelta(days=30)
    
    registros = db.query(models.RegistroUso).join(
        models.Sacola
    ).filter(
        models.Sacola.cliente_cpf == cliente_cpf,
        models.RegistroUso.data_uso >= trinta_dias_atras
    ).all()
    
    if len(registros) < 10:
        return  # Poucos dados
    
    # Agrupar por dia
    usos_por_dia = {}
    for r in registros:
        dia = r.data_uso.date()
        if dia not in usos_por_dia:
            usos_por_dia[dia] = []
        usos_por_dia[dia].append(r.valor_compra)
    
    if len(usos_por_dia) < 5:
        return  # Poucos dias diferentes
    
    # Para cada dia, pegar o valor mais usado
    valores_por_dia = []
    for dia, valores in usos_por_dia.items():
        # Se dia tem valores iguais (rancho), pega qualquer um
        # Se dia tem valores diferentes, pega o mais comum
        valor_mais_comum = max(set(valores), key=valores.count)
        valores_por_dia.append(valor_mais_comum)
    
    # Verificar se sempre mesmo valor entre dias
    valor_mais_comum_geral = max(set(valores_por_dia), key=valores_por_dia.count)
    repeticoes = valores_por_dia.count(valor_mais_comum_geral)
    percentual = (repeticoes / len(valores_por_dia)) * 100
    
    if percentual >= 80:
        # Verificar se alerta já existe
        alerta_existe = db.query(models.Alerta).filter(
            models.Alerta.cliente_cpf == cliente_cpf,
            models.Alerta.tipo == models.TipoAlerta.valor_repetido_dias_diferentes,
            models.Alerta.resolvido == False
        ).first()
        
        if not alerta_existe:
            alerta = models.Alerta(
                tipo=models.TipoAlerta.valor_repetido_dias_diferentes,
                gravidade=models.GravidadeAlerta.media,
                cliente_cpf=cliente_cpf,
                descricao=f"Cliente compra sempre R$ {valor_mais_comum_geral:.2f} em {repeticoes} de {len(valores_por_dia)} dias diferentes (últimos 30 dias)"
            )
            db.add(alerta)
            db.commit()

def detectar_abuso_valor_minimo(cliente_cpf: str, db: Session):
    """
    Detecta uso excessivo com valor mínimo
    
    Lógica: Se usa 8+ sacolas no mesmo dia, todas com R$ 15,00 = SUSPEITO
    """
    hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    registros_hoje = db.query(models.RegistroUso).join(
        models.Sacola
    ).filter(
        models.Sacola.cliente_cpf == cliente_cpf,
        models.RegistroUso.data_uso >= hoje_inicio
    ).all()
    
    if len(registros_hoje) < 8:
        return  # Menos de 8 sacolas, ok
    
    # Contar quantos são R$ 15,00
    valores_minimos = [r for r in registros_hoje if r.valor_compra == 15.00]
    percentual_minimo = (len(valores_minimos) / len(registros_hoje)) * 100
    
    if percentual_minimo >= 90:
        # Verificar se alerta já existe hoje
        alerta_existe = db.query(models.Alerta).filter(
            models.Alerta.cliente_cpf == cliente_cpf,
            models.Alerta.tipo == models.TipoAlerta.abuso_valor_minimo,
            models.Alerta.data_deteccao >= hoje_inicio,
            models.Alerta.resolvido == False
        ).first()
        
        if not alerta_existe:
            alerta = models.Alerta(
                tipo=models.TipoAlerta.abuso_valor_minimo,
                gravidade=models.GravidadeAlerta.alta,
                cliente_cpf=cliente_cpf,
                descricao=f"Cliente usou {len(registros_hoje)} sacolas hoje, {len(valores_minimos)} com valor mínimo R$ 15,00 (possível fraude)"
            )
            db.add(alerta)
            db.commit()

# ========== CONFIGURAÇÃO DO APP ==========

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

# ========== ENDPOINTS DE CLIENTES ==========

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
            "data_cadastro": cliente.data_cadastro
        }
    }

@app.get("/api/clientes")
def listar_clientes(db: Session = Depends(get_db)):
    """Lista todos os clientes cadastrados"""
    
    clientes = db.query(models.Cliente).all()
    
    clientes_data = []
    for cliente in clientes:
        # Contar sacolas ativas
        sacolas_ativas = db.query(models.Sacola).filter(
            models.Sacola.cliente_cpf == cliente.cpf,
            models.Sacola.status == models.StatusSacola.ativo
        ).count()
        
        clientes_data.append({
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "data_cadastro": cliente.data_cadastro,
            "sacolas_ativas": sacolas_ativas
        })
    
    return {
        "total": len(clientes_data),
        "clientes": clientes_data
    }

@app.get("/api/clientes/{cpf}/sacolas")
def listar_sacolas_cliente(cpf: str, db: Session = Depends(get_db)):
    """Lista todas as sacolas ativas de um cliente"""
    
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    sacolas = db.query(models.Sacola).filter(
        models.Sacola.cliente_cpf == cpf,
        models.Sacola.status == models.StatusSacola.ativo
    ).all()
    
    sacolas_data = []
    for sacola in sacolas:
        if sacola.data_vinculacao:
            dias_uso = (datetime.now() - sacola.data_vinculacao).days
        else:
            dias_uso = 0
            
        sacolas_data.append({
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "dias_de_uso": dias_uso,
            "status": sacola.status.value,
            "data_criacao": sacola.data_criacao
        })
    
    return {
        "cliente": {
            "nome": cliente.nome,
            "cpf": cliente.cpf
        },
        "total_sacolas": len(sacolas_data),
        "sacolas": sacolas_data
    }

# ========== ENDPOINTS DE SACOLAS ==========

@app.get("/api/sacolas/{sacola_id}")
def buscar_sacola(sacola_id: str, db: Session = Depends(get_db)):
    """Busca informações de uma sacola pelo ID"""
    
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    # Se sacola está em estoque (não vinculada), retornar info básica
    if sacola.status == models.StatusSacola.estoque:
        return {
            "sacola": {
                "id": sacola.id,
                "status": "estoque",
                "data_criacao": sacola.data_criacao,
                "mensagem": "Sacola nunca foi vinculada a um cliente. Use /api/sacolas/ativar para vincular."
            }
        }
    
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == sacola.cliente_cpf).first()
    
    # Calcular dias de uso
    if sacola.data_vinculacao:
        dias_uso = (datetime.now() - sacola.data_vinculacao).days
    else:
        dias_uso = 0
    
    # Calcular desconto de fidelidade
    fidelidade = calcular_desconto_fidelidade(sacola.utilizacoes)
    
    # Calcular desconto de devolução (baseado em estado)
    utilizacoes = sacola.utilizacoes
    
    if utilizacoes >= 0 and utilizacoes <= 15 and dias_uso <= 60:
        desconto_devolucao = 40.00
        estado = "verde"
    elif utilizacoes >= 16 and utilizacoes <= 25 and dias_uso <= 80:
        desconto_devolucao = 20.00
        estado = "amarelo"
    elif utilizacoes >= 26 and utilizacoes <= 40 and dias_uso <= 90:
        desconto_devolucao = 10.00
        estado = "vermelho"
    else:
        desconto_devolucao = 0.00
        estado = "sem_desconto"
    
    return {
        "sacola": {
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "dias_de_uso": dias_uso,
            "status": sacola.status.value,
            "ultima_utilizacao": sacola.ultima_utilizacao,
            "data_criacao": sacola.data_criacao
        },
        "cliente": {
            "nome": cliente.nome if cliente else None,
            "cpf": cliente.cpf if cliente else None
        },
        "fidelidade": fidelidade,
        "desconto_devolucao": desconto_devolucao,
        "estado": estado
    }

@app.post("/api/sacolas/registrar-uso")
def registrar_uso(
    sacola_id: str, 
    valor_compra: str,
    db: Session = Depends(get_db)
    ):
    """Registra o uso de uma sacola com valor da compra"""
    
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    if sacola.status != models.StatusSacola.ativo:
        raise HTTPException(status_code=400, detail="Sacola não está ativa")
    
    # Verificar se cliente está suspenso
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == sacola.cliente_cpf).first()
    if cliente and cliente.status_beneficios != models.StatusBeneficios.ativo:
        if cliente.status_beneficios == models.StatusBeneficios.suspenso:
            raise HTTPException(
                status_code=403,
                detail=f"Cliente suspenso. Motivo: {cliente.motivo_suspensao or 'Não especificado'}"
            )
        elif cliente.status_beneficios == models.StatusBeneficios.bloqueado:
            raise HTTPException(
                status_code=403,
                detail="Cliente bloqueado permanentemente do programa"
            )
    
    if sacola.utilizacoes >= 40:
        raise HTTPException(status_code=400, detail="Sacola atingiu limite de 40 utilizações")
    
    
    # Validar intervalo de 4 horas entre usos
    if sacola.ultima_utilizacao:
        tempo_desde_ultimo_uso = datetime.now() - sacola.ultima_utilizacao
        horas_desde_ultimo_uso = tempo_desde_ultimo_uso.total_seconds() / 3600
        
        if horas_desde_ultimo_uso < 4:
            horas_restantes = 4 - horas_desde_ultimo_uso
            minutos_restantes = int(horas_restantes * 60)
            
            if horas_restantes >= 1:
                mensagem = f"Aguarde {horas_restantes:.1f} horas para usar esta sacola novamente"
            else:
                mensagem = f"Aguarde {minutos_restantes} minutos para usar esta sacola novamente"
            
            raise HTTPException(status_code=400, detail=mensagem)
    
    # Converter e validar valor da compra
    try:
        # Substituir vírgula por ponto
        valor_str = valor_compra.replace(',', '.')
        valor_float = float(valor_str)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail="Valor da compra inválido. Use formato: 120.50 ou 120,50"
        )
    
    if valor_float < 0:
        raise HTTPException(
            status_code=400, 
            detail="Valor da compra não pode ser negativo"
        )
    
    if valor_float < 15.00:
        raise HTTPException(
            status_code=400,
            detail="Valor mínimo de compra: R$ 15,00"
    )
    
    # Atualizar sacola
    sacola.utilizacoes += 1
    sacola.ultima_utilizacao = datetime.now()
    
    # Criar registro de uso com valor da compra
    registro = models.RegistroUso(
        sacola_id=sacola_id,
        valor_compra=valor_float
    )
    db.add(registro)
    
    db.commit()
    db.refresh(sacola)

    try:
        detectar_valores_diferentes_mesmo_dia(sacola.cliente_cpf, db)
        detectar_valor_repetido_dias_diferentes(sacola.cliente_cpf, db)
        detectar_abuso_valor_minimo(sacola.cliente_cpf, db)
    except Exception as e:
        # Não bloquear registro se detecção falhar
        print(f"Erro na detecção de padrões: {e}")
    
    return {
        "sucesso": True,
        "mensagem": "Uso registrado com sucesso",
        "sacola": {
            "id": sacola.id,
            "utilizacoes": sacola.utilizacoes,
            "ultima_utilizacao": sacola.ultima_utilizacao
        },
        "compra": {
            "valor": valor_float
        }
    }

@app.post("/api/sacolas/devolver")
def devolver_sacola(sacola_id: str, db: Session = Depends(get_db)):
    """Processa a devolução de uma sacola"""
    
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    if sacola.status != models.StatusSacola.ativo:
        raise HTTPException(status_code=400, detail="Sacola já foi devolvida ou não está ativa")
    
    # Calcular dias de uso
    if sacola.data_vinculacao:
        dias_uso = (datetime.now() - sacola.data_vinculacao).days
    else:
        dias_uso = 0
        
    utilizacoes = sacola.utilizacoes
    
    # Calcular desconto baseado no estado da sacola
    if utilizacoes >= 0 and utilizacoes <= 15 and dias_uso <= 60:
        desconto = 40.00  # Verde
    elif utilizacoes >= 16 and utilizacoes <= 25 and dias_uso <= 80:
        desconto = 20.00  # Amarelo
    elif utilizacoes >= 26 and utilizacoes <= 40 and dias_uso <= 90:
        desconto = 10.00  # Vermelho
    else:
        desconto = 0.00   # Sem desconto
    
    # Atualizar sacola
    sacola.status = models.StatusSacola.devolvido
    sacola.data_devolucao = datetime.now()
    
    db.commit()
    
    return {
        "sucesso": True,
        "mensagem": "Devolução processada com sucesso",
        "devolucao": {
            "sacola_id": sacola_id,
            "desconto_concedido": desconto,
            "data_devolucao": sacola.data_devolucao
        }
    }

# ========== ENDPOINT DE ATIVAÇÃO ==========

@app.post("/api/sacolas/ativar")
def ativar_sacola(qr_code: str, cpf_cliente: str, db: Session = Depends(get_db)):
    """
    Ativa uma sacola vinculando-a a um cliente pela primeira vez
    
    Parâmetros:
    - qr_code: Conteúdo completo do QR Code (ex: BAG-00001:2026-03-31:a3f9d2)
    - cpf_cliente: CPF do cliente que vai receber a sacola
    """
    
    # 1. VALIDAR QR CODE (usa função auxiliar)
    valido, sacola_id, data_criacao, erro = validar_qrcode_checksum(qr_code)
    
    if not valido:
        raise HTTPException(status_code=400, detail=erro)
    
    # 2. BUSCAR SACOLA NO BANCO
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(
            status_code=404,
            detail=f"Sacola {sacola_id} não encontrada no sistema. Verifique se o lote foi importado."
        )
    
    # 3. VALIDAR CHECKSUM DO BANCO (dupla verificação)
    if sacola.checksum != qr_code.split(':')[2]:
        raise HTTPException(
            status_code=403,
            detail="Checksum não confere com registro do banco. QR Code pode estar adulterado."
        )
    
    # 4. VERIFICAR SE SACOLA JÁ FOI ATIVADA
    if sacola.status != models.StatusSacola.estoque:
        if sacola.status == models.StatusSacola.ativo:
            cliente = db.query(models.Cliente).filter(models.Cliente.cpf == sacola.cliente_cpf).first()
            raise HTTPException(
                status_code=400,
                detail=f"Sacola já está vinculada ao cliente {cliente.nome} (CPF: {cliente.cpf})"
            )
        elif sacola.status == models.StatusSacola.devolvido:
            raise HTTPException(
                status_code=400,
                detail="Sacola já foi devolvida e não pode ser reativada"
            )
    
    # 5. VERIFICAR SE CLIENTE EXISTE
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf_cliente).first()
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente com CPF {cpf_cliente} não encontrado. Cadastre o cliente primeiro."
        )
    
    # 6. ATIVAR SACOLA (vincular ao cliente)
    sacola.status = models.StatusSacola.ativo
    sacola.cliente_cpf = cpf_cliente
    sacola.data_vinculacao = datetime.now()
    
    db.commit()
    db.refresh(sacola)
    
    return {
        "sucesso": True,
        "mensagem": f"Sacola {sacola_id} ativada e vinculada ao cliente com sucesso",
        "sacola": {
            "id": sacola.id,
            "status": sacola.status.value,
            "data_criacao": sacola.data_criacao,
            "data_vinculacao": sacola.data_vinculacao
        },
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome
        }
    }

# ========== ENDPOINTS DE HISTÓRICO E ESTATÍSTICAS ==========

@app.get("/api/sacolas/{sacola_id}/historico")
def historico_uso(sacola_id: str, db: Session = Depends(get_db)):
    """
    Retorna histórico completo de usos de uma sacola com valores de compra
    """
    # Verificar se sacola existe
    sacola = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
    if not sacola:
        raise HTTPException(status_code=404, detail="Sacola não encontrada")
    
    # Buscar registros de uso
    registros = db.query(models.RegistroUso).filter(
        models.RegistroUso.sacola_id == sacola_id
    ).order_by(models.RegistroUso.data_uso.desc()).all()
    
    # Calcular estatísticas
    total_gasto = sum(r.valor_compra for r in registros)
    valor_medio = total_gasto / len(registros) if registros else 0
    
    return {
        "sacola_id": sacola_id,
        "total_usos": len(registros),
        "total_gasto": round(total_gasto, 2),
        "valor_medio": round(valor_medio, 2),
        "historico": [
            {
                "id": r.id,
                "data_uso": r.data_uso,
                "valor_compra": r.valor_compra
            }
            for r in registros
        ]
    }

@app.get("/api/clientes/{cpf}/estatisticas")
def estatisticas_cliente(cpf: str, db: Session = Depends(get_db)):
    """
    Estatísticas de compras do cliente
    """
    # Verificar se cliente existe
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Buscar todas sacolas ativas do cliente
    sacolas = db.query(models.Sacola).filter(
        models.Sacola.cliente_cpf == cpf,
        models.Sacola.status == models.StatusSacola.ativo
    ).all()
    
    # Buscar registros de uso de todas as sacolas
    total_gasto = 0
    total_usos = 0
    
    for sacola in sacolas:
        registros = db.query(models.RegistroUso).filter(
            models.RegistroUso.sacola_id == sacola.id
        ).all()
        
        total_usos += len(registros)
        total_gasto += sum(r.valor_compra for r in registros)
    
    valor_medio = total_gasto / total_usos if total_usos > 0 else 0
    
    return {
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "data_cadastro": cliente.data_cadastro
        },
        "estatisticas": {
            "sacolas_ativas": len(sacolas),
            "total_usos": total_usos,
            "total_gasto": round(total_gasto, 2),
            "valor_medio_compra": round(valor_medio, 2)
        }
    }

# ========== ENDPOINTS DE ADMINISTRAÇÃO (LOTES) ==========

@app.post("/api/admin/lotes/importar")
def importar_lote_csv(
    data_fabricacao: str,
    inicio: int,
    fim: int,
    db: Session = Depends(get_db)
):
    """
    Importa lote de sacolas do CSV gerado
    
    Parâmetros:
    - data_fabricacao: Data impressa nos QR Codes (YYYY-MM-DD)
    - inicio: Primeiro ID do lote (ex: 1 para BAG-00001)
    - fim: Último ID do lote (ex: 5 para BAG-00005)
    """
    
    # Validar dados
    if fim < inicio:
        raise HTTPException(status_code=400, detail="Fim deve ser maior que início")
    
    quantidade = fim - inicio + 1
    
    # Criar registro do lote
    lote = models.Lote(
        data_fabricacao=data_fabricacao,
        quantidade=quantidade,
        inicio=inicio,
        fim=fim
    )
    db.add(lote)
    db.flush()  # Para obter o ID do lote
    
    # Função para gerar checksum (igual ao script)
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    def gerar_checksum(sacola_id, data_criacao):
        texto = f"{sacola_id}{data_criacao}{SECRET_KEY}"
        hash_completo = hashlib.sha256(texto.encode()).hexdigest()
        return hash_completo[:6]
    
    # Criar sacolas
    sacolas_criadas = []
    for num in range(inicio, fim + 1):
        sacola_id = f"BAG-{num:05d}"
        checksum = gerar_checksum(sacola_id, data_fabricacao)
        
        # Verificar se já existe
        existe = db.query(models.Sacola).filter(models.Sacola.id == sacola_id).first()
        if existe:
            raise HTTPException(
                status_code=400, 
                detail=f"Sacola {sacola_id} já existe no sistema"
            )
        
        sacola = models.Sacola(
            id=sacola_id,
            data_criacao=data_fabricacao,
            checksum=checksum,
            status=models.StatusSacola.estoque,
            lote_id=lote.id
        )
        db.add(sacola)
        sacolas_criadas.append(sacola_id)
    
    db.commit()
    
    return {
        "sucesso": True,
        "mensagem": f"Lote importado com sucesso",
        "lote": {
            "id": lote.id,
            "data_fabricacao": data_fabricacao,
            "quantidade": quantidade,
            "inicio": f"BAG-{inicio:05d}",
            "fim": f"BAG-{fim:05d}"
        },
        "sacolas_criadas": len(sacolas_criadas)
    }

@app.get("/api/admin/lotes")
def listar_lotes(db: Session = Depends(get_db)):
    """Lista todos os lotes importados"""
    lotes = db.query(models.Lote).all()
    
    return {
        "total": len(lotes),
        "lotes": [
            {
                "id": l.id,
                "data_fabricacao": l.data_fabricacao,
                "data_importacao": l.data_importacao,
                "quantidade": l.quantidade,
                "intervalo": f"BAG-{l.inicio:05d} até BAG-{l.fim:05d}"
            }
            for l in lotes
        ]
    }

# ========== ENDPOINTS DE ADMINISTRAÇÃO - SUSPENSÃO  ==========

@app.post("/api/admin/clientes/{cpf}/suspender")
def suspender_cliente(
    cpf: str,
    motivo: str,
    db: Session = Depends(get_db)
):
    """
    Suspende um cliente do programa de fidelização
    
    Parâmetros:
    - cpf: CPF do cliente
    - motivo: Motivo da suspensão
    """
    # Buscar cliente
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Verificar se já está suspenso
    if cliente.status_beneficios == models.StatusBeneficios.suspenso:
        raise HTTPException(
            status_code=400,
            detail=f"Cliente já está suspenso desde {cliente.data_suspensao}"
        )
    
    # Validar motivo
    if not motivo or len(motivo.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Motivo da suspensão deve ter pelo menos 10 caracteres"
        )
    
    # Suspender cliente
    cliente.status_beneficios = models.StatusBeneficios.suspenso
    cliente.motivo_suspensao = motivo.strip()
    cliente.data_suspensao = datetime.now()
    
    db.commit()
    db.refresh(cliente)
    
    return {
        "sucesso": True,
        "mensagem": "Cliente suspenso com sucesso",
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "status_beneficios": cliente.status_beneficios.value,
            "motivo_suspensao": cliente.motivo_suspensao,
            "data_suspensao": cliente.data_suspensao
        }
    }

@app.post("/api/admin/clientes/{cpf}/reativar")
def reativar_cliente(cpf: str, db: Session = Depends(get_db)):
    """
    Reativa um cliente suspenso
    
    Parâmetros:
    - cpf: CPF do cliente
    """
    # Buscar cliente
    cliente = db.query(models.Cliente).filter(models.Cliente.cpf == cpf).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Verificar se está suspenso
    if cliente.status_beneficios == models.StatusBeneficios.ativo:
        raise HTTPException(status_code=400, detail="Cliente já está ativo")
    
    if cliente.status_beneficios == models.StatusBeneficios.bloqueado:
        raise HTTPException(
            status_code=400,
            detail="Cliente bloqueado permanentemente. Não pode ser reativado."
        )
    
    # Reativar cliente
    cliente.status_beneficios = models.StatusBeneficios.ativo
    cliente.motivo_suspensao = None
    cliente.data_suspensao = None
    
    db.commit()
    db.refresh(cliente)
    
    return {
        "sucesso": True,
        "mensagem": "Cliente reativado com sucesso",
        "cliente": {
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "status_beneficios": cliente.status_beneficios.value
        }
    }

@app.get("/api/admin/clientes/suspensos")
def listar_clientes_suspensos(db: Session = Depends(get_db)):
    """
    Lista todos os clientes suspensos ou bloqueados
    """
    clientes_suspensos = db.query(models.Cliente).filter(
        models.Cliente.status_beneficios.in_([
            models.StatusBeneficios.suspenso,
            models.StatusBeneficios.bloqueado
        ])
    ).all()
    
    return {
        "total": len(clientes_suspensos),
        "clientes": [
            {
                "cpf": c.cpf,
                "nome": c.nome,
                "status_beneficios": c.status_beneficios.value,
                "motivo_suspensao": c.motivo_suspensao,
                "data_suspensao": c.data_suspensao,
                "data_cadastro": c.data_cadastro
            }
            for c in clientes_suspensos
        ]
    }

# ========== ENDPOINTS DE ALERTAS ==========

@app.get("/api/admin/alertas")
def listar_alertas(
    resolvido: bool = None,
    gravidade: str = None,
    tipo: str = None,
    db: Session = Depends(get_db)
):
    """
    Lista alertas com filtros opcionais
    
    Parâmetros:
    - resolvido: true/false (opcional)
    - gravidade: baixa/media/alta (opcional)
    - tipo: tipo do alerta (opcional)
    """
    query = db.query(models.Alerta)
    
    # Aplicar filtros
    if resolvido is not None:
        query = query.filter(models.Alerta.resolvido == resolvido)
    
    if gravidade:
        try:
            grav = models.GravidadeAlerta(gravidade)
            query = query.filter(models.Alerta.gravidade == grav)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Gravidade inválida. Use: baixa, media ou alta"
            )
    
    if tipo:
        try:
            tipo_enum = models.TipoAlerta(tipo)
            query = query.filter(models.Alerta.tipo == tipo_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Tipo inválido"
            )
    
    alertas = query.order_by(models.Alerta.data_deteccao.desc()).all()
    
    # Buscar informações do cliente para cada alerta
    alertas_data = []
    for alerta in alertas:
        cliente = db.query(models.Cliente).filter(
            models.Cliente.cpf == alerta.cliente_cpf
        ).first()
        
        alertas_data.append({
            "id": alerta.id,
            "tipo": alerta.tipo.value,
            "gravidade": alerta.gravidade.value,
            "cliente": {
                "cpf": alerta.cliente_cpf,
                "nome": cliente.nome if cliente else "Desconhecido"
            },
            "descricao": alerta.descricao,
            "data_deteccao": alerta.data_deteccao,
            "resolvido": alerta.resolvido,
            "observacao": alerta.observacao,
            "data_resolucao": alerta.data_resolucao
        })
    
    return {
        "total": len(alertas_data),
        "alertas": alertas_data
    }

@app.post("/api/admin/alertas/{alerta_id}/resolver")
def resolver_alerta(
    alerta_id: int,
    observacao: str,
    db: Session = Depends(get_db)
):
    """
    Marca um alerta como resolvido
    
    Parâmetros:
    - alerta_id: ID do alerta
    - observacao: Observação sobre a resolução
    """
    alerta = db.query(models.Alerta).filter(models.Alerta.id == alerta_id).first()
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    
    if alerta.resolvido:
        raise HTTPException(
            status_code=400,
            detail=f"Alerta já foi resolvido em {alerta.data_resolucao}"
        )
    
    if not observacao or len(observacao.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Observação deve ter pelo menos 10 caracteres"
        )
    
    # Marcar como resolvido
    alerta.resolvido = True
    alerta.observacao = observacao.strip()
    alerta.data_resolucao = datetime.now()
    
    db.commit()
    db.refresh(alerta)
    
    return {
        "sucesso": True,
        "mensagem": "Alerta marcado como resolvido",
        "alerta": {
            "id": alerta.id,
            "tipo": alerta.tipo.value,
            "resolvido": alerta.resolvido,
            "observacao": alerta.observacao,
            "data_resolucao": alerta.data_resolucao
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)