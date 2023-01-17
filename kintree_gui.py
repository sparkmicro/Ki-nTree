from kintree.gui.main_gui_customtkinter import MainGUI_CustomTkinter
from kintree.gui.main_gui_flet import MainGUI_Flet
from kintree.gui.new_gui import MainGUI

if __name__ == '__main__':
    # CustomTkinter
    if False:
        main_gui = MainGUI_CustomTkinter()
        main_gui.mainloop()

    # Flet
    if False:
        import flet as ft
        ft.app(target=MainGUI_Flet)

    # New GUI
    if True:
        import flet as ft
        ft.app(target=MainGUI)
