# backend/test_db.py
from database import init_db, SessionLocal
from models import Cliente, Sacola

print("Criando banco de dados...")
init_db()

print("Testando inserção de dados...")

# Criar sessão
db = SessionLocal()

# Criar cliente teste
cliente = Cliente(
    cpf="123.456.789-00",
    nome="João Silva Teste"
)
db.add(cliente)
db.commit()
print(f" Cliente criado: {cliente.nome}")

# Criar sacola teste
sacola = Sacola(
    id="BAG-00001",
    cpf_cliente="123.456.789-00",
    utilizacoes=0
)
db.add(sacola)
db.commit()
print(f" Sacola criada: {sacola.id}")

# Buscar dados
cliente_busca = db.query(Cliente).first()
print(f" Cliente no banco: {cliente_busca.nome} - {cliente_busca.cpf}")

sacola_busca = db.query(Sacola).first()
print(f" Sacola no banco: {sacola_busca.id} - {sacola_busca.utilizacoes} usos")

db.close()

print("\n Banco de dados funcionando perfeitamente!")