import flet as ft

# Common view
from .common import DialogType
from .common import CommonView
from .common import SwitchWithRefs
from .common import GUI_PARAMS
from .common import handle_transition
# Settings
from ...config import settings as global_settings
from ...config import config_interface


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
        'Open Browser After Creating Part': [
            'AUTOMATIC_BROWSER_OPEN',
            ft.Switch(),
            False,  # Browse enabled
        ],
        'Enable Supplier Search Cache': [
            'CACHE_ENABLED',
            SwitchWithRefs(),
            False,  # Browse enabled
        ],
        'CACHE_VALID_DAYS': [
            'CACHE_VALID_DAYS',
            ft.TextField(
                text_align=ft.TextAlign.CENTER,
                width=60,
                dense=True,
                disabled=True,
            ),
            False,
        ]
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
        'Default Revision': [
            'INVENTREE_DEFAULT_REV',
            ft.TextField(),
            False,  # Browse disabled
        ],
        'Enable Internal Part Number (IPN)': [
            'IPN_ENABLE_CREATE',
            SwitchWithRefs(),
            False,  # Browse disabled
        ],
        'IPN: Enable Prefix': [
            'IPN_ENABLE_PREFIX',
            SwitchWithRefs(),
            False,  # Browse disabled
        ],
        'IPN: Prefix': [
            'IPN_PREFIX',
            ft.TextField(),
            False,  # Browse disabled
        ],
        'IPN: Length of Unique ID': [
            'IPN_UNIQUE_ID_LENGTH',
            ft.TextField(),
            False,  # Browse disabled
        ],
        'IPN: Enable Suffix': [
            'IPN_ENABLE_SUFFIX',
            SwitchWithRefs(),
            False,  # Browse disabled
        ],
        'IPN: Suffix': [
            'IPN_SUFFIX',
            ft.TextField(),
            False,  # Browse disabled
        ],
        'Test': [
            None,
            ft.ElevatedButton,
            False,  # Browse disabled
        ],
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
            icon_content=ft.Icon(name=ft.icons.INVENTORY_2, size=GUI_PARAMS['nav_rail_icon_size']),
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
    dialog = None

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
    
    def save(self, settings_file=None, show_dialog=True):
        '''Save settings'''
        if settings_file is not None:
            settings_from_file = config_interface.load_file(settings_file)
        else:
            settings_from_file = config_interface.load_file(self.settings_file)

        # Update settings values
        for key in settings_from_file:
            for setting in SETTINGS[self.title].values():
                if key == setting[0]:
                    settings_from_file[key] = setting[1].value

        # Save
        if settings_file is not None:
            config_interface.dump_file(settings_from_file, settings_file)
        else:
            config_interface.dump_file(settings_from_file, self.settings_file)

        # Alert user
        if show_dialog:
            self.show_dialog(
                d_type=DialogType.VALID,
                message=f'{self.title} successfully saved',
            )

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

    def build_column(self, ignore=[]):
        # Title and separator
        self.column = ft.Column(
            controls=[
                ft.Text(self.title, style="bodyMedium"),
                ft.Row(),
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
        # Fields
        for field_name, field in self.fields.items():
            if field_name not in ignore:
                if type(field) == ft.TextField:
                    field_predefined = bool(field.width)
                    if not field_predefined:
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
                                    height=48,
                                    on_click=lambda e, t=field_name: self.path_picker(e, title=t)
                                ),
                            )
                        self.column.controls.extend(
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
                    self.column.controls.append(field_row)
                    self.column.controls.append(ft.Divider())
                elif type(field) == ft.TextButton:
                    self.column.controls.append(
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
                    self.column.controls.append(
                        field,
                    )
                elif type(field) == ft.Switch or type(field) == SwitchWithRefs:
                    field.on_change = lambda _: self.save()
                    field.label = field_name
                    self.column.controls.append(
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
                    on_click=lambda _: self.test(),
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
        self.column.controls.append(test_save_buttons)

    def did_mount(self):
        handle_transition(self.page, transition=False, timeout=0.05)
        return super().did_mount()


class UserSettingsView(SettingsView):
    '''User settings view'''

    title = 'User Settings'
    route = '/settings/user'
    settings = {
        **global_settings.USER_SETTINGS,
        **{'AUTOMATIC_BROWSER_OPEN': global_settings.AUTOMATIC_BROWSER_OPEN},
        **{'CACHE_ENABLED': global_settings.CACHE_ENABLED,
           'CACHE_VALID_DAYS': global_settings.CACHE_VALID_DAYS},
    }
    settings_file = [
        global_settings.USER_CONFIG_FILE,
        global_settings.CONFIG_GENERAL_PATH,
        global_settings.CONFIG_SEARCH_API_PATH,
    ]

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.dialog = self.build_dialog()

    def build_dialog(self):
        return ft.Banner(
            bgcolor=ft.colors.AMBER_100,
            leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.AMBER, size=GUI_PARAMS['icon_size']),
            content=ft.Text('Restart Ki-nTree to load the new user settings', weight=ft.FontWeight.BOLD),
            actions=[
                ft.TextButton('Discard', on_click=lambda _: self.show_dialog(open=False)),
            ],
        )
    
    def show_dialog(self, d_type=None, message=None, snackbar=False, open=True):
        return super().show_dialog(d_type, message, snackbar, open)
    
    def increment_cache_value(self, inc):
        field = SETTINGS[self.title]['CACHE_VALID_DAYS'][1]
        current_value = int(field.value)
        if not inc:
            if current_value > 1:
                field.value = f'{current_value - 1}'
        else:
            if current_value < 99:
                field.value = f'{current_value + 1}'
        field.on_change(_=None)
        field.update()

    def build_column(self):
        super().build_column()
    
        # Create row ref
        cache_row_ref = ft.Ref[ft.Row]()
        # Create row for cache validity
        SETTINGS[self.title]['CACHE_VALID_DAYS'][1].value = self.settings['CACHE_VALID_DAYS']
        cache_row = ft.Row(
            ref=cache_row_ref,
            controls=[
                ft.Text('Keep Cache Valid For (Days): '),
                ft.IconButton(ft.icons.REMOVE, on_click=lambda _: self.increment_cache_value(False)),
                SETTINGS[self.title]['CACHE_VALID_DAYS'][1],
                ft.IconButton(ft.icons.ADD, on_click=lambda _: self.increment_cache_value(True)),
            ],
        )
        self.column.controls.insert(-1, cache_row)
        # Add cache row to switch refs
        SETTINGS[self.title]['Enable Supplier Search Cache'][1].refs = [cache_row_ref]
        
        setting_file1 = self.settings_file[1]
        setting_file2 = self.settings_file[2]

        for name, field in SETTINGS[self.title].items():
            if field[0] == 'AUTOMATIC_BROWSER_OPEN':
                self.fields[name].on_change = lambda _: self.save(
                    settings_file=setting_file1,
                    show_dialog=False
                )
            elif field[0] == 'CACHE_ENABLED' or field[0] == 'CACHE_VALID_DAYS':
                self.fields[name].on_change = lambda _: self.save(
                    settings_file=setting_file2,
                    show_dialog=False
                )
        self.settings_file = self.settings_file[0]

    def did_mount(self):
        # Reset Index
        settings_navrail.selected_index = 0
        settings_navrail.update()

        return super().did_mount()


class SupplierSettingsView(SettingsView):
    '''Supplier settings view'''

    title = 'Supplier Settings'
    route = '/settings/supplier'

    def __init__(self, page: ft.Page):
        super().__init__(page)

    def save_s(self, e: ft.ControlEvent, supplier: str, show_dialog=True):
        '''Save supplier API settings'''
        if supplier == 'Digi-Key':
            from ...search import digikey_api
            # Load settings from file
            settings_from_file = config_interface.load_file(global_settings.CONFIG_DIGIKEY_API)
            # Update settings values
            updated_settings = {
                'DIGIKEY_CLIENT_ID': SETTINGS[self.title][supplier]['Client ID'][1].value,
                'DIGIKEY_CLIENT_SECRET': SETTINGS[self.title][supplier]['Client Secret'][1].value,
            }
            digikey_settings = {**settings_from_file, **updated_settings}
            config_interface.dump_file(digikey_settings, global_settings.CONFIG_DIGIKEY_API)
            digikey_api.setup_environment(force=True)
        elif supplier == 'Mouser':
            from ...search import mouser_api
            # Load settings from file
            settings_from_file = config_interface.load_file(global_settings.CONFIG_MOUSER_API)
            # Update settings values
            updated_settings = {
                'MOUSER_PART_API_KEY': SETTINGS[self.title][supplier]['Part API Key'][1].value,
            }
            mouser_settings = {**settings_from_file, **updated_settings}
            config_interface.dump_file(mouser_settings, global_settings.CONFIG_MOUSER_API)
            mouser_api.setup_environment(force=True)
        elif supplier == 'Element14' or supplier == 'Farnell' or supplier == 'Newark':
            # Load settings from file
            settings_from_file = config_interface.load_file(global_settings.CONFIG_ELEMENT14_API)
            # Update settings values
            updated_settings = {
                'ELEMENT14_PRODUCT_SEARCH_API_KEY': SETTINGS[self.title][supplier]['Product Search API Key (Element14)'][1].value,
                f'{supplier.upper()}_STORE': SETTINGS[self.title][supplier][f'{supplier} Store'][1].value,
            }
            element14_settings = {**settings_from_file, **updated_settings}
            config_interface.dump_file(element14_settings, global_settings.CONFIG_ELEMENT14_API)
        elif supplier == 'LCSC':
            # Load settings from file
            settings_from_file = config_interface.load_file(global_settings.CONFIG_LCSC_API)
            # Update settings values
            updated_settings = {
                'LCSC_API_URL': SETTINGS[self.title][supplier]['API URL'][1].value,
            }
            lcsc_settings = {**settings_from_file, **updated_settings}
            config_interface.dump_file(lcsc_settings, global_settings.CONFIG_LCSC_API)
            
        if show_dialog:
            self.show_dialog(
                d_type=DialogType.VALID,
                message=f'{supplier} Settings successfully saved',
            )

    def test_s(self, e: ft.ControlEvent, supplier: str):
        '''Test supplier API settings'''
        self.save_s(e, supplier, show_dialog=False)

        result = False
        if supplier == 'Digi-Key':
            from ...search import digikey_api
            result = digikey_api.test_api()
        elif supplier == 'Mouser':
            from ...search import mouser_api
            result = mouser_api.test_api()
        elif supplier == 'Element14' or supplier == 'Farnell' or supplier == 'Newark':
            from ...search import element14_api
            result = element14_api.test_api()
        elif supplier == 'LCSC':
            from ...search import lcsc_api
            result = lcsc_api.test_api()

        if result:
            self.show_dialog(
                d_type=DialogType.VALID,
                message=f'Successfully connected to {supplier} API'
            )
        else:
            self.show_dialog(
                d_type=DialogType.ERROR,
                message=f'ERROR: Failed to connect to {supplier} API. Verify the {supplier} credentials and re-try'
            )

    def build_column(self):
        # Title and separator
        self.column = ft.Column(
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
                            on_click=lambda e, s=supplier: self.test_s(e, supplier=s),
                        ),
                        ft.ElevatedButton(
                            'Save',
                            width=GUI_PARAMS['button_width'],
                            height=GUI_PARAMS['button_height'],
                            icon=ft.icons.SAVE_OUTLINED,
                            on_click=lambda e, s=supplier: self.save_s(e, supplier=s),
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

        self.column.controls.append(supplier_tabs)


class InvenTreeSettingsView(SettingsView):
    '''InvenTree settings view'''

    title = 'InvenTree Settings'
    route = '/settings/inventree'
    settings_file = [
        global_settings.INVENTREE_CONFIG,
        global_settings.CONFIG_IPN_PATH,
    ]

    def save(self, file=None, dialog=True):
        if file is None:
            # Save to InvenTree file
            config_interface.save_inventree_user_settings(
                enable=global_settings.ENABLE_INVENTREE,
                server=SETTINGS[self.title]['Server Address'][1].value,
                username=SETTINGS[self.title]['Username'][1].value,
                password=SETTINGS[self.title]['Password'][1].value,
                user_config_path=self.settings_file[0]
            )
            # Alert user
            if dialog:
                self.show_dialog(
                    d_type=DialogType.VALID,
                    message=f'{self.title} successfully saved',
                )
        else:
            super().save(settings_file=file, show_dialog=dialog)

        # Reload InvenTree settings
        global_settings.load_inventree_settings()
        # Reload IPN settings
        global_settings.load_ipn_settings()

    def test(self):
        from ...database import inventree_interface
        self.save(dialog=False)
        connection = inventree_interface.connect_to_server()
        if connection:
            self.show_dialog(
                d_type=DialogType.VALID,
                message='Sucessfully connected to InvenTree server',
            )
        else:
            self.show_dialog(
                d_type=DialogType.ERROR,
                message='Failed to connect to InvenTree server. Check InvenTree credentials are correct and server is running',
            )

    def __init__(self, page: ft.Page):
        # Load InvenTree and IPN settings
        self.settings = {
            **config_interface.load_inventree_user_settings(self.settings_file[0]),
            **config_interface.load_file(self.settings_file[1]),
        }
        super().__init__(page)

    def build_column(self):
        ipn_file = self.settings_file[1]
        ipn_fields = [
            'IPN: Enable Prefix',
            'IPN: Prefix',
            'IPN: Length of Unique ID',
            'IPN: Enable Suffix',
            'IPN: Suffix',
        ]
        super().build_column(ignore=ipn_fields)

        ipn_fields_ref = ft.Ref[ft.Row]()
        ipn_fields_col = ft.Column()
        for name in ipn_fields:
            SETTINGS[self.title][name][1].label = name
            SETTINGS[self.title][name][1].on_change = lambda _: self.save(
                file=ipn_file,
                dialog=False,
            )
            ipn_fields_col.controls.append(
                ft.Row([SETTINGS[self.title][name][1]])
            )
        # Add before Save/Test buttons
        self.column.controls.insert(
            -1,
            ft.Row(
                ref=ipn_fields_ref,
                controls=[ipn_fields_col]
            )
        )

        # Also update main IPN switch
        main_control = 'Enable Internal Part Number (IPN)'
        SETTINGS[self.title][main_control][1].refs = [ipn_fields_ref]
        SETTINGS[self.title][main_control][1].on_change = lambda _: self.save(
            file=ipn_file,
            dialog=False,
        )

        for name in ['IPN: Enable Prefix', 'IPN: Enable Suffix']:
            ref = ft.Ref[ft.TextField]()
            ref.current = SETTINGS[self.title][name.replace('Enable ', '')][1]
            SETTINGS[self.title][name][1].refs = [ref]

        # Enable scrolling
        self.column.scroll = ft.ScrollMode.ADAPTIVE
        # self.column.expand = 0
        print(self.column)


class KiCadSettingsView(SettingsView):
    '''KiCad settings view'''

    title = 'KiCad Settings'
    route = '/settings/kicad'
    settings = global_settings.KICAD_SETTINGS
    settings_file = global_settings.KICAD_CONFIG_PATHS
