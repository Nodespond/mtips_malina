import sqlite3
from pathlib import Path

DB_PATH = Path("database.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    from db.schema import create_schema
    create_schema()
    print("Схема базы данных создана.")