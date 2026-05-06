import tkinter as tk
from tkinter import ttk, messagebox
from db.connection import get_connection
from solver import Solver
from result_window import ResultWindow, KnowledgeBaseViewer   # если KnowledgeBaseViewer в result_window.py

class InputSystemWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Решатель задач - Классификация вида малины")
        self.window.geometry("1050x720")

        self.input_data = {}      # {property_name: value}
        self.property_widgets = {}

        self.create_widgets()
        self.load_properties()

    def create_widgets(self):
        tk.Label(self.window, text="Введите характеристики плода малины",
                 font=("Arial", 16, "bold")).pack(pady=15)

        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Левая колонка — ввод
        left_frame = tk.LabelFrame(main_frame, text="Характеристики плода", padx=15, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(left_frame)
        scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Правая колонка — сводка
        right_frame = tk.LabelFrame(main_frame, text="Выбранные характеристики", padx=15, pady=10, width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(20, 0))
        right_frame.pack_propagate(False)

        self.summary_text = tk.Text(right_frame, wrap=tk.WORD, font=("Arial", 10), height=32, state="disabled")
        summary_scroll = tk.Scrollbar(right_frame, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=summary_scroll.set)

        self.summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Кнопки внизу
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="Просмотреть базу знаний",
                  command=self.show_knowledge_base).pack(side=tk.LEFT, padx=8)

        tk.Button(btn_frame, text="Очистить все", width=15,
                  command=self.clear_all).pack(side=tk.LEFT, padx=8)

        tk.Button(btn_frame, text="Определить вид плода малины",
                  font=("Arial", 11, "bold"), bg="#4CAF50", fg="white",
                  height=2, command=self.determine_variety).pack(side=tk.LEFT, padx=8)

    def load_properties(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, type FROM properties ORDER BY name")
        properties = cursor.fetchall()
        conn.close()

        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.property_widgets.clear()

        for prop_name, prop_type in properties:
            row = tk.Frame(self.scroll_frame)
            row.pack(fill=tk.X, pady=6, padx=5)

            tk.Label(row, text=prop_name + ":", width=28, anchor="w").pack(side=tk.LEFT)

            if prop_type == "categorical":
                conn = get_connection()
                c = conn.cursor()
                c.execute("""
                    SELECT categorical_value FROM possible_values 
                    WHERE property_id = (SELECT id FROM properties WHERE name = ?)
                """, (prop_name,))
                vals = [r[0] for r in c.fetchall()]
                conn.close()

                combo = ttk.Combobox(row, values=vals, state="readonly", width=35)
                combo.pack(side=tk.LEFT, padx=10)
                combo.bind("<<ComboboxSelected>>",
                          lambda e, pn=prop_name, w=combo: self.on_value_changed(pn, w.get()))

                self.property_widgets[prop_name] = ("categorical", combo)

            else:  # numeric → ОДНО значение
                entry = tk.Entry(row, width=20)
                entry.pack(side=tk.LEFT, padx=10)
                entry.bind("<KeyRelease>",
                          lambda e, pn=prop_name, w=entry: self.on_value_changed(pn, w.get()))

                self.property_widgets[prop_name] = ("numeric", entry)

    def on_value_changed(self, prop_name, value=None):
        if not value or value.strip() == "":
            self.input_data.pop(prop_name, None)
        else:
            self.input_data[prop_name] = value.strip()

        self.update_summary()

    def update_summary(self):
        self.summary_text.config(state="normal")
        self.summary_text.delete(1.0, tk.END)

        if not self.input_data:
            self.summary_text.insert(tk.END, "Пока не задано ни одной характеристики...")
        else:
            self.summary_text.insert(tk.END, "Выбранные характеристики:\n\n")
            for prop, val in sorted(self.input_data.items()):
                self.summary_text.insert(tk.END, f"• {prop}: {val}\n")

        self.summary_text.config(state="disabled")

    def clear_all(self):
        self.input_data.clear()
        for ptype, *widgets in self.property_widgets.values():
            if ptype == "categorical":
                widgets[0].set('')
            else:
                widgets[0].delete(0, tk.END)
        self.update_summary()

    def show_knowledge_base(self):
        KnowledgeBaseViewer(self.window)

    def determine_variety(self):
        if not self.input_data:
            messagebox.showwarning("Внимание", "Задайте хотя бы одну характеристику")
            return

        suitable, rejections = Solver.classify_instance(self.input_data)
        # === ДЛЯ ДИАГНОСТИКИ ===
        print("=== DEBUG REJECTIONS ===")
        import pprint
        pprint.pprint(rejections)
        # =======================
        ResultWindow(self.window, suitable, rejections, self.input_data)