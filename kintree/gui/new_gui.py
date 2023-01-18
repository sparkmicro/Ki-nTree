import flet as ft
from flet import View, colors

from ..search.digikey_api import fetch_part_info, get_default_search_keys

# Navigation indexes
NAV_BAR_INDEX = {
    0: '/search',
    1: '/kicad',
    2: '/inventree',
}

# TODO: replace with settings
SUPPORTED_SUPPLIERS = [
    'Digi-Key',
    'Mouser',
    'Farnell',
    'Newark',
    'Element14',
    'LCSC',
]

# List of search fields
search_fields_list = [
    'part_name',
    'part_description',
    'part_revision',
    'part_keywords',
    'supplier_name',
    'supplier_part_number',
    'supplier_link',
    'manufacturer_name',
    'manufacturer_part_number',
    'datasheet_link',
    'image_link',
]
# Instantiate search form fields
search_form_field = {}

def init_gui(page: ft.Page):
    ''' Initialize window '''
    # Alignments
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Theme
    page.theme_mode = "light"
    theme = ft.Theme()

    # Disable transitions
    theme.page_transitions.android = ft.PageTransitionTheme.NONE
    theme.page_transitions.ios = ft.PageTransitionTheme.NONE
    theme.page_transitions.linux = ft.PageTransitionTheme.NONE
    theme.page_transitions.macos = ft.PageTransitionTheme.NONE
    theme.page_transitions.windows = ft.PageTransitionTheme.NONE

    # Make it more compact
    theme.visual_density = ft.ThemeVisualDensity.COMPACT
    page.theme = theme
    page.scroll = ft.ScrollMode.ALWAYS

    # Creating a progress bar that will be used to show the user that the app is busy doing something.
    page.splash = ft.ProgressBar(visible=False)

    # Update
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

def search_enable_fields(page):
    for form_field in search_form_field.values():
        form_field.disabled = False
    page.update()
    return

def run_search(page):
    page.splash.visible = True
    page.update()

    if not part_number.value and not supplier.value:
        search_enable_fields(page)
    else:
        print(f'{part_number.value=} | {supplier.value=}')
        part_info = fetch_part_info(part_number.value)
        if part_info:
            for field_idx, field_name in enumerate(search_form_field.keys()):
                # print(field_idx, field_name, get_default_search_keys()[field_idx], search_form_field[field_name])
                try:
                    search_form_field[field_name].value = part_info.get(get_default_search_keys()[field_idx], '')
                except IndexError:
                    pass
                # Enable editing
                search_form_field[field_name].disabled = False

    page.splash.visible = False
    page.update()
    return

def append_supplier_options(approved_supplier: list) -> list:
        dropdown_options = []
        for supplier in approved_supplier:
            dropdown_options.append(ft.dropdown.Option(supplier))
        return dropdown_options

part_number = ft.TextField(label="Part Number", hint_text="Part Number", width=300, expand=True)
supplier = ft.Dropdown(
    label="Supplier",
    options=append_supplier_options(SUPPORTED_SUPPLIERS),
)

def search_column(page):
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
                    ft.FloatingActionButton(
                        icon=ft.icons.SEARCH,
                        on_click=lambda e: run_search(page),
                    ),
                ],
            ),
            ft.Divider(),
        ],
        alignment=ft.MainAxisAlignment.START,
        scroll=ft.ScrollMode.HIDDEN,
        expand=True,   
    )

    # Create search form
    for field in search_fields_list:
        label = field.replace('_', ' ').title()
        text_field = ft.TextField(label=label, hint_text=label, disabled=True, expand=True)
        search_view.controls.append(ft.Row(controls=[text_field]))
        search_form_field[field] = text_field

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
            page.views.append(build_main_view('/search', column=search_column(page)))
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
