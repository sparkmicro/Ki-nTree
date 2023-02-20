import os
import copy
import flet as ft

# Version
from ... import __version__
# Common view
from .common import GUI_PARAMS, data_from_views
from .common import CommonView, DropdownWithSearch
from ...common.tools import cprint
# Settings
from ...common import progress
from ...config import settings, config_interface
# InvenTree
from ...database import inventree_interface
# KiCad
from ...kicad import kicad_interface

# Main AppBar
main_appbar = ft.AppBar(
    leading=ft.Icon(ft.icons.DOUBLE_ARROW),
    leading_width=40,
    title=ft.Text(f'Ki-nTree | {__version__}'),
    center_title=False,
    bgcolor=ft.colors.SURFACE_VARIANT,
    actions=[],
)

# Navigation Controls
MAIN_NAVIGATION = {
    'Part Search': {
        'nav_index': 0,
        'route': '/main/part'
    },
    'InvenTree': {
        'nav_index': 1,
        'route': '/main/inventree'
    },
    'KiCad': {
        'nav_index': 2,
        'route': '/main/kicad'
    },
    'Create': {
        'nav_index': 3,
        'route': '/main/create'
    },
}

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
            label_content=ft.Text("Part Search", size=16),
            padding=10,
        ),
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.INVENTORY_2_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.INVENTORY_2, size=40),
            label_content=ft.Text("InvenTree", size=16),
            padding=10,
        ),
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT, size=40),
            label_content=ft.Text("KiCad", size=16),
            padding=10,
        ),
        ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.CREATE_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.CREATE, size=40),
            label_content=ft.Text("Create", size=16),
            padding=10,
        ),
    ],
    on_change=None,
)


class MainView(CommonView):
    '''Main view'''

    route = None
    data = None

    def __init__(self, page: ft.Page):
        # Get route
        self.route = MAIN_NAVIGATION[self.title].get('route', '/')

        # Init view
        super().__init__(page=page, appbar=main_appbar, navigation_rail=main_navrail)

        # Update application bar
        if not self.appbar.actions:
            self.appbar.actions.append(ft.IconButton(ft.icons.SETTINGS, on_click=lambda e: self.page.go('/settings')))

        # Load navigation indexes
        self.NAV_BAR_INDEX = {}
        for view in MAIN_NAVIGATION.values():
            self.NAV_BAR_INDEX[view['nav_index']] = view['route']

        # Update navigation rail
        if not self.navigation_rail.on_change:
            self.navigation_rail.on_change = lambda e: self.page.go(self.NAV_BAR_INDEX[e.control.selected_index])

        # Init data
        self.data = {}

        # Process enable switch
        if 'enable' in self.fields:
            self.fields['enable'].on_change = self.process_enable

        # Add floating button to reset view
        self.floating_action_button = ft.FloatingActionButton(
            icon=ft.icons.REPLAY, on_click=self.reset_view,
        )

    def reset_view(self, e, ignore=['enable']):
        def reset_field(field):
            if type(field) is ft.ProgressBar:
                field.value = 0
            else:
                field.value = None
            field.update()

        for name, field in self.fields.items():
            if type(field) == dict:
                for key, value in field.items():
                    value.disabled = True
                    reset_field(value)
            else:
                if name not in ignore:
                    reset_field(field)
        # Clear data
        self.push_data()

    def get_footprint_libraries(self) -> dict:
        footprint_libraries = {}
        for folder in sorted(os.listdir(settings.KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'])):
            if os.path.isdir(os.path.join(settings.KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'], folder)):
                footprint_libraries[folder.replace('.pretty', '')] = os.path.join(settings.KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'], folder)
        return footprint_libraries
    
    def find_libraries(self, type: str) -> list:
        found_libraries = []
        if type == 'symbol':
            found_libraries = [
                file.replace('.kicad_sym', '')
                for file in sorted(os.listdir(settings.KICAD_SETTINGS['KICAD_SYMBOLS_PATH']))
                if file.endswith('.kicad_sym')
            ]
        elif type == 'template':
            templates = config_interface.load_templates_paths(
                user_config_path=settings.KICAD_CONFIG_CATEGORY_MAP,
                template_path=settings.KICAD_SETTINGS['KICAD_TEMPLATES_PATH']
            )
            for key in templates:
                for template in templates[key]:
                    found_libraries.append(f'{key}/{template}')
        elif type == 'footprint':
            found_libraries = list(self.get_footprint_libraries().keys())
        return found_libraries

    def show_error_dialog(self, message):
        self.build_snackbar(False, message)
        self.show_dialog()

    def process_enable(self, e, ignore=['enable']):
        disable = True
        if e.data.lower() == 'true':
            disable = False

        # print(e.control.label, not(disable))
        key = e.control.label.lower()
        settings.set_enable_flag(key, not disable)

        for name, field in self.fields.items():
            if name not in ignore:
                field.disabled = disable
                field.update()
        self.push_data(e)

    def sanitize_data(self):
        return

    def push_data(self, e=None):
        for key, field in self.fields.items():
            try:
                self.data[key] = field.value
            except AttributeError:
                pass
        # Sanitize data before pushing
        self.sanitize_data()
        # Push
        data_from_views[self.title] = self.data


class PartSearchView(MainView):
    '''Part search view'''

    title = 'Part Search'

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
        'part_number': ft.TextField(
            label="Part Number",
            dense=True,
            hint_text="Part Number",
            width=300,
            expand=True
        ),
        'supplier': ft.Dropdown(
            label="Supplier",
            dense=True,
            width=250
        ),
        'search_button': ft.IconButton(
            icon=ft.icons.SEND,
            icon_color="blue900",
            icon_size=32,
            height=48,
            width=48,
            tooltip="Submit",
        ),
        'search_form': {},
    }

    def enable_search_fields(self):
        for form_field in self.fields['search_form'].values():
            form_field.disabled = False
        self.page.update()
        return

    def run_search(self, e):
        # Validate form
        if bool(self.fields['part_number'].value) != bool(self.fields['supplier'].value):
            if not self.fields['part_number'].value:
                self.build_snackbar(dialog_success=False, dialog_text='Missing Part Number')
            else:
                self.build_snackbar(dialog_success=False, dialog_text='Missing Supplier')
            self.show_dialog()
        else:
            self.page.splash.visible = True
            self.page.update()

            if not self.fields['part_number'].value and not self.fields['supplier'].value:
                self.data['custom_part'] = True
                self.enable_search_fields()
            else:
                self.data['custom_part'] = False

                # Supplier search
                part_supplier_info = inventree_interface.supplier_search(
                    self.fields['supplier'].value,
                    self.fields['part_number'].value
                )

                if part_supplier_info:
                    # Translate to user form format
                    part_supplier_form = inventree_interface.translate_supplier_to_form(
                        supplier=self.fields['supplier'].value,
                        part_info=part_supplier_info,
                    )

                if part_supplier_info:
                    for field_idx, field_name in enumerate(self.fields['search_form'].keys()):
                        # print(field_idx, field_name, get_default_search_keys()[field_idx], search_form_field[field_name])
                        try:
                            self.fields['search_form'][field_name].value = part_supplier_form.get(field_name, '')
                        except IndexError:
                            pass
                        # Enable editing
                        self.enable_search_fields()

            # Add to data buffer
            self.push_data()
            self.page.splash.visible = False
            self.page.update()
        return

    def push_data(self, e=None):
        for key, field in self.fields['search_form'].items():
            self.data[key] = field.value
        data_from_views[self.title] = self.data

    def build_column(self):
        # Populate dropdown suppliers
        self.fields['supplier'].options = [ft.dropdown.Option(supplier) for supplier in settings.SUPPORTED_SUPPLIERS_API]
        # Enable search method
        self.fields['search_button'].on_click = self.run_search

        self.column = ft.Column(
            controls=[
                ft.Row(),
                ft.Row(
                    controls=[
                        self.fields['part_number'],
                        self.fields['supplier'],
                        self.fields['search_button'],
                    ],
                ),
                ft.Divider(),
            ],
            alignment=ft.MainAxisAlignment.START,
            scroll=ft.ScrollMode.HIDDEN,
            expand=True,
        )

        # Create search form
        for field in self.search_fields_list:
            label = field.replace('_', ' ').title()
            text_field = ft.TextField(
                label=label,
                dense=True,
                hint_text=label,
                disabled=True,
                expand=True,
                on_change=self.push_data,
            )
            self.column.controls.append(ft.Row([text_field]))
            self.fields['search_form'][field] = text_field


class InventreeView(MainView):
    '''InvenTree categories view'''

    title = 'InvenTree'
    fields = {
        'enable': ft.Switch(label='InvenTree', value=settings.ENABLE_INVENTREE, on_change=None),
        'alternate': ft.Switch(label='Alternate', value=False, disabled=True),
        'load_categories': ft.ElevatedButton('Reload InvenTree Categories', height=36, icon=ft.icons.REPLAY, disabled=True),
        'Category': DropdownWithSearch(label='Category', dr_width=400, sr_width=400, dense=True, options=[]),
    }
    category_separator = '/'

    def clean_category_tree(self, category_tree: str) -> str:
        import re
        find_prefix = re.match(r'^-+ (.+?)$', category_tree)
        if find_prefix:
            return find_prefix.group(1)
        return category_tree

    def clean_split_category_tree(self, category_tree: str) -> list:
        return self.clean_category_tree(category_tree).split(self.category_separator)
    
    def sanitize_data(self):
        category_tree = self.data.get('Category', None)
        if category_tree:
            self.data['Category'] = self.clean_split_category_tree(category_tree)

    def process_enable(self, e, ignore=['enable', 'alternate', 'load_categories']):
        return super().process_enable(e, ignore)

    def reload_categories(self, e):
        # TODO: Implement pulling categories from InvenTree
        print('Loading categories from InvenTree...')

    def build_column(self):
        def build_tree(tree, left_to_go, level):
            try:
                last_entry = f' {self.clean_category_tree(tree[-1])}{self.category_separator}'
            except IndexError:
                last_entry = ''
            if type(left_to_go) == dict:
                for key, value in left_to_go.items():
                    tree.append(f'{"-" * level}{last_entry}{key}')
                    build_tree(tree, value, level + 1)
            elif type(left_to_go) == list:
                for item in left_to_go:
                    tree.append(f'{"-" * level}{last_entry}{item}')
            elif left_to_go is None:
                pass
            return
            
        categories = config_interface.load_file(settings.CONFIG_CATEGORIES).get('CATEGORIES', {})

        inventree_categories = []
        # Build category tree
        build_tree(inventree_categories, categories, 0)

        category_options = [ft.dropdown.Option(category) for category in inventree_categories]
        # Update dropdown
        self.fields['Category'].options = category_options
        self.fields['Category'].on_change = self.push_data

        self.fields['load_categories'].on_click = self.reload_categories

        self.column = ft.Column(
            controls=[
                ft.Row(),
                ft.Row(
                    [
                        self.fields['enable'],
                        self.fields['alternate'],
                        self.fields['load_categories'],
                    ]
                ),
                self.fields['Category'],
            ],
        )


class KicadView(MainView):
    '''KiCad view'''

    title = 'KiCad'
    fields = {
        'enable': ft.Switch(label='KiCad', value=settings.ENABLE_KICAD, on_change=None),
        'Symbol Library': DropdownWithSearch(label='', dr_width=400, sr_width=400, dense=True, options=[]),
        'Symbol Template': DropdownWithSearch(label='', dr_width=400, sr_width=400, dense=True, options=[]),
        'Footprint Library': DropdownWithSearch(label='', dr_width=400, sr_width=400, dense=True, options=[]),
        'Footprint': DropdownWithSearch(label='', dr_width=400, sr_width=400, dense=True, options=[]),
        'New Footprint Name': ft.TextField(label='New Footprint Name', width=400, dense=True),
    }

    def update_footprint_options(self, library: str):
        footprint_options = []
        # Load paths
        footprint_paths = self.get_footprint_libraries()
        # Get path matching selected footprint library
        footprint_lib_path = footprint_paths[library]
        # Load footprints
        footprints = [
            item.replace('.kicad_mod', '')
            for item in sorted(os.listdir(footprint_lib_path))
            if os.path.isfile(os.path.join(footprint_lib_path, item))
        ]
        # Find folder matching value
        for footprint in footprints:
            footprint_options.append(ft.dropdown.Option(footprint))

        return footprint_options

    def push_data(self, e=None, label=None, value=None):
        super().push_data(e)
        if label or e:
            if 'Footprint Library' in [label, e.control.label]:
                if value:
                    selected_footprint_library = value
                else:
                    selected_footprint_library = e.data
                self.fields['Footprint'].options = self.update_footprint_options(selected_footprint_library)
                self.fields['Footprint'].update()

    def build_library_options(self, type: str):
        found_libraries = self.find_libraries(type)
        options = [ft.dropdown.Option(lib_name) for lib_name in found_libraries]
        return options

    def build_column(self):
        self.column = ft.Column(
            controls=[ft.Row()],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
        kicad_inputs = []
        for name, field in self.fields.items():
            field.on_change = self.push_data
            if type(field) == DropdownWithSearch:
                field.label = name
                if name == 'Symbol Library':
                    field.options = self.build_library_options(type='symbol')
                elif name == 'Symbol Template':
                    field.options = self.build_library_options(type='template')
                elif name == 'Footprint Library':
                    field.options = self.build_library_options(type='footprint')

            kicad_inputs.append(field)
        
        self.column.controls.extend(kicad_inputs)


class CreateView(MainView):
    '''Create view'''

    title = 'Create'
    fields = {
        'inventree_progress': ft.ProgressBar(height=32, width=420, value=0),
        'kicad_progress': ft.ProgressBar(height=32, width=420, value=0),
    }
    inventree_progress_row = None
    kicad_progress_row = None

    def create_part(self, e=None):
        # Setup progress bars
        if not settings.ENABLE_INVENTREE:
            self.inventree_progress_row.current.visible = False
        else:
            self.inventree_progress_row.current.visible = True
            # Reset progress bar
            progress.reset_progress_bar(self.fields['inventree_progress'])
        self.inventree_progress_row.current.update()

        if not settings.ENABLE_KICAD:
            self.kicad_progress_row.current.visible = False
        else:
            self.kicad_progress_row.current.visible = True
            # Reset progress bar
            progress.reset_progress_bar(self.fields['kicad_progress'])
        self.kicad_progress_row.current.update()

        if not settings.ENABLE_INVENTREE and not settings.ENABLE_KICAD:
            self.show_error_dialog('Both InvenTree and KiCad are disabled (nothing to create)')

        # print('data_from_views='); cprint(data_from_views)

        # Check data is present
        if not data_from_views.get('Part Search', None):
            self.show_error_dialog('Missing Part Data (nothing to create)')
            return
        
        # Custom part check
        part_info = copy.deepcopy(data_from_views['Part Search'])
        custom = part_info.pop('custom_part')
        
        if not custom:
            # Part number check
            part_number = data_from_views['Part Search'].get('manufacturer_part_number', None)
            if not part_number:
                self.show_error_dialog('Missing Part Number')
                return

        # KiCad data gathering
        symbol = None
        template = None
        footprint = None
        if settings.ENABLE_KICAD:
            # Check data is present
            if not data_from_views.get('KiCad', None):
                self.show_error_dialog('Missing KiCad Data')
                return
            
            # Process symbol
            symbol_lib = data_from_views['KiCad'].get('Symbol Library', None)
            if symbol_lib:
                symbol = f"{symbol_lib}:{part_number}"

            # Process template
            template = data_from_views['KiCad'].get('Symbol Template', None)

            # Process footprint
            footprint_lib = data_from_views['KiCad'].get('Footprint Library', None)
            if footprint_lib:
                if data_from_views['KiCad'].get('New Footprint Name', None):
                    footprint = f"{footprint_lib}:{data_from_views['KiCad']['New Footprint Name']}"
                elif data_from_views['KiCad'].get('Footprint', None):
                    footprint = f"{footprint_lib}:{data_from_views['KiCad']['Footprint']}"
                else:
                    pass
            
            # print(symbol, template, footprint)
            if not symbol or not template or not footprint:
                self.show_error_dialog('Missing KiCad Data')
                return
        
        # InvenTree data processing
        if settings.ENABLE_INVENTREE:
            # Check data is present
            if not data_from_views.get('InvenTree', None):
                self.show_error_dialog('Missing InvenTree Data')
                return
            # Check connection
            if not inventree_interface.connect_to_server():
                self.show_error_dialog('ERROR: Failed to connect to InvenTree server')
                return
            # Check mandatory data
            if not data_from_views['Part Search'].get('name', None):
                self.show_error_dialog('Missing Part Name')
                return
            if not data_from_views['Part Search'].get('description', None):
                self.show_error_dialog('Missing Part Description')
                return
            # Get relevant data
            category_tree = data_from_views['InvenTree'].get('Category', None)
            if not category_tree:
                # Check category is present
                self.show_error_dialog('Missing InvenTree Category')
                return
            
            # Create part
            new_part, part_pk, part_info = inventree_interface.inventree_create(
                part_info=part_info,
                category_tree=category_tree,
                kicad=settings.ENABLE_KICAD,
                symbol=symbol,
                footprint=footprint,
                show_progress=self.fields['inventree_progress'],
                is_custom=custom
            )
            # print(new_part, part_pk)
            # cprint(part_info)

            if part_pk:
                # Update symbol
                if symbol:
                    symbol = f'{symbol.split(":")[0]}:{part_info["IPN"]}'

                if not new_part:
                    self.fields['inventree_progress'].color = "amber"
                    self.fields['inventree_progress'].update()
                # Complete add operation
                self.fields['inventree_progress'].value = progress.MAX_PROGRESS
                self.fields['inventree_progress'].update()
            else:
                self.fields['inventree_progress'].color = "red"
                self.fields['inventree_progress'].update()

        # KiCad data processing
        if settings.ENABLE_KICAD:
            part_info['Symbol'] = symbol
            part_info['Template'] = template.split('/')
            part_info['Footprint'] = footprint

            symbol_library_path = os.path.join(
                settings.KICAD_SETTINGS['KICAD_SYMBOLS_PATH'],
                f'{symbol.split(":")[0]}.kicad_sym',
            )

            # Reset progress
            progress.CREATE_PART_PROGRESS = 0
            # Create part
            kicad_success, kicad_new_part = kicad_interface.inventree_to_kicad(
                part_data=part_info,
                library_path=symbol_library_path,
                show_progress=self.fields['kicad_progress'],
            )
            # print(kicad_success, kicad_new_part)

            # Complete add operation
            if kicad_success:
                if not kicad_new_part:
                    self.fields['kicad_progress'].color = "amber"
                    self.fields['kicad_progress'].update()
                self.fields['kicad_progress'].value = progress.MAX_PROGRESS
                self.fields['kicad_progress'].update()
            else:
                self.fields['kicad_progress'].color = "red"
                self.fields['kicad_progress'].update()
        
        # Final operations
        if settings.ENABLE_INVENTREE:
            if part_info.get('inventree_url', None):
                if settings.AUTOMATIC_BROWSER_OPEN:
                    # Auto-Open Browser Window
                    cprint(
                        f'\n[MAIN]\tOpening URL {part_info["inventree_url"]} in browser',
                        silent=settings.SILENT
                    )
                    try:
                        self.page.launch_url(part_info['inventree_url'])
                    except TypeError:
                        cprint('[INFO]\tError: Failed to open URL', silent=settings.SILENT)
                else:
                    cprint(f'\n[MAIN]\tPart page URL: {part_info["inventree_url"]}', silent=settings.SILENT)

    def build_column(self):
        self.inventree_progress_row = ft.Ref[ft.Row]()
        self.kicad_progress_row = ft.Ref[ft.Row]()

        self.column = ft.Column(
            controls=[
                ft.Row(),
                ft.Text('Progress', style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Row(
                    ref=self.inventree_progress_row,
                    controls=[
                        ft.Icon(ft.icons.INVENTORY_2, size=32),
                        ft.Text('InvenTree', size=20, weight=ft.FontWeight.BOLD, width=120),
                        self.fields['inventree_progress'],
                    ],
                    width=600,
                    visible=settings.ENABLE_INVENTREE,
                ),
                ft.Row(
                    ref=self.kicad_progress_row,
                    controls=[
                        ft.Icon(ft.icons.SETTINGS_INPUT_COMPONENT, size=32),
                        ft.Text('KiCad', size=20, weight=ft.FontWeight.BOLD, width=120),
                        self.fields['kicad_progress'],
                    ],
                    width=600,
                    visible=settings.ENABLE_KICAD,
                ),
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            'Create Part',
                            height=GUI_PARAMS['button_height'],
                            width=GUI_PARAMS['button_width'] * 2,
                            on_click=self.create_part,
                            expand=True,
                        ),
                    ],
                    width=600,
                ),
            ],
        )
