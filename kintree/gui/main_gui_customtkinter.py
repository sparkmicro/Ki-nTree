import tkinter
import tkinter.messagebox
from tkinter import Menu
import customtkinter

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

def hello_world():
    tkinter.messagebox.showinfo(title='MessageBox', message='Hello World')

class MainGUI_CustomTkinter(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Ki-nTree | 0.7.0dev")
        self.geometry(f"{800}x{260}")

        # Set scaling
        customtkinter.set_widget_scaling(1.2)

        self.build_menu()

        # configure grid layout (4x3)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure((0, 1, 2), weight=1)

        # Create headers frame
        self.part_number_label = customtkinter.CTkLabel(self, width=400, text="Part Number", anchor="w")
        self.part_number_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 0))
        self.supplier_label = customtkinter.CTkLabel(self, width=200, text="Supplier", anchor="w")
        self.supplier_label.grid(row=0, column=2, padx=20, pady=(10, 0))

        # Create entries row
        self.part_number_entry = customtkinter.CTkEntry(self, width=400, placeholder_text="Part Number")
        self.part_number_entry.grid(row=1, column=0, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="ew")
        self.supplier_entry = customtkinter.CTkOptionMenu(self, width=200, values=["Digi-Key", "Mouser", "Element14"])
        self.supplier_entry.grid(row=1, column=2, padx=20, pady=(10, 10), sticky="ew")

        # Create checkboxes row
        self.kicad_checkbox = customtkinter.CTkCheckBox(self, text="KiCad")
        self.kicad_checkbox.grid(row=2, column=0, padx=20, pady=(10, 10), sticky="ew")

        self.inventree_checkbox = customtkinter.CTkCheckBox(self, text="InvenTree")
        self.inventree_checkbox.grid(row=2, column=1, padx=20, pady=(10, 10), sticky="ew")

        self.alternate_checkbox = customtkinter.CTkCheckBox(self, text="Alternate")
        self.alternate_checkbox.grid(row=2, column=2, padx=20, pady=(10, 10), sticky="ew")

        # Create button row
        self.create_button = customtkinter.CTkButton(self, text='CREATE')
        self.create_button.grid(row=3, columnspan=3, padx=20, pady=(10, 10), sticky="ew")

    def build_menu(self):
        menu_bar = Menu(self)
        # self.config(menu=menu_bar)

        settingsMenu = Menu(menu_bar, tearoff="off")
        menu_bar.add_cascade(label="Settings", menu=settingsMenu)
        settingsMenu.add_command(label="User", command=hello_world)
        settingsMenu.add_command(label="InvenTree")
        settingsMenu.add_command(label="KiCad")
        settingsMenu.add_command(label="Suppliers")
        
        moreMenu = Menu(menu_bar, tearoff="off")
        menu_bar.add_cascade(label="More", menu=moreMenu)
        moreMenu.add_command(label="Custom Part")

        self.config(menu=menu_bar)
