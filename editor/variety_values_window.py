import tkinter as tk
from tkinter import ttk, messagebox
from db.connection import get_connection
from knowledge_base import KnowledgeBase

class VarietyValuesWindow:
    def __init__(self, parent, embedded=False, editor=None):
        self.embedded = embedded
        self.editor = editor
        if embedded:
            self.window = parent
        else:
            self.window = tk.Toplevel(parent)
            self.window.title("5. Значения для вида")
            self.window.geometry("850x650")

        self.current_variety = None
        self.current_property = None
        self.var_value = None
        self.min_entry = None
        self.max_entry = None

        self.create_widgets()
        self.load_varieties()

    def refresh_data(self):
        self.load_varieties()

    def create_widgets(self):
        tk.Label(self.window, text="Значения свойств для вида",
                 font=("Arial", 14, "bold")).pack(pady=10)

        top = tk.Frame(self.window)
        top.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(top, text="Вид плода малины:").pack(side=tk.LEFT, padx=5)
        self.variety_combo = ttk.Combobox(top, state="readonly", width=50)
        self.variety_combo.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.variety_combo.bind("<<ComboboxSelected>>", self.on_variety_selected)

        prop_frame = tk.Frame(self.window)
        prop_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(prop_frame, text="Свойство:").pack(side=tk.LEFT, padx=5)
        self.property_combo = ttk.Combobox(prop_frame, state="readonly", width=50)
        self.property_combo.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.property_combo.bind("<<ComboboxSelected>>", self.on_property_selected)

        self.edit_area = tk.LabelFrame(self.window, text="Значение свойства", padx=15, pady=15)
        self.edit_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.dynamic_frame = tk.Frame(self.edit_area)
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Сохранить значение", bg="#90ee90",
                  font=("Arial", 10, "bold"), command=self.save_value).pack()

    def load_varieties(self):
        varieties = KnowledgeBase.get_all_varieties()
        self.variety_combo['values'] = varieties
        if varieties:
            self.variety_combo.set(varieties[0])
            self.on_variety_selected(None)

    def on_variety_selected(self, event):
        self.current_variety = self.variety_combo.get()
        if not self.current_variety:
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.name 
            FROM variety_properties vp
            JOIN properties p ON vp.property_id = p.id
            WHERE vp.variety_id = (SELECT id FROM varieties WHERE name = ?)
            ORDER BY p.name
        """, (self.current_variety,))
        props = [row["name"] for row in cursor.fetchall()]
        conn.close()

        self.property_combo['values'] = props
        if props:
            self.property_combo.set(props[0])
            self.on_property_selected(None)

    def on_property_selected(self, event):
        self.current_property = self.property_combo.get()
        if not self.current_property or not self.current_variety:
            return

        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT type FROM properties WHERE name = ?", (self.current_property,))
        row = cursor.fetchone()
        prop_type = row["type"] if row else "categorical"

        if prop_type == "categorical":
            canvas = tk.Canvas(self.dynamic_frame)
            scrollbar = tk.Scrollbar(self.dynamic_frame, orient="vertical", command=canvas.yview)
            scroll_frame = tk.Frame(canvas)

            scroll_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            self.var_value = tk.StringVar()

            cursor.execute("""
                SELECT categorical_value 
                FROM possible_values 
                WHERE property_id = (SELECT id FROM properties WHERE name = ?)
            """, (self.current_property,))
            values = [r["categorical_value"] for r in cursor.fetchall()]

            for val in values:
                rb = tk.Radiobutton(scroll_frame, text=val, variable=self.var_value,
                                  value=val, font=("Arial", 10), anchor="w")
                rb.pack(anchor="w", pady=2, padx=10)

            cursor.execute("""
                SELECT categorical_value FROM variety_values 
                WHERE variety_id = (SELECT id FROM varieties WHERE name = ?)
                  AND property_id = (SELECT id FROM properties WHERE name = ?)
            """, (self.current_variety, self.current_property))
            current = cursor.fetchone()
            if current and current["categorical_value"]:
                self.var_value.set(current["categorical_value"])

        else:  # numeric
            tk.Label(self.dynamic_frame, text="Текущее значение:",
                    font=("Arial", 10, "bold")).pack(anchor="w", pady=5)

            cursor.execute("""
                SELECT min_value, max_value FROM variety_values 
                WHERE variety_id = (SELECT id FROM varieties WHERE name = ?)
                  AND property_id = (SELECT id FROM properties WHERE name = ?)
            """, (self.current_variety, self.current_property))
            curr = cursor.fetchone()

            if curr and curr["min_value"] is not None:
                tk.Label(self.dynamic_frame,
                        text=f"[{curr['min_value']} — {curr['max_value']}]",
                        fg="blue", font=("Arial", 10)).pack(anchor="w", pady=5)
            else:
                tk.Label(self.dynamic_frame, text="Не задано", fg="gray").pack(anchor="w", pady=5)

            tk.Label(self.dynamic_frame, text="Новое значение:",
                    font=("Arial", 10, "bold")).pack(anchor="w", pady=(15,5))

            sub = tk.Frame(self.dynamic_frame)
            sub.pack(anchor="w")
            tk.Label(sub, text="от").pack(side=tk.LEFT)
            self.min_entry = tk.Entry(sub, width=15)
            self.min_entry.pack(side=tk.LEFT, padx=5)

            tk.Label(sub, text="до").pack(side=tk.LEFT)
            self.max_entry = tk.Entry(sub, width=15)
            self.max_entry.pack(side=tk.LEFT, padx=5)

            if curr and curr["min_value"] is not None:
                self.min_entry.insert(0, str(curr["min_value"]))
                self.max_entry.insert(0, str(curr["max_value"]))

        conn.close()

    def save_value(self):
        if not self.current_variety or not self.current_property:
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM varieties WHERE name = ?", (self.current_variety,))
        variety_id = cursor.fetchone()["id"]

        cursor.execute("SELECT id, type FROM properties WHERE name = ?", (self.current_property,))
        prop = cursor.fetchone()
        prop_id = prop["id"]
        prop_type = prop["type"]

        try:
            if prop_type == "categorical":
                value = self.var_value.get() if self.var_value else None
                if not value:
                    messagebox.showwarning("Ошибка", "Выберите категориальное значение")
                    return
                cursor.execute("""
                    INSERT OR REPLACE INTO variety_values 
                    (variety_id, property_id, categorical_value, min_value, max_value)
                    VALUES (?, ?, ?, NULL, NULL)
                """, (variety_id, prop_id, value))
            else:
                if not self.min_entry or not self.max_entry:
                    return

                min_str = self.min_entry.get().strip()
                max_str = self.max_entry.get().strip()

                if not min_str or not max_str:
                    messagebox.showwarning("Ошибка", "Введите оба значения диапазона")
                    return

                try:
                    if prop_type == "integer":
                        min_v = int(min_str)
                        max_v = int(max_str)
                    else:  # real
                        min_v = float(min_str)
                        max_v = float(max_str)
                except ValueError:
                    if prop_type == "integer":
                        messagebox.showwarning("Ошибка", "Введите целые числа")
                    else:
                        messagebox.showwarning("Ошибка", "Введите числа (можно дробные)")
                    return

                if min_v > max_v:
                    messagebox.showwarning("Ошибка", "Минимум не может быть больше максимума")
                    return

                cursor.execute("""
                                    INSERT OR REPLACE INTO variety_values
                                    (variety_id, property_id, categorical_value, min_value, max_value)
                                    VALUES (?, ?, NULL, ?, ?)
                                """, (variety_id, prop_id, min_v, max_v))

            conn.commit()
            self.on_property_selected(None)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить значение: {e}")
        finally:
            conn.close()