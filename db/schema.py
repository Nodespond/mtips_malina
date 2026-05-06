from db.connection import get_connection


def create_schema():
    """Создаёт все таблицы (вызывается при инициализации)"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # Свойства
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS properties (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('categorical', 'integer', 'real'))
    );
    """)

    # Возможные значения
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

    # Виды
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS varieties (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    );
    """)

    # Связь видов и свойств
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS variety_properties (
        variety_id INTEGER NOT NULL,
        property_id INTEGER NOT NULL,
        PRIMARY KEY (variety_id, property_id),
        FOREIGN KEY (variety_id) REFERENCES varieties(id) ON DELETE CASCADE,
        FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
    );
    """)

    # Значения для видов
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