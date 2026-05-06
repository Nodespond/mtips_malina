import tkinter as tk
from db.connection import get_connection

class ValidationWindow:
    def __init__(self, parent, embedded=False):
        self.embedded = embedded
        if embedded:
            self.window = parent
        else:
            self.window = tk.Toplevel(parent)
            self.window.title("6. Проверка полноты знаний")
            self.window.geometry("800x550")

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.window, text="Проверка полноты базы знаний",
                 font=("Arial", 14, "bold")).pack(pady=20)

        self.check_button = tk.Button(self.window, text="Проверить полноту знаний",
                                    font=("Arial", 11, "bold"), bg="#4CAF50", fg="white",
                                    height=2, width=30, command=self.run_check)
        self.check_button.pack(pady=20)

        self.result_frame = tk.Frame(self.window)
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.result_text = tk.Text(self.result_frame, wrap=tk.WORD, font=("Consolas", 10),
                                 height=20, state="disabled")
        scrollbar = tk.Scrollbar(self.result_frame, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar.set)

        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.result_frame.pack_forget()

    def run_check(self):
        self.result_frame.pack(fill=tk.BOTH, expand=True)
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)

        conn = get_connection()
        cursor = conn.cursor()

        report = ["Результат проверки:\n\n"]

        cursor.execute("""
            SELECT v.name as variety_name, p.name as prop_name
            FROM variety_properties vp
            JOIN varieties v ON vp.variety_id = v.id
            JOIN properties p ON vp.property_id = p.id
            LEFT JOIN variety_values vv ON vv.variety_id = v.id 
                                      AND vv.property_id = p.id
            WHERE vv.variety_id IS NULL
            ORDER BY v.name, p.name
        """)
        missing = cursor.fetchall()

        if not missing:
            report.append("- Все виды имеют описания свойств.\n")
            report.append("- Для всех свойств всех видов заданы значения.\n")
            report.append("- Все значения корректны.\n\n")
        else:
            report.append("Обнаружены следующие проблемы:\n\n")
            current_variety = None
            for row in missing:
                if row["variety_name"] != current_variety:
                    current_variety = row["variety_name"]
                    report.append(f"Вид «{current_variety}»:\n")
                report.append(f"   - свойству «{row['prop_name']}» не заданы значения\n")

        self.result_text.insert(tk.END, "\n".join(report))
        self.result_text.config(state="disabled")
        conn.close()