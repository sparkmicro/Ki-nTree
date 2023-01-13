import flet as ft
from flet import AppBar, Column, SnackBar, Text, View, colors

def MainGUI_Flet(page: ft.Page):
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_height = 300
    page.window_width = 800
    # page.window_resizable = True
    import time
    time.sleep(0.2)
    page.update()

    # Row 1
    def append_supplier_options(approved_supplier: list) -> list:
        dropdown_options = []
        for supplier in approved_supplier:
            dropdown_options.append(ft.dropdown.Option(supplier))
        return dropdown_options

    part_number = ft.TextField(label="Part Number", hint_text="Part Number", width=300, expand=True)
    supplier = ft.Dropdown(
        label="Supplier",
        options=append_supplier_options([
            'Digi-Key',
            'Mouser',
            'Farnell',
            'Newark',
            'Element14',
            'LCSC',
        ]),
    )

    # Row 2
    inventree_cb = ft.Container(
        content=ft.Checkbox(label="InvenTree", scale=1.3, value=False),
        alignment=ft.alignment.center,
    )
    kicad_cb = ft.Container(
        content=ft.Checkbox(label="KiCad", scale=1.3, value=False),
        alignment=ft.alignment.center,
    )
    alternate_cb = ft.Container(
        content=ft.Checkbox(label="Alternate", scale=1.3, value=False),
        alignment=ft.alignment.center,
    )

    # Row 3
    welcome_message = SnackBar(
        content=ft.Text("1. Enter a Part Number and select a Supplier\n2. Click on search icon to start creating part"),
        action="Close",
        open=True,
    )

    print("Initial route:", page.route)

    def route_change(e):
        print("Route change:", e.route)
        page.views.clear()
        page.views.append(
            View(
                "/",
                [
                    AppBar(
                        leading=ft.Icon(ft.icons.INVENTORY),
                        leading_width=40,
                        title=ft.Text("Ki-nTree | 0.7.0dev"),
                        center_title=False,
                        bgcolor=ft.colors.SURFACE_VARIANT,
                        actions=[
                            ft.IconButton(ft.icons.SETTINGS, on_click=open_settings),
                            ft.PopupMenuButton(
                                items=[
                                    ft.PopupMenuItem(
                                        text="Custom Part", checked=False, on_click=None
                                    ),
                                ]
                            ),
                        ],
                    ),
                    Column(
                        controls=[
                            ft.Row(),
                            ft.Row(
                                controls=[
                                    part_number,
                                    supplier,
                                    ft.FloatingActionButton(icon=ft.icons.SEARCH, on_click=None),
                                ],
                            ),
                            ft.Row(
                                controls=[
                                    kicad_cb,
                                    inventree_cb,
                                    alternate_cb,
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                            ),
                            ft.Row(
                                controls=[
                                    welcome_message
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        )

        if page.route == "/settings":
            page.views.append(
                View(
                    "/settings",
                    [
                        AppBar(title=Text("Settings"), bgcolor=colors.SURFACE_VARIANT),
                        Text("Settings!", style="bodyMedium"),
                    ],
                )
            )

        page.update()

    def view_pop(e):
        print("View pop:", e.view)
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    def open_settings(e):
        page.go("/settings")

    page.go(page.route)
