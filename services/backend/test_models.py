"""
Teste rápido: Models vs Database
Verifica se models estão alinhados com schema
"""
from app.db.models import Base, Entidade, Unidade, Usuario, Cliente, Sacola
from app.db.session import engine
from sqlalchemy.orm import Session

print("🔍 Testando Models vs Database...\n")

try:
    # 1. Criar tabelas (se não existirem)
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas/verificadas")
    
    # 2. Criar sessão
    db = Session(engine)
    
    # 3. Criar entidade de teste
    zaffari = Entidade(
        nome_comercial="Zaffari Teste",
        cnpj="12.345.678/0001-90",
        meta_desconto_percentual=5.0,
        meta_desconto_quantidade_usos=10
    )
    db.add(zaffari)
    db.commit()
    print("✅ Entidade criada")
    
    # 4. Criar unidade de teste
    iguatemi = Unidade(
        entidade_id=zaffari.id,
        nome="Iguatemi Teste",
        endereco="Av. João Wallig, 1800",
        cidade="Porto Alegre",
        estado="RS"
    )
    db.add(iguatemi)
    db.commit()
    print("✅ Unidade criada")
    
    # 5. Criar usuário admin (global)
    admin = Usuario(
        username="admin_teste",
        password_hash="hash_temporario",
        nome="Admin Teste",
        role="admin",
        entidade_id=None,  # NULL = admin global
        unidade_id=None
    )
    db.add(admin)
    db.commit()
    print("✅ Admin criado (entidade_id=NULL)")
    
    # 6. Criar usuário gerente (vinculado)
    gerente = Usuario(
        username="gerente_teste",
        password_hash="hash_temporario",
        nome="Gerente Teste",
        role="gerente",
        entidade_id=zaffari.id,
        unidade_id=iguatemi.id
    )
    db.add(gerente)
    db.commit()
    print("✅ Gerente criado (vinculado a unidade)")
    
    # 7. Verificar relationships
    print(f"\n🔗 Testando Relationships:")
    print(f"   Zaffari tem {len(zaffari.unidades)} unidade(s)")
    print(f"   Iguatemi pertence a: {iguatemi.entidade.nome_comercial}")
    print(f"   Zaffari tem {len(zaffari.usuarios)} usuário(s)")
    
    # 8. Buscar dados
    print(f"\n📊 Dados criados:")
    print(f"   Entidade: {zaffari.nome_comercial} (ID: {zaffari.id})")
    print(f"   Unidade: {iguatemi.nome} (ID: {iguatemi.id})")
    print(f"   Admin: {admin.username} (entidade_id={admin.entidade_id})")
    print(f"   Gerente: {gerente.username} (entidade_id={gerente.entidade_id}, unidade_id={gerente.unidade_id})")
    
    print("\n🎉 TESTE COMPLETO! Models e Database alinhados!\n")
    
    db.close()
    
except Exception as e:
    print(f"\n❌ ERRO: {e}\n")
    import traceback
    traceback.print_exc()