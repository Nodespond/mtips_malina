# editor/editor_main.py
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

        self.editor_windows = []

        self.create_widgets()

    def register_window(self, window):
        if window not in self.editor_windows:
            self.editor_windows.append(window)

    def refresh_all_windows(self):
        for window in self.editor_windows:
            if hasattr(window, 'refresh_data'):
                window.refresh_data()

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

        varieties_win = VarietiesWindow(tab1, embedded=True, editor=self)
        self.register_window(varieties_win)

        PropertiesWindow(tab2, embedded=True)

        possible_values_win = PossibleValuesWindow(tab3, embedded=True, editor=self)
        self.register_window(possible_values_win)

        variety_props_win = VarietyPropertiesWindow(tab4, embedded=True, editor=self)
        self.register_window(variety_props_win)

        variety_values_win = VarietyValuesWindow(tab5, embedded=True, editor=self)
        self.register_window(variety_values_win)

        ValidationWindow(tab6, embedded=True)

        tk.Button(self, text="Закрыть редактор",
                  command=self.destroy, font=("Arial", 10)).pack(pady=8)