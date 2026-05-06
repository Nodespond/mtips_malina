import tkinter as tk
from knowledge_base import KnowledgeBase


class VarietiesWindow:
    def __init__(self, parent, embedded=False):
        self.embedded = embedded
        if embedded:
            self.window = parent
        else:
            self.window = tk.Toplevel(parent)
            self.window.title("Виды плодов малины")
            self.window.geometry("600x500")

        self.create_widgets()
        self.load_varieties()

    def create_widgets(self):
        tk.Label(self.window, text="Виды плодов малины",
                 font=("Arial", 14, "bold")).pack(pady=10)

        # Контейнер со скроллом
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
        add_frame = tk.Frame(self.window)
        add_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(add_frame, text="Новый вид:").pack(side=tk.LEFT)
        self.new_var_entry = tk.Entry(add_frame, width=40)
        self.new_var_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        tk.Button(add_frame, text="Добавить", command=self.add_variety).pack(side=tk.LEFT, padx=5)

    def load_varieties(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        varieties = KnowledgeBase.get_all_varieties()

        for variety in varieties:
            row = tk.Frame(self.scrollable_frame)
            row.pack(fill=tk.X, pady=2, padx=5)

            label = tk.Label(row, text=variety, font=("Arial", 10), anchor="w")
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            delete_btn = tk.Button(row, text="✕", fg="white", bg="#d32f2f",
                                   width=3, font=("Arial", 9, "bold"),
                                   command=lambda v=variety: self.delete_variety(v))
            delete_btn.pack(side=tk.RIGHT, padx=5)

    def add_variety(self):
        name = self.new_var_entry.get().strip()
        if not name:
            return

        if KnowledgeBase.add_variety(name):
            self.new_var_entry.delete(0, tk.END)
            self.load_varieties()  # автообновление

    def delete_variety(self, name):
        if KnowledgeBase.delete_variety(name):
            self.load_varieties()  # автообновление