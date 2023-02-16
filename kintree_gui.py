import flet as ft

from kintree.gui.gui import kintree_gui

if __name__ == '__main__':
    browser = False
    if browser:
        ft.app(target=kintree_gui, view=ft.WEB_BROWSER)
    else:
        ft.app(target=kintree_gui)
