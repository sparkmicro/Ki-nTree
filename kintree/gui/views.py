import flet as ft
from flet import View

# Settings
from ..config import settings, config_interface
# InvenTree
from ..database import inventree_interface
# Tools
from ..common.tools import cprint, create_library

# Load InvenTree Settings
settings.load_inventree_settings()
# Load Supplier Settings
supplier_settings = {}
for supplier in settings.SUPPORTED_SUPPLIERS_API:
    supplier_settings[supplier] = {}

    # Add fields
    if supplier == 'Digi-Key':
        digikey_api_settings = config_interface.load_file(settings.CONFIG_DIGIKEY_API)
        supplier_settings[supplier]['Client ID'] = [
            digikey_api_settings['DIGIKEY_CLIENT_ID'],
            ft.TextField(),
            None,
        ]
        supplier_settings[supplier]['Client Secret'] = [
            digikey_api_settings['DIGIKEY_CLIENT_SECRET'],
            ft.TextField(),
            None,
        ]
    elif supplier == 'Mouser':
        mouser_api_settings = config_interface.load_file(settings.CONFIG_MOUSER_API)
        supplier_settings[supplier]['Part API Key'] = [
            mouser_api_settings['MOUSER_PART_API_KEY'],
            ft.TextField(),
            None,
        ]
    elif supplier == 'Element14' or supplier == 'Farnell' or supplier == 'Newark':
        from ..search.element14_api import STORES
        element14_api_settings = config_interface.load_file(settings.CONFIG_ELEMENT14_API)
        default_store = element14_api_settings.get(f'{supplier.upper()}_STORE', '')

        supplier_settings[supplier]['Product Search API Key'] = [
            element14_api_settings['ELEMENT14_PRODUCT_SEARCH_API_KEY'],
            ft.TextField(),
            None,
        ]
        
        dropdown_options = []
        for store in STORES[supplier].keys():
            dropdown_options.append(ft.dropdown.Option(store))
        supplier_settings[supplier][f'{supplier} Store'] = [
            default_store,
            ft.Dropdown(label='Store', width=800, options=dropdown_options),
            None,
        ]
    elif supplier == 'LCSC':
        lcsc_api_settings = config_interface.load_file(settings.CONFIG_LCSC_API)
        supplier_settings[supplier]['API URL'] = [
            lcsc_api_settings['LCSC_API_URL'],
            ft.TextField(),
            None,
        ]

SETTINGS = {
    'User Settings': {
        'Configuration Files Folder': [
            settings.USER_SETTINGS['USER_FILES'],
            ft.TextField(),
            True,  # Browse enabled
        ],
        'Cache Folder': [
            settings.USER_SETTINGS['USER_CACHE'],
            ft.TextField(),
            True,  # Browse enabled
        ],
    },
    'Supplier Settings': supplier_settings,
    'InvenTree Settings': {
        'Server Address': [
            settings.SERVER_ADDRESS,
            ft.TextField(),
            False,  # Browse disabled
        ],
        'Username': [
            settings.USERNAME,
            ft.TextField(),
            False,  # Browse disabled
        ],
        'Password': [
            settings.PASSWORD,
            ft.TextField(),
            False,  # Browse disabled
        ],
        'Test': [
            None,
            ft.ElevatedButton,
            False, # Browse disabled
        ]
    },
    'KiCad Settings': {
        'Symbol Libraries Folder': [
            settings.KICAD_SYMBOLS_PATH,
            ft.TextField(),
            True,  # Browse enabled
        ],
        'Symbol Templates Folder': [
            settings.KICAD_TEMPLATES_PATH,
            ft.TextField(),
            True,  # Browse enabled
        ],
        'Footprint Libraries Folder': [
            settings.KICAD_FOOTPRINTS_PATH,
            ft.TextField(),
            True,  # Browse enabled
        ],
    },
}

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
            icon_content=ft.Icon(name=ft.icons.INVENTORY, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.INVENTORY_2_OUTLINED, size=40),
            label_content=ft.Text("InvenTree", size=16),
            padding=10,
        ),
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT_OUTLINED, size=40),
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

    title = 'Settings'
    route = '/settings'

    # Navigation indexes
    NAV_BAR_INDEX = {
        0: '/settings/user',
        1: '/settings/supplier',
        2: '/settings/inventree',
        3: '/settings/kicad',
    }

    def __init__(self, page: ft.Page):
        # Load setting fields
        self.fields = {}
        for field_name, field_data in SETTINGS.get(self.title, {}).items():
            if type(field_data) == list:
                self.fields[field_name] = field_data[1]
                self.fields[field_name].value = field_data[0]

        # Init view
        super().__init__(page=page, appbar=settings_appbar, navigation_rail=settings_navrail)

        # Update navigation rail
        if not self.navigation_rail.on_change:
            self.navigation_rail.on_change = lambda e: self.page.go(self.NAV_BAR_INDEX[e.control.selected_index])
    
    def test_s(self, e: ft.ControlEvent, s: str):
        '''Test supplier API'''
        print(s)

    def test(self):
        '''Test settings'''
        print(f'Testing {self.title}')

    def save(self):
        '''Save settings'''
        print(f'Saving {self.title}')

    def on_dialog_result(self, e: ft.FilePickerResultEvent):
        '''Populate field with user-selected system path'''
        if e.path:
            self.fields[e.control.dialog_title].value = e.path
            self.page.update()

    def path_picker(self, e: ft.ControlEvent, title: str):
        '''Let user browse to a system path'''
        if self.page.overlay:
            self.page.overlay.pop()
        path_picker = ft.FilePicker(on_result=self.on_dialog_result)
        self.page.overlay.append(path_picker)
        self.page.update()
        path_picker.get_directory_path(dialog_title=title, initial_directory=self.fields[title].value)

    def build_column(self):
        button_width = 100
        button_height = 48
        # Title and separator
        column = ft.Column(
            controls=[
                ft.Text(self.title, style="bodyMedium"),
                ft.Row(),
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
        # Fields
        for field_name, field in self.fields.items():
            if type(field) == ft.TextField:
                field.label = field_name
                field.width = 800
                if 'password' in field.label.lower():
                    field.password = True
                field_row = ft.Row(
                    controls=[
                        field,
                    ]
                )
                # Add browse button
                if SETTINGS[self.title][field_name][2]:
                    field_row.controls.append(
                        ft.ElevatedButton('Browse', width=button_width, height=button_height, on_click=lambda e, t=field_name: self.path_picker(e, title=t))
                    )
                column.controls.append(field_row)
            elif type(field) == ft.Text:
                field.value = field_name
                field_row = ft.Row(
                    controls=[
                        field,
                    ]
                )
                column.controls.append(field_row)
                column.controls.append(ft.Divider())
            elif type(field) == ft.TextButton:
                column.controls.append(
                    ft.ElevatedButton(field_name, width=button_width*2, height=button_height, icon=ft.icons.CHECK_OUTLINED, on_click=lambda e, s=field_name: self.test_s(e, s=s)),
                )
            elif type(field) == ft.Dropdown:
                field.on_change = lambda _: self.save()
                column.controls.append(
                    field,
                )

        # Test and Save buttons
        test_save_buttons = ft.Row()
        if list(self.fields.keys())[-1] == 'Test':
            test_save_buttons.controls.append(
                ft.ElevatedButton('Test', width=button_width, height=button_height, icon=ft.icons.CHECK_OUTLINED, on_click=lambda _: self.test()),
            )
        test_save_buttons.controls.append(
                ft.ElevatedButton('Save', width=button_width, height=button_height, icon=ft.icons.SAVE_OUTLINED, on_click=lambda _: self.save()),
            )
        column.controls.append(test_save_buttons)

        return column


class UserSettingsView(SettingsView):
    '''User settings view'''

    title = 'User Settings'
    route = '/settings/user'

    def __init__(self, page: ft.Page):
        super().__init__(page)


class SupplierSettingsView(SettingsView):
    '''Supplier settings view'''

    title = 'Supplier Settings'
    route = '/settings/supplier'

    def __init__(self, page: ft.Page):
        super().__init__(page)

    def test_s(self, e: ft.ControlEvent, s: str):
        '''Test supplier API'''
        supplier = s.replace('Test', '').replace('API', '').replace(' ','')
        print(f'Testing {supplier} API')

    def build_column(self):
        button_width = 100
        button_height = 48
        # Title and separator
        column = ft.Column(
            controls=[
                ft.Text(self.title, style="bodyMedium"),
                ft.Row(),
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
        # Tabs
        supplier_tabs = ft.Tabs(
            selected_index=0,
            animation_duration=10,
            expand=1,
            tabs=[],
        )
        for supplier, settings in SETTINGS[self.title].items():
            supplier_tab_content = [
                ft.Row(height=10),
            ]
            for setting_name, setting_data in settings.items():
                setting_data[1].label = setting_name
                setting_data[1].width = 800
                setting_data[1].value = setting_data[0]
                supplier_tab_content.append(
                    ft.Row(
                        controls=[
                            setting_data[1]
                        ]
                    )
                )

            # Test and Save buttons
            supplier_tab_content.append(
                ft.Row(
                    controls=[
                        ft.ElevatedButton('Test', width=button_width, height=button_height, icon=ft.icons.CHECK_OUTLINED, on_click=lambda e, s=supplier: self.test_s(e, s=s)),
                        ft.ElevatedButton('Save', width=button_width, height=button_height, icon=ft.icons.SAVE_OUTLINED, on_click=lambda _: self.save()),
                    ]
                )
            )

            supplier_tabs.tabs.append(
                ft.Tab(
                    tab_content=ft.Text(supplier, size=16),
                    content=ft.Container(
                        ft.Column(
                            controls=supplier_tab_content,
                        )
                    )
                )
            )

        column.controls.append(supplier_tabs)
        return column


class InvenTreeSettingsView(SettingsView):
    '''InvenTree settings view'''

    title = 'InvenTree Settings'
    route = '/settings/inventree'

    def __init__(self, page: ft.Page):
        super().__init__(page)


class KiCadSettingsView(SettingsView):
    '''KiCad settings view'''

    title = 'KiCad Settings'
    route = '/settings/kicad'

    def __init__(self, page: ft.Page):
        super().__init__(page)


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
        self.fields['supplier'].options = [ft.dropdown.Option(supplier) for supplier in settings.SUPPORTED_SUPPLIERS_API]

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
