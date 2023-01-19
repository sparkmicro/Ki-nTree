import flet as ft
from flet import View

from ..search.digikey_api import fetch_part_info, get_default_search_keys


class MainView(View):
    '''Common main view'''

    navidx = None
    page = None
    column = None
    fields = {}

    def __init__(self, page: ft.Page, appbar: ft.AppBar, navrail: ft.NavigationRail):
        super().__init__()
        self.page = page
        self.appbar = appbar
        self.__navigation_bar = navrail

        # Build column
        self.column = self.build_column()

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
        'supplier': ft.Dropdown(
            label="Supplier",
            # options=append_supplier_options(SUPPORTED_SUPPLIERS),
        ),
        # Instantiate search form fields
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
        
    def __init__(self, page: ft.Page, appbar: ft.AppBar, navrail: ft.NavigationRail):
        # Init view
        super().__init__(page, appbar, navrail)

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
