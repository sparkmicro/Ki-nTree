import os
import flet as ft

# Version
from ... import __version__
# Common view
from .common import GUI_PARAMS
from .common import data_from_views, CommonView, DropdownWithSearch, Collapsible, MenuButton
from ...common.tools import cprint
# Settings
from ...config import settings, config_interface
# InvenTree
from ...database import inventree_interface

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
NAV_BAR_INDEX = {}
for view in MAIN_NAVIGATION.values():
    NAV_BAR_INDEX[view['nav_index']] = view['route']

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

        # Update navigation rail
        if not self.navigation_rail.on_change:
            self.navigation_rail.on_change = lambda e: self.page.go(NAV_BAR_INDEX[e.control.selected_index])

        # Init data
        self.data = {}

        # Process enable switch
        if 'enable' in self.fields:
            self.fields['enable'].on_change = self.process_enable

    def process_enable(self, e):
        disable = True
        if e.data.lower() == 'true':
            disable = False
        for name, field in self.fields.items():
            if name != 'enable':
                field.disabled = disable
                field.update()
        self.push_data(e)

    def push_data(self, e=None):
        for key, field in self.fields.items():
            try:
                self.data[key] = field.value
            except AttributeError:
                pass
        data_from_views[self.title] = self.data


class PartSearchView(MainView):
    '''Part search view'''

    title = 'Part Search'
    add_to = {'inventree': False, 'kicad': False}

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
        'supplier': ft.Dropdown(label="Supplier", dense=True, width=200),
        'search_button': ft.ElevatedButton('Find', icon=ft.icons.SEARCH),
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
            text_field = ft.TextField(label=label, dense=True, hint_text=label, disabled=True, expand=True, on_change=self.push_data)
            self.column.controls.append(ft.Row(controls=[text_field]))
            self.fields['search_form'][field] = text_field

    def enable_search_fields(self):
        for form_field in self.fields['search_form'].values():
            form_field.disabled = False
        self.page.update()
        return

    def run_search(self):
        # Validate form
        if bool(self.fields['part_number'].value) !=  bool(self.fields['supplier'].value):
            if not self.fields['part_number'].value:
                self.build_snackbar(dialog_success=False, dialog_text='Missing Part Number')
            else:
                self.build_snackbar(dialog_success=False, dialog_text='Missing Supplier')
            self.show_dialog()
        else:
            self.page.splash.visible = True
            self.page.update()

            if not self.fields['part_number'].value and not self.fields['supplier'].value:
                self.enable_search_fields()
            else:
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
        for name, field in self.fields.items():
            if type(field) == ft.ElevatedButton:
                field.width = 100
                field.height = 48
            if name == 'search_button':
                field.on_click = lambda e: self.run_search()

        return ft.Column(
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


class InventreeView(MainView):
    '''InvenTree categories view'''

    title = 'InvenTree'
    fields = {
        'enable': ft.Switch(label='InvenTree', value=settings.ENABLE_INVENTREE, on_change=None),
        # 'alternate': ft.Switch(label='Alternate', value=False, disabled=True),
        'load_categories': ft.ElevatedButton('Reload InvenTree Categories', height=48, icon=ft.icons.REPLAY),
        'Category': DropdownWithSearch(label='Category', dr_width=400, sr_width=400, dense=True, options=[]),
    }

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page)

    def load_categories(self, e):
        print('Loading categories from InvenTree...')

    def build_column(self):
        def build_tree(tree, left_to_go, level):
            try:
                last_entry = f' {tree[-1].replace("-", "").replace(" ","")}/'
            except IndexError:
                last_entry = f''
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

        self.fields['load_categories'].on_click = self.load_categories

        return ft.Column(
            controls=[
                ft.Row(),
                ft.Row(
                    [
                        self.fields['enable'],
                        # self.fields['alternate'],
                    ]
                ),
                self.fields['Category'],
                ft.Row(
                    [
                        self.fields['load_categories'],
                    ]
                ),
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

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page)

    def get_footprint_libraries(self) -> dict:
        footprint_libraries = {}
        for folder in sorted(os.listdir(settings.KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'])):
            if os.path.isdir(os.path.join(settings.KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'], folder)):
                footprint_libraries[folder.replace('.pretty', '')] = os.path.join(settings.KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'], folder)
        return footprint_libraries

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
        import os
        found_libraries = []
        if type == 'symbol':
            found_libraries = [file.replace('.kicad_sym', '') for file in sorted(os.listdir(settings.KICAD_SETTINGS['KICAD_SYMBOLS_PATH']))
                                if file.endswith('.kicad_sym')]
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
        
        options = [ft.dropdown.Option(lib_name) for lib_name in found_libraries]
        return options

    def build_column(self):
        column = ft.Column(
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
        
        column.controls.extend(kicad_inputs)
        return column


class CreateView(MainView):
    '''Create view'''

    title = 'Create'
    fields = {
        'inventree_progress': ft.ProgressBar(height=(GUI_PARAMS['button_height'] / 2), width=400, value=0),
        'kicad_progress': ft.ProgressBar(height=(GUI_PARAMS['button_height'] / 2), width=400, value=0),
    }

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page)

    def load_data(self, e=None):
        import time
        cprint(data_from_views)

        for i in range(0, 21):
            progress_value = i * 0.05
            self.fields['inventree_progress'].value = progress_value
            self.fields['kicad_progress'].value = progress_value
            time.sleep(0.1)
            self.page.update()

    def build_column(self):
        return ft.Column(
            controls=[
                ft.Row(),
                ft.ElevatedButton(
                    'Create Part',
                    height=GUI_PARAMS['button_height'],
                    width=GUI_PARAMS['button_width'] * 2,
                    on_click=self.load_data,
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.icons.INVENTORY_2, size=(GUI_PARAMS['icon_size'] / 2)),
                        ft.Text('InvenTree', size=GUI_PARAMS['text_size'], weight=ft.FontWeight.BOLD, width=100),
                        self.fields['inventree_progress'],
                    ],
                ),
                ft.Row(
                    controls=[
                        ft.Icon(ft.icons.SETTINGS_INPUT_COMPONENT, size=(GUI_PARAMS['icon_size'] / 2)),
                        ft.Text('KiCad', size=GUI_PARAMS['text_size'], weight=ft.FontWeight.BOLD, width=100),
                        self.fields['kicad_progress'],
                    ],
                ),
            ],
        )
