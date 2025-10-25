"""
Script de migração para tornar o campo 'brand' da tabela 'cars' nullable.
"""
import sqlite3
import os

# Caminho para o banco de dados
DB_PATH = "mech_ai.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("🔄 Iniciando migração...")
        
        # SQLite não suporta ALTER COLUMN diretamente, então precisamos:
        # 1. Criar nova tabela com a estrutura correta
        # 2. Copiar dados
        # 3. Deletar tabela antiga
        # 4. Renomear nova tabela
        
        # Criar tabela temporária com brand nullable
        cursor.execute("""
            CREATE TABLE cars_new (
                id INTEGER PRIMARY KEY,
                brand VARCHAR(100),
                model VARCHAR(100) NOT NULL,
                color VARCHAR(50),
                year INTEGER,
                client_id INTEGER NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(client_id) REFERENCES clients(id)
            )
        """)
        print("✅ Tabela temporária criada")
        
        # Copiar dados da tabela antiga para a nova
        cursor.execute("""
            INSERT INTO cars_new (id, brand, model, color, year, client_id, created_at, updated_at)
            SELECT id, brand, model, color, year, client_id, created_at, updated_at
            FROM cars
        """)
        print("✅ Dados copiados")
        
        # Deletar tabela antiga
        cursor.execute("DROP TABLE cars")
        print("✅ Tabela antiga removida")
        
        # Renomear tabela nova
        cursor.execute("ALTER TABLE cars_new RENAME TO cars")
        print("✅ Tabela renomeada")
        
        # Commit das mudanças
        conn.commit()
        print("✅ Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
