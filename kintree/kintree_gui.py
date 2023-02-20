import flet as ft

from .gui.gui import kintree_gui


def main():
    browser = False
    if browser:
        ft.app(target=kintree_gui, view=ft.WEB_BROWSER)
    else:
        ft.app(target=kintree_gui)
