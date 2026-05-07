import tkinter as tk
from tkinter import ttk, messagebox
from knowledge_base import KnowledgeBase
from db.connection import get_connection

class VarietyPropertiesWindow:
    def __init__(self, parent, embedded=False, editor=None):
        self.embedded = embedded
        self.editor = editor
        if embedded:
            self.window = parent
        else:
            self.window = tk.Toplevel(parent)
            self.window.title("4. Описание свойств вида")
            self.window.geometry("750x550")

        self.create_widgets()
        self.load_data()

    def refresh_data(self):
        self.load_data()

    def create_widgets(self):
        tk.Label(self.window, text="Описание свойств вида",
                 font=("Arial", 14, "bold")).pack(pady=10)

        top_frame = tk.Frame(self.window)
        top_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(top_frame, text="Вид плода малины:").pack(side=tk.LEFT)
        self.variety_combo = ttk.Combobox(top_frame, state="readonly", width=60)
        self.variety_combo.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.variety_combo.bind("<<ComboboxSelected>>", self.on_variety_selected)

        frame = tk.Frame(self.window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(frame, text="Все доступные свойства:").grid(row=0, column=0, sticky="w")
        tk.Label(frame, text="Используемые свойства для выбранного вида:").grid(row=0, column=2, sticky="w")

        self.all_props_list = tk.Listbox(frame, height=12, selectmode=tk.MULTIPLE, width=35)
        self.all_props_list.grid(row=1, column=0, padx=5, sticky="nswe")

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=1, column=1, padx=15)
        tk.Button(btn_frame, text="→ Добавить", width=12, command=self.add_to_used).pack(pady=10)
        tk.Button(btn_frame, text="← Убрать", width=12, command=self.remove_from_used).pack(pady=10)

        self.used_props_list = tk.Listbox(frame, height=12, width=35)
        self.used_props_list.grid(row=1, column=2, padx=5, sticky="nswe")

        if not self.embedded:
            tk.Button(self.window, text="Закрыть", command=self.window.destroy).pack(pady=10)

    def load_data(self):
        varieties = KnowledgeBase.get_all_varieties()
        self.variety_combo['values'] = varieties
        if varieties:
            self.variety_combo.set(varieties[0])
            self.on_variety_selected(None)

        self.all_props_list.delete(0, tk.END)
        for p in KnowledgeBase.get_all_properties():
            self.all_props_list.insert(tk.END, p.name)

    def on_variety_selected(self, event):
        variety_name = self.variety_combo.get()
        if not variety_name:
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.name 
            FROM variety_properties vp
            JOIN properties p ON vp.property_id = p.id
            WHERE vp.variety_id = (SELECT id FROM varieties WHERE name = ?)
        """, (variety_name,))
        used = [row["name"] for row in cursor.fetchall()]
        conn.close()

        self.used_props_list.delete(0, tk.END)
        for prop in used:
            self.used_props_list.insert(tk.END, prop)

    def add_to_used(self):
        variety_name = self.variety_combo.get()
        if not variety_name:
            messagebox.showwarning("Ошибка", "Выберите вид")
            return

        selected = [self.all_props_list.get(i) for i in self.all_props_list.curselection()]
        if not selected:
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM varieties WHERE name = ?", (variety_name,))
        variety_id = cursor.fetchone()["id"]

        for prop_name in selected:
            cursor.execute("SELECT id FROM properties WHERE name = ?", (prop_name,))
            row = cursor.fetchone()
            if row:
                prop_id = row["id"]
                cursor.execute("INSERT OR IGNORE INTO variety_properties (variety_id, property_id) VALUES (?, ?)",
                             (variety_id, prop_id))

        conn.commit()
        conn.close()
        self.on_variety_selected(None)
        messagebox.showinfo("Успех", f"Добавлено свойств: {len(selected)}")

    def remove_from_used(self):
        variety_name = self.variety_combo.get()
        if not variety_name:
            return

        selected = [self.used_props_list.get(i) for i in self.used_props_list.curselection()]
        if not selected:
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM varieties WHERE name = ?", (variety_name,))
        variety_id = cursor.fetchone()["id"]

        for prop_name in selected:
            cursor.execute("SELECT id FROM properties WHERE name = ?", (prop_name,))
            row = cursor.fetchone()
            if row:
                prop_id = row["id"]
                cursor.execute("DELETE FROM variety_properties WHERE variety_id = ? AND property_id = ?",
                             (variety_id, prop_id))

        conn.commit()
        conn.close()
        self.on_variety_selected(None)