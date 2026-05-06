import tkinter as tk
from tkinter import ttk
from knowledge_base import KnowledgeBase

class PropertiesWindow:
    def __init__(self, parent, embedded=False):
        self.embedded = embedded
        if embedded:
            self.window = parent
        else:
            self.window = tk.Toplevel(parent)
            self.window.title("Свойства")
            self.window.geometry("600x500")

        self.create_widgets()
        self.load_properties()

    def create_widgets(self):
        tk.Label(self.window, text="Свойства",
                 font=("Arial", 14, "bold")).pack(pady=10)

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

        add_frame = tk.Frame(self.window)
        add_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(add_frame, text="Название:").pack(side=tk.LEFT)
        self.name_entry = tk.Entry(add_frame, width=30)
        self.name_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(add_frame, text="Тип:").pack(side=tk.LEFT, padx=5)
        self.type_var = tk.StringVar(value="categorical")
        ttk.Combobox(add_frame, textvariable=self.type_var,
                     values=["categorical", "integer", "real"], width=12).pack(side=tk.LEFT, padx=5)

        tk.Button(add_frame, text="Добавить", command=self.add_property).pack(side=tk.LEFT, padx=10)

    def load_properties(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        props = KnowledgeBase.get_all_properties()

        for p in props:
            row = tk.Frame(self.scrollable_frame)
            row.pack(fill=tk.X, pady=2, padx=5)

            label = tk.Label(row, text=p.name, font=("Arial", 10), anchor="w")
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            delete_btn = tk.Button(row, text="✕", fg="white", bg="#d32f2f",
                                 width=3, font=("Arial", 9, "bold"),
                                 command=lambda prop=p.name: self.delete_property(prop))
            delete_btn.pack(side=tk.RIGHT, padx=5)

    def add_property(self):
        name = self.name_entry.get().strip()
        prop_type = self.type_var.get()

        if not name:
            return

        if KnowledgeBase.add_property(name, prop_type):
            self.name_entry.delete(0, tk.END)
            self.load_properties()

    def delete_property(self, name):
        if KnowledgeBase.delete_property(name):
            self.load_properties()