import tkinter as tk
from tkinter import ttk

from editor.varieties_window import VarietiesWindow
from editor.properties_window import PropertiesWindow
from editor.possible_values_window import PossibleValuesWindow
from editor.variety_properties_window import VarietyPropertiesWindow
from editor.variety_values_window import VarietyValuesWindow
from editor.validation_window import ValidationWindow


class EditorMain(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Редактор базы знаний")
        self.geometry("900x650")
        self.parent = parent

        self.create_widgets()

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tab1 = tk.Frame(notebook)
        tab2 = tk.Frame(notebook)
        tab3 = tk.Frame(notebook)
        tab4 = tk.Frame(notebook)
        tab5 = tk.Frame(notebook)
        tab6 = tk.Frame(notebook)

        notebook.add(tab1, text="1. Виды плодов малины")
        notebook.add(tab2, text="2. Свойства")
        notebook.add(tab3, text="3. Возможные значения")
        notebook.add(tab4, text="4. Описание свойств вида")
        notebook.add(tab5, text="5. Значения для вида")
        notebook.add(tab6, text="6. Проверка полноты знаний")

        VarietiesWindow(tab1, embedded=True)
        PropertiesWindow(tab2, embedded=True)
        PossibleValuesWindow(tab3, embedded=True)
        VarietyPropertiesWindow(tab4, embedded=True)
        VarietyValuesWindow(tab5, embedded=True)
        ValidationWindow(tab6, embedded=True)

        tk.Button(self, text="Закрыть редактор",
                  command=self.destroy, font=("Arial", 10)).pack(pady=8)