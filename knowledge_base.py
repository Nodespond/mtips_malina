import sqlite3

from db.connection import get_connection
from models import Property

class KnowledgeBase:

    @staticmethod
    def get_all_varieties() -> list[str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM varieties ORDER BY name")
        return [row["name"] for row in cursor.fetchall()]

    @staticmethod
    def add_variety(name: str) -> bool:
        if not name or not name.strip():
            return False
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO varieties (name) VALUES (?)", (name.strip(),))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_variety(name: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM varieties WHERE name = ?", (name,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    @staticmethod
    def get_all_properties() -> list[Property]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type FROM properties ORDER BY name")
        return [Property(id=row["id"], name=row["name"], type=row["type"]) for row in cursor.fetchall()]

    @staticmethod
    def add_property(name: str, prop_type: str) -> bool:
        if not name or not name.strip():
            return False
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO properties (name, type) VALUES (?, ?)",
                         (name.strip(), prop_type))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_property(name: str) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM properties WHERE name = ?", (name,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted