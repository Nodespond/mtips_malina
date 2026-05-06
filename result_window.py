import tkinter as tk
from tkinter import ttk
from db.connection import get_connection


class ResultWindow(tk.Toplevel):
    def __init__(self, parent, suitable, rejections, input_data=None):
        super().__init__(parent)
        self.title("Результат")
        self.geometry("980x720")

        self.create_widgets(suitable, rejections)

    def create_widgets(self, suitable, rejections):
        tk.Label(self, text="Результат", font=("Arial", 18, "bold")).pack(pady=15)

        suitable_frame = tk.LabelFrame(self, text="Подходящие виды", padx=20, pady=12)
        suitable_frame.pack(fill=tk.X, padx=25, pady=(0, 10))

        if suitable:
            for variety in suitable:
                tk.Label(suitable_frame, text=variety,
                         font=("Arial", 12, "bold"), fg="#2e7d32").pack(anchor="w", pady=4)
        else:
            tk.Label(suitable_frame, text="Вид не определен. Подходящих не найдено.",
                     font=("Arial", 11), fg="#c62828").pack(anchor="w", pady=5)

        rej_frame = tk.LabelFrame(self, text="Объяснение опровержений", padx=20, pady=12)
        rej_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=10)

        result_text = tk.Text(rej_frame, wrap=tk.WORD, font=("Arial", 10), height=22)
        scrollbar = tk.Scrollbar(rej_frame, command=result_text.yview)
        result_text.configure(yscrollcommand=scrollbar.set)

        result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        explanation = self._build_explanation(suitable, rejections)
        result_text.insert(tk.END, explanation)
        result_text.config(state="disabled")

    def _build_explanation(self, suitable, rejections):
        text = ""

        if suitable:
            text += "Другие виды опровергнуты по следующим причинам:\n\n"
        else:
            text += "Все виды опровергнуты по следующим причинам:\n\n"

        for rej in rejections:
            variety = rej.get('variety', 'Неизвестный вид')
            text += f"Вид «{variety}» опровергнут,\n"

            for reason in rej.get('reasons', []):
                prop = reason.get('property', '')
                user_value = reason.get('user_value', reason.get('value', ''))

                text += f"так как значение «{user_value}» свойства «{prop}» "
                text += f"не соответствует описанию вида."

                expected = reason.get('expected')
                if expected:
                    text += f" (допустимо «{expected}»)"
                else:
                    reason_str = reason.get('reason', '')
                    if 'ожидался диапазон' in reason_str or 'ожидается' in reason_str:
                        import re
                        match = re.search(r'\[.*?\]', reason_str)
                        if match:
                            allowed = match.group(0)
                            text += f" (допустимо {allowed})"
                        else:
                            if 'ожидался диапазон' in reason_str:
                                allowed_part = reason_str.split('ожидался диапазон')[-1].strip()
                                text += f" (допустимо {allowed_part})"

                text += "\n"

            text += "\n"

        if not suitable:
            text += "\nРекомендуется проверить корректность введённых данных\n"
            text += "либо уточнить базу знаний у эксперта."

        return text


class KnowledgeBaseViewer(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Просмотр базы знаний")
        self.geometry("850x600")

        tk.Label(self, text="База знаний (виды и их характеристики)",
                 font=("Arial", 14, "bold")).pack(pady=10)

        text = tk.Text(self, wrap=tk.WORD, font=("Consolas", 9))
        text.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self.load_data(text)

    def load_data(self, text_widget):
        from db.connection import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.name, p.name as prop, 
                   vv.categorical_value, vv.min_value, vv.max_value
            FROM varieties v
            JOIN variety_properties vp ON v.id = vp.variety_id
            JOIN properties p ON p.id = vp.property_id
            LEFT JOIN variety_values vv ON vv.variety_id = v.id 
                                       AND vv.property_id = p.id
            ORDER BY v.name, p.name
        """)
        rows = cursor.fetchall()
        conn.close()

        current = None
        for row in rows:
            if row[0] != current:
                current = row[0]
                text_widget.insert(tk.END, f"\n{current}:\n")
            val = row[2] or (f"[{row[3]} — {row[4]}]" if row[3] is not None else "не задано")
            text_widget.insert(tk.END, f"   • {row[1]}: {val}\n")