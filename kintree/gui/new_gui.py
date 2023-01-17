import flet as ft
from flet import View, colors


NAV_BAR_INDEX = {
    0: '/search',
    1: '/kicad',
    2: '/inventree',
}

def init_gui(page: ft.Page):
    ''' Initialize window '''
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.update()

def main_app_bar(page: ft.Page, title='Ki-nTree | 0.7.0dev'):
    ''' Top application bar '''    
    app_bar = ft.AppBar(
        leading=ft.Icon(ft.icons.INVENTORY),
        leading_width=40,
        title=ft.Text(title),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions = [
            ft.IconButton(ft.icons.SETTINGS, on_click=lambda e: page.go(f'/settings')),
        ],
    )

    return app_bar

def settings_app_bar(page: ft.Page, title='User Settings'):
    return ft.AppBar(title=ft.Text(title), bgcolor=colors.SURFACE_VARIANT)

def nav_rail(page: ft.Page, selected_index=0):
    ''' Navigation rail '''

    rail = ft.NavigationRail(
        selected_index=selected_index,
        label_type=ft.NavigationRailLabelType.ALL,
        # extended=True,
        min_width=100,
        min_extended_width=400,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.SEARCH,
                selected_icon=ft.icons.MANAGE_SEARCH,
                label="Search"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_INPUT_COMPONENT_OUTLINED,
                selected_icon=ft.icons.SETTINGS_INPUT_COMPONENT,
                label="KiCad",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.INVENTORY_2_OUTLINED,
                selected_icon_content=ft.Icon(ft.icons.INVENTORY),
                label_content=ft.Text("InvenTree"),
            ),
        ],
        on_change=lambda e: page.go(NAV_BAR_INDEX[e.control.selected_index]),
    )

    return rail

    return ft.Row(
        [
            rail,
            ft.VerticalDivider(width=1),
            # ft.Column([ ft.Text("Body!")], alignment=ft.MainAxisAlignment.START, expand=True),
        ],
        expand=True,
    )

def search_column():
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
    # inventree_cb = ft.Container(
    #     content=ft.Checkbox(label="InvenTree", scale=1.3, value=False),
    #     alignment=ft.alignment.center,
    # )
    # kicad_cb = ft.Container(
    #     content=ft.Checkbox(label="KiCad", scale=1.3, value=False),
    #     alignment=ft.alignment.center,
    # )
    # alternate_cb = ft.Container(
    #     content=ft.Checkbox(label="Alternate", scale=1.3, value=False),
    #     alignment=ft.alignment.center,
    # )

    # Row 3
    # welcome_message = ft.SnackBar(
    #     content=ft.Text("1. Enter a Part Number and select a Supplier\n2. Click on search icon to start creating part"),
    #     action="Close",
    #     open=True,
    # )
    
    search_view = ft.Column(
        controls=[
            ft.Row(),
            ft.Row(
                controls=[
                    part_number,
                    supplier,
                    ft.FloatingActionButton(icon=ft.icons.SEARCH, on_click=None),
                ],
            ),
            # ft.Row(
            #     controls=[
            #         kicad_cb,
            #         inventree_cb,
            #         alternate_cb,
            #     ],
            #     alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            # ),
            # ft.Row(
            #     controls=[
            #         welcome_message
            #     ],
            # ),
        ],
        alignment=ft.MainAxisAlignment.START,
        expand=True,
    )

    return search_view

def MainGUI(page: ft.Page):

    def build_main_view(route, column: ft.Column, nav_index=0):
        return ft.View(
            route = route,
            controls = [
                main_app_bar(page),
                ft.Row(
                    controls = [
                        nav_rail(page, selected_index=nav_index),
                        ft.VerticalDivider(width=1),
                        column,
                    ],
                    expand=True,
                ),
            ],
        )

    # Init
    init_gui(page)

    # Routing
    print(f'Initial route {page.route}')

    def route_change(route):
        print(f'New route {page.route}')
        
        if page.route in ['/', '/search']:
            page.views.clear()
            page.views.append(build_main_view('/search', column=search_column()))
        elif '/kicad' in page.route:
            kicad_column = ft.Column(
                controls=[
                    ft.Text('KiCad', style="bodyMedium"),
                ],
                alignment=ft.MainAxisAlignment.START,
                expand=True,
            )
            page.views.append(build_main_view('/kicad', column=kicad_column, nav_index=1))
        elif '/inventree' in page.route:
            page.views.clear()
            inventree_column = ft.Column(
                controls=[
                    ft.Text('InvenTree', style="bodyMedium"),
                ],
                alignment=ft.MainAxisAlignment.START,
                expand=True,
            )
            page.views.append(build_main_view('/inventree', column=inventree_column, nav_index=2))
        elif '/settings' in page.route:
            page.views.append(
                ft.View(
                    '/settings',
                    [
                        settings_app_bar(page),
                        ft.Text('Settings View', style="bodyMedium"),
                    ],
                )
            )

        page.update()

    def view_pop(e):
        # print("View pop:", e.view)
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go(page.route)
