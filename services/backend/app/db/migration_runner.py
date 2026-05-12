"""
Migration Runner - Executa migrations SQL em ordem com controle de versão
"""
import sqlite3
from pathlib import Path
from datetime import datetime


def run_migrations(db_path: str):
    """
    Executa apenas migrations ainda não aplicadas, registrando
    cada execução na tabela _migrations.

    Args:
        db_path: Caminho para o arquivo .db
    """
    migrations_dir = Path(__file__).parent / "migrations"

    if not migrations_dir.exists():
        print(f"Pasta migrations não encontrada: {migrations_dir}")
        return

    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("Nenhuma migration encontrada!")
        return

    conn = sqlite3.connect(db_path)

    try:
        # Criar tabela de controle se não existir
        conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                aplicada_em TEXT NOT NULL
            )
        """)
        conn.commit()

        # Buscar migrations já aplicadas
        aplicadas = {
            row[0]
            for row in conn.execute("SELECT nome FROM _migrations").fetchall()
        }

        pendentes = [f for f in migration_files if f.name not in aplicadas]

        if not pendentes:
            print(f"Banco atualizado. Nenhuma migration pendente.")
            return

        print(f"Database: {db_path}")
        print(f"Migrations já aplicadas: {len(aplicadas)}")
        print(f"Migrations pendentes: {len(pendentes)}\n")

        for migration_file in pendentes:
            print(f"Rodando {migration_file.name}...", end=" ")

            with open(migration_file, encoding='utf-8') as f:
                sql_script = f.read()

            conn.executescript(sql_script)

            conn.execute(
                "INSERT INTO _migrations (nome, aplicada_em) VALUES (?, ?)",
                (migration_file.name, datetime.now().isoformat())
            )
            conn.commit()
            print("✅")

        print(f"\n{len(pendentes)} migration(s) aplicada(s) com sucesso!")

    except Exception as e:
        conn.rollback()
        print(f"\nErro ao executar migration: {e}")
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations("data/bagplus.db")