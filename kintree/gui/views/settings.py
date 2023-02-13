import os
import flet as ft
# Common view
from .common import CommonView
# Settings
from ...config import settings as global_settings
from ...config import config_interface


GUI_PARAMS = {
    'nav_rail_min_width': 100,
    'nav_rail_width': 400,
    'nav_rail_alignment': -0.9,
    'nav_rail_icon_size': 40,
    'nav_rail_text_size': 16,
    'nav_rail_padding': 10,
    'textfield_width': 600,
    'textfield_dense': False,
    'textfield_space_after': 3,
    'dropdown_width': 600,
    'dropdown_dense': False,
    'button_width': 100,
    'button_height': 56,
    'icon_size': 40,
}

# Load Supplier Settings
supplier_settings = {}
for supplier in global_settings.SUPPORTED_SUPPLIERS_API:
    supplier_settings[supplier] = {}

    # Add fields
    if supplier == 'Digi-Key':
        digikey_api_settings = config_interface.load_file(global_settings.CONFIG_DIGIKEY_API)
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
        mouser_api_settings = config_interface.load_file(global_settings.CONFIG_MOUSER_API)
        supplier_settings[supplier]['Part API Key'] = [
            mouser_api_settings['MOUSER_PART_API_KEY'],
            ft.TextField(),
            None,
        ]
    elif supplier == 'Element14' or supplier == 'Farnell' or supplier == 'Newark':
        from ...search.element14_api import STORES
        element14_api_settings = config_interface.load_file(global_settings.CONFIG_ELEMENT14_API)
        default_store = element14_api_settings.get(f'{supplier.upper()}_STORE', '')

        supplier_settings[supplier]['Product Search API Key (Element14)'] = [
            element14_api_settings['ELEMENT14_PRODUCT_SEARCH_API_KEY'],
            ft.TextField(),
            None,
        ]
        
        dropdown_options = []
        for store_name, store_url in STORES[supplier].items():
            dropdown_options.append(ft.dropdown.Option(f'{store_name} ({store_url})'))
        supplier_settings[supplier][f'{supplier} Store'] = [
            default_store,
            ft.Dropdown(
                label='Store',
                width=GUI_PARAMS['dropdown_width'],
                dense=GUI_PARAMS['dropdown_dense'],
                options=dropdown_options
            ),
            None,
        ]
    elif supplier == 'LCSC':
        lcsc_api_settings = config_interface.load_file(global_settings.CONFIG_LCSC_API)
        supplier_settings[supplier]['API URL'] = [
            lcsc_api_settings['LCSC_API_URL'],
            ft.TextField(),
            None,
        ]

SETTINGS = {
    'User Settings': {
        'Configuration Files Folder': [
            'USER_FILES',
            ft.TextField(),
            True,  # Browse enabled
        ],
        'Cache Folder': [
            'USER_CACHE',
            ft.TextField(),
            True,  # Browse enabled
        ],
    },
    'Supplier Settings': supplier_settings,
    'InvenTree Settings': {
        'Server Address': [
            'SERVER_ADDRESS',
            ft.TextField(),
            False,  # Browse disabled
        ],
        'Username': [
            'USERNAME',
            ft.TextField(),
            False,  # Browse disabled
        ],
        'Password': [
            'PASSWORD',
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
            'KICAD_SYMBOLS_PATH',
            ft.TextField(),
            True,  # Browse enabled
        ],
        'Symbol Templates Folder': [
            'KICAD_TEMPLATES_PATH',
            ft.TextField(),
            True,  # Browse enabled
        ],
        'Footprint Libraries Folder': [
            'KICAD_FOOTPRINTS_PATH',
            ft.TextField(),
            True,  # Browse enabled
        ],
    },
}

# Settings AppBar
settings_appbar = ft.AppBar(
    title=ft.Text('Ki-nTree Settings'),
    bgcolor=ft.colors.SURFACE_VARIANT
)

# Settings NavRail
settings_navrail = ft.NavigationRail(
    selected_index=0,
    label_type=ft.NavigationRailLabelType.ALL,
    min_width=GUI_PARAMS['nav_rail_min_width'],
    min_extended_width=GUI_PARAMS['nav_rail_width'],
    group_alignment=GUI_PARAMS['nav_rail_alignment'],
    destinations=[
        ft.NavigationRailDestination(
            label_content=ft.Text("User", size=GUI_PARAMS['nav_rail_text_size']),
            icon_content=ft.Icon(name=ft.icons.SUPERVISED_USER_CIRCLE, size=GUI_PARAMS['nav_rail_icon_size']),
            selected_icon_content=ft.Icon(name=ft.icons.SUPERVISED_USER_CIRCLE_OUTLINED, size=GUI_PARAMS['nav_rail_icon_size']),
            padding=GUI_PARAMS['nav_rail_padding'],
        ),
        ft.NavigationRailDestination(
            label_content=ft.Text("Supplier", size=GUI_PARAMS['nav_rail_text_size']),
            icon_content=ft.Icon(name=ft.icons.LOCAL_SHIPPING, size=GUI_PARAMS['nav_rail_icon_size']),
            selected_icon_content=ft.Icon(name=ft.icons.LOCAL_SHIPPING_OUTLINED, size=GUI_PARAMS['nav_rail_icon_size']),
            padding=GUI_PARAMS['nav_rail_padding'],
        ),
        ft.NavigationRailDestination(
            label_content=ft.Text("InvenTree", size=GUI_PARAMS['nav_rail_text_size']),
            icon_content=ft.Icon(name=ft.icons.INVENTORY, size=GUI_PARAMS['nav_rail_icon_size']),
            selected_icon_content=ft.Icon(name=ft.icons.INVENTORY_2_OUTLINED, size=GUI_PARAMS['nav_rail_icon_size']),
            padding=GUI_PARAMS['nav_rail_padding'],
        ),
        ft.NavigationRailDestination(
            label_content=ft.Text("KiCad", size=GUI_PARAMS['nav_rail_text_size']),
            icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT, size=GUI_PARAMS['nav_rail_icon_size']),
            selected_icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT_OUTLINED, size=GUI_PARAMS['nav_rail_icon_size']),
            padding=GUI_PARAMS['nav_rail_padding'],
        ),
    ],
    on_change=None,
)

class SettingsView(CommonView):
    '''Main settings view'''

    title = 'Settings'
    route = '/settings'
    settings = None
    settings_file = None
    banner = None

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
            if type(field_data) == list and field_data[0] is not None:
                self.fields[field_name] = field_data[1]
                self.fields[field_name].value = self.settings[field_data[0]]

        # Init view
        super().__init__(page=page, appbar=settings_appbar, navigation_rail=settings_navrail)

        # Update navigation rail
        if not self.navigation_rail.on_change:
            self.navigation_rail.on_change = lambda e: self.page.go(self.NAV_BAR_INDEX[e.control.selected_index])

    def set_dialog(self, open=True):
        if type(self.dialog) == ft.Banner:
            self.page.banner = self.dialog
            self.page.banner.open = open
        elif type(self.dialog) == ft.SnackBar:
            self.page.snack_bar = self.dialog
            self.page.snack_bar.open = True
        self.page.update()

    def set_snackbar(self):
        self.page.snackbar = self.banner
        self.page.snackbar.open = open
        self.page.update()
    
    def test_s(self, e: ft.ControlEvent, s: str):
        '''Test supplier API'''
        print(s)

    def test(self):
        '''Test settings'''
        print(f'Testing {self.title}')

    def save(self):
        '''Save settings'''
        print(f'Saving {self.title}')
        
        # Load file
        settings_from_file = config_interface.load_file(self.settings_file)
        # Update settings values
        for setting in SETTINGS[self.title].values():
            self.settings[setting[0]] = setting[1].value
        updated_settings = {**settings_from_file, **self.settings}
        # Save
        config_interface.dump_file(updated_settings, self.settings_file)

        # Alert user
        if self.dialog:
            self.set_dialog()

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
                field.width = GUI_PARAMS['textfield_width']
                field.dense = GUI_PARAMS['textfield_dense']
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
                        ft.ElevatedButton(
                            'Browse',
                            width=GUI_PARAMS['button_width'],
                            height=GUI_PARAMS['button_height'],
                            on_click=lambda e, t=field_name: self.path_picker(e, title=t)
                        ),
                    )
                column.controls.extend(
                    [
                        field_row,
                        ft.Row(height=GUI_PARAMS['textfield_space_after']),
                    ]
                )
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
                    ft.ElevatedButton(
                        field_name,
                        width=GUI_PARAMS['button_width'] * 2,
                        height=GUI_PARAMS['button_height'],
                        icon=ft.icons.CHECK_OUTLINED,
                        on_click=lambda e, s=field_name: self.test_s(e, s=s)
                    ),
                )
            elif type(field) == ft.Dropdown:
                field.on_change = lambda _: self.save()
                column.controls.append(
                    field,
                )

        # Test and Save buttons
        test_save_buttons = ft.Row()
        if list(SETTINGS[self.title])[-1] == 'Test':
            test_save_buttons.controls.append(
                ft.ElevatedButton(
                'Test',
                width=GUI_PARAMS['button_width'],
                height=GUI_PARAMS['button_height'],
                icon=ft.icons.CHECK_OUTLINED,
                on_click=lambda _: self.test()
                ),
            )
        test_save_buttons.controls.append(
                ft.ElevatedButton(
                    'Save',
                    width=GUI_PARAMS['button_width'],
                    height=GUI_PARAMS['button_height'],
                    icon=ft.icons.SAVE_OUTLINED,
                    on_click=lambda _: self.save()
                ),
            )
        column.controls.append(test_save_buttons)

        return column


class UserSettingsView(SettingsView):
    '''User settings view'''

    title = 'User Settings'
    route = '/settings/user'
    settings = global_settings.USER_SETTINGS
    settings_file = global_settings.USER_CONFIG_FILE

    def __init__(self, page: ft.Page):
        self.dialog = ft.Banner(
            bgcolor=ft.colors.AMBER_100,
            leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.AMBER, size=GUI_PARAMS['icon_size']),
            content=ft.Text('Restart Ki-nTree for the new user paths to be loaded'),
            actions=[
                ft.TextButton('Discard', on_click=lambda _: self.set_dialog(open=False)),
            ],
        )

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
                setting_data[1].width = GUI_PARAMS['textfield_width']
                setting_data[1].dense = GUI_PARAMS['textfield_dense']
                setting_data[1].value = setting_data[0]
                supplier_tab_content.extend(
                    [
                        ft.Row([setting_data[1]]),
                        ft.Row(height=GUI_PARAMS['textfield_space_after']),
                    ]
                )

            # Test and Save buttons
            supplier_tab_content.append(
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            'Test',
                            width=GUI_PARAMS['button_width'],
                            height=GUI_PARAMS['button_height'],
                            icon=ft.icons.CHECK_OUTLINED,
                            on_click=lambda e, s=supplier: self.test_s(e, s=s)
                        ),
                        ft.ElevatedButton(
                            'Save',
                            width=GUI_PARAMS['button_width'],
                            height=GUI_PARAMS['button_height'],
                            icon=ft.icons.SAVE_OUTLINED,
                            on_click=lambda _: self.save()
                        ),
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
    # settings = None
    settings_file = global_settings.INVENTREE_CONFIG

    def save(self):
        # Save to file
        config_interface.save_inventree_user_settings(enable=global_settings.ENABLE_INVENTREE,
                                                      server=SETTINGS[self.title]['Server Address'][1].value,
                                                      username=SETTINGS[self.title]['Username'][1].value,
                                                      password=SETTINGS[self.title]['Password'][1].value,
                                                      user_config_path=self.settings_file)
        # Reload InvenTree Settings
        global_settings.load_inventree_settings()

    def test(self):
        from ...database import inventree_interface
        self.save()
        connection = inventree_interface.connect_to_server()
        if connection:
            self.dialog = ft.SnackBar(
                bgcolor=ft.colors.GREEN_100,
                content=ft.Text(
                    'Sucessfully connected to InvenTree server',
                    color=ft.colors.GREEN_700,
                    size=GUI_PARAMS['nav_rail_text_size'],
                    weight=ft.FontWeight.BOLD,
                ),
            )
        else:
            self.dialog = ft.SnackBar(
                bgcolor=ft.colors.RED_ACCENT_100,
                content=ft.Text(
                    'ERROR: Failed to connect to InvenTree server. Make sure the credentials are correct and server is running',
                    color=ft.colors.RED_ACCENT_700,
                    size=GUI_PARAMS['nav_rail_text_size'],
                    weight=ft.FontWeight.BOLD,
                ),
            )
        self.set_dialog()

    def __init__(self, page: ft.Page):
        self.settings = config_interface.load_inventree_user_settings(self.settings_file)
        print(self.settings)
        super().__init__(page)


class KiCadSettingsView(SettingsView):
    '''KiCad settings view'''

    title = 'KiCad Settings'
    route = '/settings/kicad'
    settings = global_settings.KICAD_SETTINGS
    settings_file = global_settings.KICAD_CONFIG_PATHS

    def __init__(self, page: ft.Page):
        super().__init__(page)
