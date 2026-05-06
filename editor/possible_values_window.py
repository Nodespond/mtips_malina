import tkinter as tk
from tkinter import ttk
from knowledge_base import KnowledgeBase
from db.connection import get_connection

class PossibleValuesWindow:
    def __init__(self, parent, embedded=False):
        self.embedded = embedded
        if embedded:
            self.window = parent
        else:
            self.window = tk.Toplevel(parent)
            self.window.title("Возможные значения свойств")
            self.window.geometry("750x550")

        self.current_property = None
        self.create_widgets()
        self.load_properties()

    def create_widgets(self):
        tk.Label(self.window, text="Возможные значения свойств",
                 font=("Arial", 14, "bold")).pack(pady=10)

        # Выбор свойства
        top_frame = tk.Frame(self.window)
        top_frame.pack(fill=tk.X, padx=20, pady=8)

        tk.Label(top_frame, text="Свойство:").pack(side=tk.LEFT)
        self.prop_combo = ttk.Combobox(top_frame, state="readonly", width=50)
        self.prop_combo.pack(side=tk.LEFT, padx=10)
        self.prop_combo.bind("<<ComboboxSelected>>", self.on_property_selected)

        # Скроллируемая область значений
        container = tk.Frame(self.window)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Панель добавления
        add_frame = tk.LabelFrame(self.window, text="Добавить / Изменить значение", padx=15, pady=10)
        add_frame.pack(fill=tk.X, padx=20, pady=10)

        self.cat_frame = tk.Frame(add_frame)
        tk.Label(self.cat_frame, text="Значение:").pack(side=tk.LEFT)
        self.cat_entry = tk.Entry(self.cat_frame, width=40)
        self.cat_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(self.cat_frame, text="Добавить", command=self.add_value).pack(side=tk.LEFT, padx=10)

        self.num_frame = tk.Frame(add_frame)
        tk.Label(self.num_frame, text="от").pack(side=tk.LEFT)
        self.min_entry = tk.Entry(self.num_frame, width=12)
        self.min_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(self.num_frame, text="до").pack(side=tk.LEFT)
        self.max_entry = tk.Entry(self.num_frame, width=12)
        self.max_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(self.num_frame, text="Установить диапазон", command=self.add_value).pack(side=tk.LEFT, padx=10)

        self.cat_frame.pack(fill=tk.X, pady=5)
        self.num_frame.pack_forget()

    def load_properties(self):
        props = KnowledgeBase.get_all_properties()
        prop_names = [p.name for p in props]
        self.prop_combo['values'] = prop_names
        if prop_names:
            self.prop_combo.set(prop_names[0])
            self.on_property_selected(None)

    def on_property_selected(self, event):
        prop_name = self.prop_combo.get()
        if not prop_name:
            return

        self.current_property = prop_name

        # Очистка предыдущих элементов
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.type, pv.categorical_value, pv.min_value, pv.max_value, pv.id
            FROM properties p
            LEFT JOIN possible_values pv ON p.id = pv.property_id
            WHERE p.name = ?
            ORDER BY pv.categorical_value, pv.min_value
        """, (prop_name,))
        rows = cursor.fetchall()
        conn.close()

        prop_type = rows[0]["type"] if rows else "categorical"

        for row in rows:
            if not row["categorical_value"] and row["min_value"] is None:
                continue

            val_frame = tk.Frame(self.scrollable_frame)
            val_frame.pack(fill=tk.X, pady=2, padx=5)

            if row["categorical_value"]:
                value_text = row["categorical_value"]
            else:
                value_text = f"[{row['min_value']} — {row['max_value']}]"

            label = tk.Label(val_frame, text=value_text, font=("Arial", 10), anchor="w")
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            delete_btn = tk.Button(val_frame, text="✕", fg="white", bg="#d32f2f",
                                 width=3, font=("Arial", 9, "bold"),
                                 command=lambda rid=row["id"]: self.delete_value(rid))
            delete_btn.pack(side=tk.RIGHT, padx=5)

        # Переключение панели добавления
        if prop_type == "categorical":
            self.cat_frame.pack(fill=tk.X, pady=5)
            self.num_frame.pack_forget()
        else:
            self.cat_frame.pack_forget()
            self.num_frame.pack(fill=tk.X, pady=5)

    def add_value(self):
        if not self.current_property:
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, type FROM properties WHERE name = ?", (self.current_property,))
        prop = cursor.fetchone()
        if not prop:
            conn.close()
            return

        prop_id = prop["id"]
        prop_type = prop["type"]

        try:
            if prop_type == "categorical":
                val = self.cat_entry.get().strip()
                if not val:
                    return

                # Проверка на дубликат
                cursor.execute("""
                    SELECT 1 FROM possible_values 
                    WHERE property_id = ? AND categorical_value = ?
                """, (prop_id, val))
                if cursor.fetchone():
                    self.cat_entry.delete(0, tk.END)
                    return  # уже существует — ничего не делаем

                cursor.execute("""
                    INSERT OR IGNORE INTO possible_values (property_id, categorical_value)
                    VALUES (?, ?)
                """, (prop_id, val))
                self.cat_entry.delete(0, tk.END)

            else:  # numeric
                min_v = float(self.min_entry.get().strip())
                max_v = float(self.max_entry.get().strip())
                if min_v > max_v:
                    return

                # Удаляем старый диапазон (чтобы был только один)
                cursor.execute("DELETE FROM possible_values WHERE property_id = ? AND min_value IS NOT NULL", (prop_id,))

                cursor.execute("""
                    INSERT INTO possible_values (property_id, min_value, max_value)
                    VALUES (?, ?, ?)
                """, (prop_id, min_v, max_v))

                self.min_entry.delete(0, tk.END)
                self.max_entry.delete(0, tk.END)

            conn.commit()
            self.on_property_selected(None)  # автообновление списка

        except:
            pass
        finally:
            conn.close()

    def delete_value(self, value_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM possible_values WHERE id = ?", (value_id,))
        conn.commit()
        conn.close()
        self.on_property_selected(None)