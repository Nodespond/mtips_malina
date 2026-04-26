import sqlite3
from pathlib import Path

DB_PATH = Path("database.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # чтобы возвращались словари
    return conn


def init_db():
    """Создаёт таблицы, если их нет"""
    conn = get_connection()
    cursor = conn.cursor()

    # Включаем поддержку внешних ключей
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Таблица свойств
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('categorical', 'integer', 'real'))
    );
    """)

    # Таблица возможных значений свойств
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS possible_values (
        id INTEGER PRIMARY KEY,
        property_id INTEGER NOT NULL,
        categorical_value TEXT,
        min_value REAL,
        max_value REAL,
        FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
        CHECK (
            (categorical_value IS NOT NULL AND min_value IS NULL AND max_value IS NULL) OR
            (categorical_value IS NULL AND min_value IS NOT NULL AND max_value IS NOT NULL)
        )
    );
    """)

    # Таблица видов малины
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS varieties (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # Связь "какие свойства используются для вида"
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS variety_properties (
        variety_id INTEGER NOT NULL,
        property_id INTEGER NOT NULL,
        PRIMARY KEY (variety_id, property_id),
        FOREIGN KEY (variety_id) REFERENCES varieties(id) ON DELETE CASCADE,
        FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
    );
    """)

    # Конкретные значения/интервалы для каждого вида и свойства
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS variety_values (
        variety_id INTEGER NOT NULL,
        property_id INTEGER NOT NULL,
        categorical_value TEXT,
        min_value REAL,
        max_value REAL,
        PRIMARY KEY (variety_id, property_id),
        FOREIGN KEY (variety_id) REFERENCES varieties(id) ON DELETE CASCADE,
        FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
        CHECK (
            (categorical_value IS NOT NULL AND min_value IS NULL AND max_value IS NULL) OR
            (categorical_value IS NULL AND min_value IS NOT NULL AND max_value IS NOT NULL)
        )
    );
    """)

    conn.commit()
    conn.close()
    print("База данных инициализирована.")