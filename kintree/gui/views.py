import flet as ft
from flet import View

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

class SettingsView(View):

    __appbar = ft.AppBar(title=ft.Text('User Settings'), bgcolor=ft.colors.SURFACE_VARIANT)

    def __init__(self):
        super().__init__()
        self.route = '/settings'
        self.controls = [
            self.__appbar,
            ft.Text('Settings View', style="bodyMedium"),
        ]


class MainView(View):
    '''Common main view'''

    navidx = None
    page = None
    column = None
    fields = {}

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page

        # Appbar
        self.appbar = self.build_appbar()

        # Navigation rail
        self.__navigation_bar = self.build_navrail()

        # Build column
        self.column = self.build_column()

    def build_appbar(self, title='Ki-nTree | 0.7.0dev'):
        return ft.AppBar(
                leading=ft.Icon(ft.icons.INVENTORY),
                leading_width=40,
                title=ft.Text(title),
                center_title=False,
                bgcolor=ft.colors.SURFACE_VARIANT,
                actions = [
                    ft.IconButton(ft.icons.SETTINGS, on_click=lambda e: self.page.go(f'/settings')),
                ],
            )

    def build_navrail(self, selected_index=0):
        return ft.NavigationRail(
            selected_index=selected_index,
            label_type=ft.NavigationRailLabelType.ALL,
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
            on_change=lambda e: self.page.go(NAV_BAR_INDEX[e.control.selected_index]),
        )

    def build_column():
        # Empty column (set inside the children views)
        return ft.Column()

    def build_controls(self):
        self.controls = [
            ft.Row(
                controls = [
                    self.__navigation_bar,
                    ft.VerticalDivider(width=1),
                    self.column,
                ],
                expand=True,
            ),
        ]


class SearchView(MainView):
    '''Search view'''

    # Search view index
    navidx = 0

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

    fields = {
        'part_number': ft.TextField(label="Part Number", hint_text="Part Number", width=300, expand=True),
        'supplier': ft.Dropdown(label="Supplier"),
        'search_form': {},
    }

    def search_enable_fields(self):
        for form_field in self.fields['search_form'].values():
            form_field.disabled = False
        self.page.update()
        return

    def run_search(self):
        self.page.splash.visible = True
        self.page.update()

        if not self.fields['part_number'].value and not self.fields['supplier'].value:
            self.search_enable_fields()
        else:
            print(f"{self.fields['part_number'].value=} | {self.fields['supplier'].value=}")
            part_info = fetch_part_info(self.fields['part_number'].value)
            if part_info:
                for field_idx, field_name in enumerate(self.fields['search_form'].keys()):
                    # print(field_idx, field_name, get_default_search_keys()[field_idx], search_form_field[field_name])
                    try:
                        self.fields['search_form'][field_name].value = part_info.get(get_default_search_keys()[field_idx], '')
                    except IndexError:
                        pass
                    # Enable editing
                    self.fields['search_form'][field_name].disabled = False

        self.page.splash.visible = False
        self.page.update()
        return

    def build_column(self):
        return ft.Column(
            controls=[
                ft.Row(),
                ft.Row(
                    controls=[
                        self.fields['part_number'],
                        self.fields['supplier'],
                        ft.FloatingActionButton(
                            icon=ft.icons.SEARCH,
                            on_click=lambda e: self.run_search(),
                        ),
                    ],
                ),
                ft.Divider(),
            ],
            alignment=ft.MainAxisAlignment.START,
            scroll=ft.ScrollMode.HIDDEN,
            expand=True,   
        )
        
    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page)

        # Populate dropdown suppliers
        self.fields['supplier'].options = [ft.dropdown.Option(supplier) for supplier in SUPPORTED_SUPPLIERS]

        # Create search form
        for field in self.search_fields_list:
            label = field.replace('_', ' ').title()
            text_field = ft.TextField(label=label, hint_text=label, disabled=True, expand=True)
            self.column.controls.append(ft.Row(controls=[text_field]))
            self.fields['search_form'][field] = text_field


class KicadView(MainView):
    '''KiCad view'''
    navidx = 1

    def build_column(self):
        return ft.Column(
            controls=[
                ft.Text('KiCad', style="bodyMedium"),
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )


class InvenTreeView(MainView):
    '''InvenTree view'''
    navidx = 2

    def build_column(self):
        return ft.Column(
            controls=[
                ft.Text('InvenTree', style="bodyMedium"),
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
