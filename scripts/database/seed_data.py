# scripts/seed_data.py
import sys
import os

# Adicionar pasta backend ao path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import SessionLocal, init_db
from models import Cliente, Sacola
from datetime import datetime, timedelta
import random

def limpar_banco():
    """Remove todos os dados do banco"""
    db = SessionLocal()
    db.query(Sacola).delete()
    db.query(Cliente).delete()
    db.commit()
    db.close()
    print("Banco limpo!")

def criar_clientes_teste():
    """Cria clientes de teste"""
    db = SessionLocal()
    
    clientes = [
        {"cpf": "123.456.789-00", "nome": "João Silva"},
        {"cpf": "987.654.321-00", "nome": "Maria Santos"},
        {"cpf": "456.789.123-00", "nome": "Pedro Costa"},
        {"cpf": "321.654.987-00", "nome": "Ana Oliveira"},
        {"cpf": "789.123.456-00", "nome": "Carlos Ferreira"},
    ]
    
    for c in clientes:
        cliente = Cliente(**c)
        db.add(cliente)
    
    db.commit()
    db.close()
    print(f"{len(clientes)} clientes criados!")
    return clientes

def criar_sacolas_teste(clientes):
    """Cria sacolas de teste com diferentes estados"""
    db = SessionLocal()
    
    sacola_id = 1
    total_sacolas = 0
    
    for cliente in clientes:
        # Cada cliente tem de 2 a 4 sacolas
        num_sacolas = random.randint(2, 4)
        
        for _ in range(num_sacolas):
            # Gerar ID da sacola
            id_sacola = f"BAG-{sacola_id:05d}"
            
            # Idade variada (5 a 80 dias)
            dias_atras = random.randint(5, 80)
            data_compra = datetime.now() - timedelta(days=dias_atras)
            
            # Utilizações baseadas na idade
            if dias_atras < 30:
                utilizacoes = random.randint(0, 15)  # Sacola nova
            elif dias_atras < 60:
                utilizacoes = random.randint(10, 25)  # Sacola média
            else:
                utilizacoes = random.randint(20, 38)  # Sacola antiga
            
            # Última utilização (0-7 dias atrás)
            ultima_utilizacao = datetime.now() - timedelta(days=random.randint(0, 7))
            
            sacola = Sacola(
                id=id_sacola,
                cpf_cliente=cliente["cpf"],
                data_compra=data_compra,
                utilizacoes=utilizacoes,
                dias_de_uso=dias_atras,
                ultima_utilizacao=ultima_utilizacao,
                status="ativo"
            )
            
            db.add(sacola)
            sacola_id += 1
            total_sacolas += 1
    
    db.commit()
    db.close()
    print(f"{total_sacolas} sacolas criadas!")

def mostrar_resumo():
    """Mostra resumo dos dados criados"""
    db = SessionLocal()
    
    print("\n" + "="*50)
    print("RESUMO DOS DADOS DE TESTE")
    print("="*50)
    
    clientes = db.query(Cliente).all()
    print(f"\nClientes: {len(clientes)}")
    for cliente in clientes:
        sacolas = db.query(Sacola).filter(Sacola.cpf_cliente == cliente.cpf).all()
        print(f"   • {cliente.nome} ({cliente.cpf}) - {len(sacolas)} sacolas")
    
    print(f"\nSacolas por Estado:")
    
    # Sacolas novas (0-15 usos)
    novas = db.query(Sacola).filter(Sacola.utilizacoes <= 15).count()
    print(f"   🟢 Novas (0-15 usos): {novas}")
    
    # Sacolas médias (16-25 usos)
    medias = db.query(Sacola).filter(
        Sacola.utilizacoes > 15, 
        Sacola.utilizacoes <= 25
    ).count()
    print(f"   🟡 Médias (16-25 usos): {medias}")
    
    # Sacolas antigas (26+ usos)
    antigas = db.query(Sacola).filter(Sacola.utilizacoes > 25).count()
    print(f"   🔴 Antigas (26+ usos): {antigas}")
    
    print("\n" + "="*50)
    print("Dados de teste prontos para usar!")
    print("="*50 + "\n")
    
    db.close()

def main():
    print("\nPopulando banco de dados com dados de teste...\n")
    
    # Inicializar banco
    init_db()
    
    # Limpar dados antigos
    limpar_banco()
    
    # Criar dados novos
    clientes = criar_clientes_teste()
    criar_sacolas_teste(clientes)
    
    # Mostrar resumo
    mostrar_resumo()

if __name__ == "__main__":
    main()