import flet as ft
from flet import View

# InvenTree
from ..database import inventree_interface
# Tools
from ..common.tools import cprint, create_library

# TODO: replace with settings
SUPPORTED_SUPPLIERS = [
    'Digi-Key',
    'Mouser',
    'Farnell',
    'Newark',
    'Element14',
    'LCSC',
]

# Main AppBar
main_appbar = ft.AppBar(
    leading=ft.Icon(ft.icons.DOUBLE_ARROW),
    leading_width=40,
    title=ft.Text('Ki-nTree | 0.7.0dev'),
    center_title=False,
    bgcolor=ft.colors.SURFACE_VARIANT,
    actions=[],
)

# Settings AppBar
settings_appbar = ft.AppBar(
    title=ft.Text('Ki-nTree Settings'),
    bgcolor=ft.colors.SURFACE_VARIANT
)

# Main NavRail
main_navrail = ft.NavigationRail(
    selected_index=0,
    label_type=ft.NavigationRailLabelType.ALL,
    min_width=100,
    min_extended_width=400,
    group_alignment=-0.9,
    destinations=[
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.SEARCH, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.MANAGE_SEARCH, size=40),
            label_content=ft.Text("Search", size=16),
            padding=10,
        ),
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.INVENTORY_2_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.INVENTORY, size=40),
            label_content=ft.Text("InvenTree", size=16),
            padding=10,
        ),
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT, size=40),
            label_content=ft.Text("KiCad", size=16),
            padding=10,
        ),
    ],
    on_change=None,
)

# Settings NavRail
settings_navrail = ft.NavigationRail(
    selected_index=0,
    label_type=ft.NavigationRailLabelType.ALL,
    min_width=100,
    min_extended_width=400,
    group_alignment=-0.9,
    destinations=[
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.SUPERVISED_USER_CIRCLE, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.SUPERVISED_USER_CIRCLE_OUTLINED, size=40),
            label_content=ft.Text("User", size=16),
            padding=10,
        ),
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.LOCAL_SHIPPING, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.LOCAL_SHIPPING_OUTLINED, size=40),
            label_content=ft.Text("Supplier", size=16),
            padding=10,
        ),
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.INVENTORY_2_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.INVENTORY, size=40),
            label_content=ft.Text("InvenTree", size=16),
            padding=10,
        ),
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT, size=40),
            label_content=ft.Text("KiCad", size=16),
            padding=10,
        ),
    ],
    on_change=None,
)

class CommonView(View):
    '''Common view to all GUI views'''

    page = None
    navigation_rail = None
    navidx = None
    NAV_BAR_INDEX = {}
    column = None
    fields = {}
    
    def __init__(self, page: ft.Page, appbar: ft.NavigationBar, navigation_rail: ft.NavigationRail):
        # Store page pointer
        self.page = page

        # Init view
        super().__init__(route=self.route, appbar=appbar)

        # Set navigation rail
        if not self.navigation_rail:
            self.navigation_rail = navigation_rail

        # Build column
        if not self.column:
            self.column = self.build_column()

        # Build controls
        if not self.controls:
            self.controls = self.build_controls()

    def build_column(self):
        # Empty column (to be set inside the children views)
        return ft.Column()

    def build_controls(self):
        return [
            ft.Row(
                controls=[
                    self.navigation_rail,
                    ft.VerticalDivider(width=1),
                    self.column,
                ],
                expand=True,
            ),
        ]


class SettingsView(CommonView):
    '''Main settings view'''
    route = '/settings'

    # Navigation indexes
    NAV_BAR_INDEX = {
        0: '/settings/user',
        1: '/settings/supplier',
        2: '/settings/inventree',
        3: '/settings/kicad',
    }

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page=page, appbar=settings_appbar, navigation_rail=settings_navrail)

        # Update navigation rail
        if not self.navigation_rail.on_change:
            self.navigation_rail.on_change = lambda e: self.page.go(self.NAV_BAR_INDEX[e.control.selected_index])


class UserSettingsView(SettingsView):
    '''User settings view'''

    route = '/settings/user'

    def __init__(self, page: ft.Page):
        super().__init__(page)

        self.file_picker = ft.FilePicker(on_result=self.on_dialog_result)
        page.overlay.append(self.file_picker)
        page.update()

    def on_dialog_result(self, e: ft.FilePickerResultEvent):
            print("event: ", dir(e))
            print(e.name)
            print(e.control)
            print(e.target)
            print(e.data)
            print("Selected file or directory:", e.path)

    def build_column(self):
        return ft.Column(
            controls=[
                ft.Text('User Settings', style="bodyMedium"),
                ft.Row(),
                ft.Row(
                    controls=[
                        ft.TextField(label="Configuration Files Folder"),
                        ft.ElevatedButton("Browse", on_click=lambda _: self.file_picker.get_directory_path(dialog_title='Configuration Files Folder')),
                    ]
                ),
                ft.Row(
                    controls=[
                        ft.TextField(label="Cache Folder"),
                        ft.ElevatedButton("Browse", on_click=lambda _: self.file_picker.get_directory_path()),
                    ]
                ),
            ]
        )


class SupplierSettingsView(SettingsView):
    '''Supplier settings view'''

    route = '/settings/supplier'

    def build_column(self):
        return ft.Column(
            controls=[
                ft.Text('Supplier Settings', style="bodyMedium"),
            ]
        )


class InvenTreeSettingsView(SettingsView):
    '''Supplier settings view'''

    route = '/settings/inventree'

    def build_column(self):
        return ft.Column(
            controls=[
                ft.Text('InvenTree Settings', style="bodyMedium"),
            ]
        )


class KiCadSettingsView(SettingsView):
    '''Supplier settings view'''

    route = '/settings/kicad'

    def build_column(self):
        return ft.Column(
            controls=[
                ft.Text('KiCad Settings', style="bodyMedium"),
            ]
        )


class MainView(CommonView):
    '''Main view'''

    route = '/'
    # Navigation indexes
    NAV_BAR_INDEX = {
        0: '/search',
        1: '/inventree',
        2: '/kicad',
    }

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page=page, appbar=main_appbar, navigation_rail=main_navrail)

        # Update application bar
        if not self.appbar.actions:
            self.appbar.actions.append(ft.IconButton(ft.icons.SETTINGS, on_click=lambda e: self.page.go('/settings')))

        # Update navigation rail
        if not self.navigation_rail.on_change:
            self.navigation_rail.on_change = lambda e: self.page.go(self.NAV_BAR_INDEX[e.control.selected_index])


class SearchView(MainView):
    '''Search view'''

    route = '/search'

    # List of search fields
    search_fields_list = [
        'name',
        'description',
        'revision',
        'keywords',
        'supplier_name',
        'supplier_part_number',
        'supplier_link',
        'manufacturer_name',
        'manufacturer_part_number',
        'datasheet',
        'image',
    ]

    fields = {
        'part_number': ft.TextField(label="Part Number", dense=True, hint_text="Part Number", width=300, expand=True),
        'supplier': ft.Dropdown(label="Supplier", dense=True),
        'search_form': {},
    }

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page)

        # Populate dropdown suppliers
        self.fields['supplier'].options = [ft.dropdown.Option(supplier) for supplier in SUPPORTED_SUPPLIERS]

        # Create search form
        for field in self.search_fields_list:
            label = field.replace('_', ' ').title()
            text_field = ft.TextField(label=label, dense=True, hint_text=label, disabled=True, expand=True)
            self.column.controls.append(ft.Row(controls=[text_field]))
            self.fields['search_form'][field] = text_field

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
            # Supplier search
            part_supplier_info = inventree_interface.supplier_search(self.fields['supplier'].value, self.fields['part_number'].value)

            if part_supplier_info:
                # Translate to user form format
                part_supplier_form = inventree_interface.translate_supplier_to_form(supplier=self.fields['supplier'].value,
                                           part_info=part_supplier_info)

            if part_supplier_info:
                for field_idx, field_name in enumerate(self.fields['search_form'].keys()):
                    # print(field_idx, field_name, get_default_search_keys()[field_idx], search_form_field[field_name])
                    try:
                        self.fields['search_form'][field_name].value = part_supplier_form.get(field_name, '')
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
                            shape=ft.RoundedRectangleBorder(radius=5),
                            height=48,
                            width=80,
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


class InvenTreeView(MainView):
    '''InvenTree view'''

    route = '/inventree'

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page)

    def build_column(self):
        return ft.Column(
            controls=[
                ft.Text('InvenTree', style="bodyMedium"),
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )


class KicadView(MainView):
    '''KiCad view'''

    route = '/kicad'

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page)

    def build_column(self):
        return ft.Column(
            controls=[
                ft.Text('KiCad', style="bodyMedium"),
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
