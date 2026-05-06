from db.connection import init_db
from db.init_data import insert_initial_data
from editor.editor_main import EditorMain
from input_system import InputSystemWindow
import tkinter as tk
from ml_model import train_model

def main():
    init_db()
    insert_initial_data()

    train_model()

    root = tk.Tk()
    root.title("Классификация видов плодов малины")
    root.geometry("800x500")
    root.resizable(False, False)

    title_label = tk.Label(root,
                           text="Классификация видов плодов малины",
                           font=("Arial", 18, "bold"))
    title_label.pack(pady=50)

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=20)

    tk.Button(btn_frame, text="Редактор базы знаний (эксперт)",
              font=("Arial", 12), width=35, height=2,
              command=lambda: EditorMain(root)).pack(pady=12)

    tk.Button(btn_frame, text="Решатель задач (пользователь)",
              font=("Arial", 12), width=35, height=2, bg="#90ee90",
              command=lambda: InputSystemWindow(root)).pack(pady=12)

    tk.Button(btn_frame, text="Выход",
              font=("Arial", 11), width=35, height=2,
              command=root.destroy).pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    main()