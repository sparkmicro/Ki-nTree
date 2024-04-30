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
for supplier, data in global_settings.CONFIG_SUPPLIERS.items():
    supplier_settings[supplier] = {}

    # Add enable
    supplier_settings[supplier]['Enable'] = [
        data['enable'],
        ft.Switch(),
        None,
    ]

    # Add supplier name
    supplier_settings[supplier]['InvenTree Name'] = [
        data['name'],
        ft.TextField(),
        None,
    ]

    # Add API fields
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
    elif supplier == 'TME':
        tme_api_settings = config_interface.load_file(global_settings.CONFIG_TME_API)
        supplier_settings[supplier]['API Token'] = [
            tme_api_settings['TME_API_TOKEN'],
            ft.TextField(),
            None,
        ]
        supplier_settings[supplier]['API Secret'] = [
            tme_api_settings['TME_API_SECRET'],
            ft.TextField(),
            None,
        ]
        supplier_settings[supplier]['API Country'] = [
            tme_api_settings['TME_API_COUNTRY'],
            ft.TextField(),
            None,
        ]
        supplier_settings[supplier]['API Language'] = [
            tme_api_settings['TME_API_LANGUAGE'],
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
        'Save Datasheets to Local Folder': [
            'DATASHEET_SAVE_ENABLED',
            SwitchWithRefs(),
            False,  # Browse enabled
        ],
        'Datasheet Folder': [
            'DATASHEET_SAVE_PATH',
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
        'Password or Token': [
            'PASSWORD',
            ft.TextField(),
            False,  # Browse disabled
        ],
        'Enable Proxy Support': [
            'ENABLE_PROXY',
            SwitchWithRefs(),
            False,  # Browse disabled
        ],
        'Proxy': [
            'PROXY',
            ft.TextField(),
            False,  # Browse disabled
        ],
        'Upload Datasheets to InvenTree': [
            'DATASHEET_UPLOAD',
            SwitchWithRefs(),
            False,  # Browse enabled
        ],
        'Upload Pricing Data to InvenTree': [
            'PRICING_UPLOAD',
            SwitchWithRefs(),
            False,  # Browse enabled
        ],
        'Default Part Revision': [
            'INVENTREE_DEFAULT_REV',
            ft.TextField(),
            False,  # Browse disabled
        ],
        'Enable Internal Part Number (IPN)': [
            'IPN_ENABLE_CREATE',
            SwitchWithRefs(),
            False,  # Browse disabled
        ],
        'Use Manufacturer Part Number as IPN': [
            'IPN_USE_MANUFACTURER_PART_NUMBER',
            SwitchWithRefs(reverse_dir=True),
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
        'IPN: Enable Category Codes': [
            'IPN_CATEGORY_CODE',
            ft.Switch(),
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

# Navigation indexes (settings)
NAV_BAR_INDEX = {
    0: '/settings/user',
    1: '/settings/supplier',
    2: '/settings/inventree',
    3: '/settings/kicad',
}


class SettingsView(CommonView):
    '''Main settings view'''

    title = 'Settings'
    route = '/settings'
    settings = None
    settings_file = None
    dialog = None

    def __init__(self, page: ft.Page):
        # Load setting fields
        self.fields = {}
        for field_name, field_data in SETTINGS.get(self.title, {}).items():
            if isinstance(field_data, list) and field_data[0] is not None:
                self.fields[field_name] = field_data[1]
                self.fields[field_name].value = self.settings[field_data[0]]

        # Init view
        super().__init__(page=page, appbar=settings_appbar, navigation_rail=settings_navrail)

        # Update navigation rail
        self.navigation_rail.on_change = self.nav_rail_redirect

    def nav_rail_redirect(self, e):
        self._page.go(NAV_BAR_INDEX[e.control.selected_index])
    
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
            self._page.update()

    def path_picker(self, e: ft.ControlEvent, title: str):
        '''Let user browse to a system path'''
        if self._page.overlay:
            self._page.overlay.pop()
        path_picker = ft.FilePicker(on_result=self.on_dialog_result)
        self._page.overlay.append(path_picker)
        self._page.update()
        if self.fields[title].value:
            path_picker.get_directory_path(dialog_title=title, initial_directory=self.fields[title].value)
        else:
            path_picker.get_directory_path(dialog_title=title, initial_directory=global_settings.HOME_DIR)

    def init_column(self) -> ft.Column:
        return ft.Column(
            controls=[
                ft.Text(self.title, style="bodyMedium"),
                ft.Row(),
            ],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )

    def update_field(self, name, field, column):
        if isinstance(field, ft.TextField):
            field_predefined = bool(field.width)
            if not field_predefined:
                field.label = name
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
                if SETTINGS[self.title][name][2]:
                    field_row.controls.append(
                        ft.ElevatedButton(
                            'Browse',
                            width=GUI_PARAMS['button_width'],
                            height=48,
                            on_click=lambda e, t=name: self.path_picker(e, title=t)
                        ),
                    )
                column.controls.extend(
                    [
                        field_row,
                        ft.Row(height=GUI_PARAMS['textfield_space_after']),
                    ]
                )
        elif isinstance(field, ft.Text):
            field.value = name
            field_row = ft.Row(
                controls=[
                    field,
                ]
            )
            column.controls.append(field_row)
            column.controls.append(ft.Divider())
        elif isinstance(field, ft.TextButton):
            column.controls.append(
                ft.ElevatedButton(
                    name,
                    width=GUI_PARAMS['button_width'] * 2,
                    height=GUI_PARAMS['button_height'],
                    icon=ft.icons.CHECK_OUTLINED,
                    on_click=lambda e, s=name: self.test_s(e, s=s)
                ),
            )
        elif isinstance(field, ft.Dropdown):
            field.on_change = lambda _: self.save()
            column.controls.append(
                field,
            )
        elif isinstance(field, ft.Switch) or isinstance(field, SwitchWithRefs):
            if 'proxy' in name.lower():
                field.on_change = lambda _: None
            else:
                field.on_change = lambda _: self.save()
            field.label = name
            column.controls.append(
                field,
            )

    def add_buttons(self, column, test=False) -> ft.Row:
        test_save_buttons = ft.Row()
        if test:
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
        column.controls.append(test_save_buttons)

    def build_column(self, ignore=[]):
        # Header
        self.column = self.init_column()

        # Fields
        for name, field in self.fields.items():
            if name not in ignore:
                self.update_field(name, field, self.column)

        # Test and Save buttons
        enable_test = bool(list(SETTINGS[self.title])[-1] == 'Test')
        self.add_buttons(self.column, test=enable_test)

    def did_mount(self):
        handle_transition(self._page, transition=False, timeout=0.05)
        return super().did_mount()
    

class PathSettingsView(SettingsView):
    '''Template View for Path Setters'''

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.dialog = self.build_dialog()

    def build_dialog(self):
        return ft.Banner(
            bgcolor=ft.colors.AMBER_100,
            leading=ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color=ft.colors.AMBER, size=GUI_PARAMS['icon_size']),
            content=ft.Text(f'Restart Ki-nTree to load the new {self.title}', weight=ft.FontWeight.BOLD),
            actions=[
                ft.TextButton('Discard', on_click=lambda _: self.show_dialog(open=False)),
            ],
        )
    
    def show_dialog(self, d_type=None, message=None, snackbar=False, open=True):
        return super().show_dialog(d_type, message, snackbar, open)


class UserSettingsView(PathSettingsView):
    '''User settings view'''

    title = 'User Settings'
    route = '/settings/user'
    settings = {
        **global_settings.USER_SETTINGS,
        **{
            'DATASHEET_SAVE_ENABLED': global_settings.DATASHEET_SAVE_ENABLED,
            'DATASHEET_SAVE_PATH': global_settings.DATASHEET_SAVE_PATH,
            'AUTOMATIC_BROWSER_OPEN': global_settings.AUTOMATIC_BROWSER_OPEN
        },
        **{
            'CACHE_ENABLED': global_settings.CACHE_ENABLED,
            'CACHE_VALID_DAYS': global_settings.CACHE_VALID_DAYS
        },
    }
    settings_file_list = [
        global_settings.USER_CONFIG_FILE,
        global_settings.CONFIG_GENERAL_PATH,
        global_settings.CONFIG_SEARCH_API_PATH,
    ]

    def save(self):
        # Save all settings
        for sf in self.settings_file_list:
            super().save(settings_file=sf, show_dialog=True)
    
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
        # Header
        self.column = self.init_column()
        # Fields
        for name, field in self.fields.items():
            self.update_field(name, field, self.column)
    
        # Create refs
        datasheet_row_ref = ft.Ref[ft.Row]()
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
        self.column.controls.append(cache_row)
        # Add cache row to switch refs
        SETTINGS[self.title]['Enable Supplier Search Cache'][1].refs = [cache_row_ref]

        for name, field in SETTINGS[self.title].items():
            if field[0] in ['AUTOMATIC_BROWSER_OPEN', 'DATASHEET_SAVE_ENABLED', 'DATASHEET_SAVE_PATH', 'DATASHEET_INVENTREE_ENABLED']:
                self.fields[name].on_change = lambda _: self.save()
            elif field[0] in ['CACHE_ENABLED', 'CACHE_VALID_DAYS']:
                self.fields[name].on_change = lambda _: self.save()
        self.settings_file = self.settings_file_list[0]

        # Update datasheet ref
        for idx, field in enumerate(self.column.controls):
            if isinstance(field, SwitchWithRefs):
                if field.label == 'Save Datasheets to Local Folder':
                    datasheet_row_ref.current = self.column.controls[idx + 1]
                    SETTINGS[self.title]['Save Datasheets to Local Folder'][1].refs = [datasheet_row_ref]
        
        # Save button
        self.add_buttons(self.column, test=False)

    def did_mount(self):
        try:
            # Reset Index
            self.navigation_rail.selected_index = 0
            self.navigation_rail.update()
        except AssertionError:
            pass
        return super().did_mount()


class SupplierSettingsView(SettingsView):
    '''Supplier settings view'''

    title = 'Supplier Settings'
    route = '/settings/supplier'
    settings = global_settings.CONFIG_SUPPLIERS
    settings_file = global_settings.CONFIG_SUPPLIERS_PATH

    def __init__(self, page: ft.Page):
        super().__init__(page)

    def save_s(self, e: ft.ControlEvent, supplier: str, show_dialog=True):
        '''Save supplier settings'''

        # Enable/Name settings
        supplier_settings = self.settings
        enable_name = {
            'enable': SETTINGS[self.title][supplier]['Enable'][1].value,
            'name': SETTINGS[self.title][supplier]['InvenTree Name'][1].value,
        }
        supplier_settings.update({supplier: enable_name})
        config_interface.dump_file(supplier_settings, self.settings_file)
        # Update suppliers
        global_settings.load_suppliers()
        
        # API settings
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
        elif supplier == 'TME':
            # Load settings from file
            settings_from_file = config_interface.load_file(global_settings.CONFIG_TME_API)
            # Update settings values
            updated_settings = {
                'TME_API_TOKEN': SETTINGS[self.title][supplier]['API Token'][1].value,
                'TME_API_SECRET': SETTINGS[self.title][supplier]['API Secret'][1].value,
                'TME_API_COUNTRY': SETTINGS[self.title][supplier]['API Country'][1].value,
                'TME_API_LANGUAGE': SETTINGS[self.title][supplier]['API Language'][1].value,
            }
            tme_settings = {**settings_from_file, **updated_settings}
            config_interface.dump_file(tme_settings, global_settings.CONFIG_TME_API)
            
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
        elif supplier == 'TME':
            from ...search import tme_api
            result = tme_api.test_api()

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
        # Header
        self.column = self.init_column()
        
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
        address = SETTINGS[self.title]['Server Address'][1].value
        proxy = SETTINGS[self.title]['Proxy'][1].value
        enable_proxy = SETTINGS[self.title]['Enable Proxy Support'][1].value
        if not enable_proxy:
            proxies = None
        elif address.startswith('https'):
            proxies = {'https': proxy}
        else:
            proxies = {'http': proxy}
        if file is None:
            # Save to InvenTree file
            config_interface.save_inventree_user_settings(
                enable=global_settings.ENABLE_INVENTREE,
                server=address,
                username=SETTINGS[self.title]['Username'][1].value,
                password=SETTINGS[self.title]['Password or Token'][1].value,
                enable_proxy=enable_proxy,
                proxies=proxies,
                datasheet_upload=SETTINGS[self.title][
                    'Upload Datasheets to InvenTree'][1].value,
                pricing_upload=SETTINGS[self.title][
                    'Upload Pricing Data to InvenTree'][1].value,
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
            'Default Part Revision',
            'Enable Internal Part Number (IPN)',
            'Use Manufacturer Part Number as IPN',
            'IPN: Enable Prefix',
            'IPN: Prefix',
            'IPN: Enable Category Codes',
            'IPN: Length of Unique ID',
            'IPN: Enable Suffix',
            'IPN: Suffix',
        ]

        # Tabs
        inventree_tabs = ft.Tabs(
            selected_index=0,
            animation_duration=10,
            expand=1,
            tabs=[],
        )
        
        # Build server tab content
        server_col = ft.Column([ft.Row(height=10)])
        for name, field in self.fields.items():
            if name not in ipn_fields:
                self.update_field(name, field, server_col)
        self.add_buttons(server_col, test=True)

        # Add InvenTree server tab
        inventree_tabs.tabs.append(
            ft.Tab(
                tab_content=ft.Text('Server', size=16),
                content=ft.Container(
                    server_col,
                )
            )
        )

        # Link Proxy Switch to the input field
        ref = ft.Ref[ft.TextField]()
        ref.current = SETTINGS[self.title]['Proxy'][1]
        SETTINGS[self.title]['Enable Proxy Support'][1].refs = [ref]

        # Create IPN fields
        ipn_fields_ref = ft.Ref[ft.Row]()
        ipn_fields_col = ft.Column(
            ref=ipn_fields_ref,
            controls=[],
        )
        for name in ipn_fields:
            SETTINGS[self.title][name][1].label = name
            SETTINGS[self.title][name][1].on_change = lambda _: self.save(
                file=ipn_file,
                dialog=False,
            )
            if name.startswith('IPN: '):
                ipn_fields_col.controls.append(
                    ft.Row([SETTINGS[self.title][name][1]])
                )
        ipn_manufacturer_part_number_ref = ft.Ref[ft.Row]()
        ipn_manufacturer_part_number_col = ft.Column(
            ref=ipn_manufacturer_part_number_ref,
            controls=[
                ft.Row([SETTINGS[self.title]['Use Manufacturer Part Number as IPN'][1]]),
                ft.Row([ipn_fields_col]),
            ],
        )
        
        # Build IPN tab column
        ipn_tab_col = ft.Column(
            [
                ft.Row(height=10),
                ft.Row([SETTINGS[self.title]['Default Part Revision'][1]]),
                ft.Row([SETTINGS[self.title]['Enable Internal Part Number (IPN)'][1]]),
                ft.Row([ipn_manufacturer_part_number_col]),
            ]
        )
    
        # Link main IPN switch to corresponding fields
        main_control = 'Enable Internal Part Number (IPN)'
        secondary_control = 'Use Manufacturer Part Number as IPN'
        SETTINGS[self.title][main_control][1].refs = [ipn_manufacturer_part_number_ref]
        SETTINGS[self.title][main_control][1].on_change = lambda _: self.save(
            file=ipn_file,
            dialog=False,
        )

        # Link Manufacturer Part Number switch to corresponding fields
        SETTINGS[self.title][secondary_control][1].refs = [ipn_fields_ref]
        SETTINGS[self.title][secondary_control][1].on_change = lambda _: self.save(
            file=ipn_file,
            dialog=False,
        )

        # Link prefix/suffix switches to corresponding fields
        for name in ['IPN: Enable Prefix', 'IPN: Enable Suffix']:
            ref = ft.Ref[ft.TextField]()
            ref.current = SETTINGS[self.title][name.replace('Enable ', '')][1]
            SETTINGS[self.title][name][1].refs = [ref]

        # Add IPN tab
        inventree_tabs.tabs.append(
            ft.Tab(
                tab_content=ft.Text('Internal Part Number', size=16),
                content=ft.Container(
                    ipn_tab_col,
                )
            )
        )

        # Build column
        self.column = self.init_column()
        # Add tabs
        self.column.controls.append(inventree_tabs)


class KiCadSettingsView(PathSettingsView):
    '''KiCad settings view'''

    title = 'KiCad Settings'
    route = '/settings/kicad'
    settings = global_settings.KICAD_SETTINGS
    settings_file = global_settings.KICAD_CONFIG_PATHS
