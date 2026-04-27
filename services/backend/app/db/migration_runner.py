"""
Migration Runner - Executa migrations SQL em ordem
"""
import sqlite3
from pathlib import Path


def run_migrations(db_path: str):
    """
    Executa todas migrations SQL em ordem numérica
    
    Args:
        db_path: Caminho para o arquivo .db
    """
    migrations_dir = Path(__file__).parent / "migrations"
    
    if not migrations_dir.exists():
        print(f"Pasta migrations não encontrada: {migrations_dir}")
        return
    
    # Buscar todos arquivos .sql em ordem
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("Nenhuma migration encontrada!")
        return
    
    print(f"Executando {len(migration_files)} migrations...")
    print(f"Database: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    
    try:
        for migration_file in migration_files:
            print(f"Rodando {migration_file.name}...", end=" ")
            
            with open(migration_file, encoding='utf-8') as f:
                sql_script = f.read()
            
            conn.executescript(sql_script)
            print("✅")
        
        conn.commit()
        print(f"\nTodas migrations executadas com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"\nErro ao executar migration: {e}")
        raise
    
    finally:
        conn.close()


if __name__ == "__main__":
    # Rodar migrations no banco local
    run_migrations("data/bagplus.db")