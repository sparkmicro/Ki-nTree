import os
import copy
import flet as ft

# Version
from ... import __version__
# Common view
from .common import GUI_PARAMS, data_from_views
from .common import DialogType
from .common import CommonView
from .common import DropdownWithSearch, SwitchWithRefs
from .common import handle_transition
# Tools
from ...common.tools import cprint
# Settings
from ...common import progress
from ...config import settings, config_interface
# InvenTree
from ...database import inventree_interface
# KiCad
from ...kicad import kicad_interface
# SnapEDA
from ...search import snapeda_api

# Main AppBar
main_appbar = ft.AppBar(
    # leading=ft.Icon(ft.icons.DOUBLE_ARROW),
    leading=ft.Container(
        content=ft.Image(
            src=os.path.join(settings.PROJECT_DIR, 'logo.png'),
            fit=ft.ImageFit.CONTAIN,
        ),
        padding=ft.padding.only(left=10),
        expand=True,
    ),
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
            icon_content=ft.Icon(name=ft.icons.SCREEN_SEARCH_DESKTOP_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.SCREEN_SEARCH_DESKTOP_SHARP, size=40),
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
            icon_content=ft.Icon(name=ft.icons.BUILD_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.BUILD, size=40),
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
            self.appbar.actions.append(
                ft.IconButton(
                    ft.icons.SETTINGS,
                    on_click=self.call_settings,
                )
            )

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

    def call_settings(self, e):
        handle_transition(self.page, transition=True)
        self.page.go('/settings')

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

    def process_enable(self, e, value=None, ignore=['enable']):
        disabled = False
        if e.data.lower() == 'false':
            disabled = True

        # Overwrite with value
        if value is not None:
            disabled = not value

        # print(e.control.label, not disabled)
        key = e.control.label.lower()
        settings.set_enable_flag(key, not disabled)

        for name, field in self.fields.items():
            if name not in ignore:
                field.disabled = disabled
                field.update()
        self.push_data(e)

    def sanitize_data(self):
        return

    def push_data(self, e=None, label=None, value=None):
        for key, field in self.fields.items():
            try:
                self.data[key] = field.value
            except AttributeError:
                pass
        # Sanitize data before pushing
        self.sanitize_data()
        # Push
        data_from_views[self.title] = self.data

    def did_mount(self, enable=False):
        handle_transition(self.page, transition=False, update_page=True)
        if self.fields.get('enable', None) is not None:
            # Create enable event
            e = ft.ControlEvent(
                target=None,
                name='did_mount_enable',
                data='true' if enable else 'false',
                page=self.page,
                control=self.fields['enable'],
            )
            # Process enable
            self.process_enable(e)
        return super().did_mount()


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
        # Reset view
        self.reset_view(e, ignore=['part_number', 'supplier'])
        # Validate form
        if not bool(self.fields['part_number'].value) or not bool(self.fields['supplier'].value):
            if not self.fields['part_number'].value:
                error_msg = 'Missing Part Number'
            else:
                error_msg = 'Missing Supplier'
            self.show_dialog(
                d_type=DialogType.ERROR,
                message=error_msg,
            )
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

                part_supplier_form = None
                if part_supplier_info:
                    # Translate to user form format
                    part_supplier_form = inventree_interface.translate_supplier_to_form(
                        supplier=self.fields['supplier'].value,
                        part_info=part_supplier_info,
                    )
                    # Stitch parameters
                    if part_supplier_info.get('parameters', None):
                        self.data['parameters'] = part_supplier_info['parameters']

                if part_supplier_form:
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

            if not self.data['manufacturer_part_number']:
                self.show_dialog(
                    d_type=DialogType.ERROR,
                    message='Part not found',
                )
            elif self.data['searched_part_number'].lower() != self.data['manufacturer_part_number'].lower():
                self.show_dialog(
                    d_type=DialogType.WARNING,
                    message='Found part number does not match the requested part number',
                )
            self.page.update()
        return

    def push_data(self, e=None):
        self.data['searched_part_number'] = self.fields['part_number'].value
        for key, field in self.fields['search_form'].items():
            self.data[key] = field.value
        data_from_views[self.title] = self.data
    
    def update_suppliers(self):
        # Reload suppliers
        self.fields['supplier'].options = [
            ft.dropdown.Option(supplier) for supplier in settings.SUPPORTED_SUPPLIERS_API
        ]
        try:
            self.fields['supplier'].update()
        except AssertionError:
            # Control not added to page yet
            pass

    def build_column(self):
        self.update_suppliers()
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
        'enable': ft.Switch(
            label='InvenTree',
            value=settings.ENABLE_INVENTREE,
        ),
        'alternate': SwitchWithRefs(
            label='Alternate',
            value=settings.ENABLE_ALTERNATE if settings.ENABLE_INVENTREE else False,
            disabled=not settings.ENABLE_INVENTREE,
        ),
        'load_categories': ft.ElevatedButton(
            'Reload InvenTree Categories',
            width=GUI_PARAMS['button_width'] * 2.6,
            height=36,
            icon=ft.icons.REPLAY,
            disabled=False,
        ),
        'Category': DropdownWithSearch(
            label='Category',
            dr_width=GUI_PARAMS['textfield_width'],
            sr_width=GUI_PARAMS['searchfield_width'],
            dense=GUI_PARAMS['textfield_dense'],
            disabled=settings.ENABLE_ALTERNATE,
            options=[],
        ),
        'Existing Part ID': ft.TextField(
            label='Existing Part ID',
            width=GUI_PARAMS['textfield_width'] / 2 - 5,
            dense=GUI_PARAMS['textfield_dense'],
            visible=settings.ENABLE_INVENTREE and settings.ENABLE_ALTERNATE,
        ),
        'Existing Part IPN': ft.TextField(
            label='Existing Part IPN',
            width=GUI_PARAMS['textfield_width'] / 2 - 5,
            dense=GUI_PARAMS['textfield_dense'],
            visible=settings.ENABLE_INVENTREE and settings.ENABLE_ALTERNATE,
        ),
    }

    def __init__(self, page: ft.Page):
        super().__init__(page)
    
    def sanitize_data(self):
        category_tree = self.data.get('Category', None)
        if category_tree:
            self.data['Category'] = inventree_interface.split_category_tree(category_tree)

    def process_enable(self, e):
        # Switch control
        if e.data.lower() == 'false':
            self.fields['alternate'].value = False
            self.fields['alternate'].update()
            self.process_alternate(e, value=False)
        # View mounting control
        if self.fields['alternate'].value:
            # Alternate mode enabled: disable eveything except the alternate fields
            super().process_enable(e, value=True, ignore=['enable', 'Existing Part ID', 'Existing Part IPN'])
            self.process_alternate(e, value=True)
        else:
            super().process_enable(e, value=self.fields['enable'].value, ignore=['enable'])
    
    def process_alternate(self, e, value=None):
        if value:
            visible = value
        else:
            visible = False
            if e.data.lower() == 'true':
                visible = True
        if visible:
            self.show_dialog(
                d_type=DialogType.WARNING,
                message='Enter Existing Part ID or Part IPN',
            )
        settings.set_enable_flag('alternate', visible)

        # Process category dropdown and load category button
        if visible:
            self.fields['Category'].value = None
        self.fields['Category'].disabled = visible
        self.fields['Category'].update()
        self.fields['load_categories'].disabled = visible
        self.fields['load_categories'].update()

        self.push_data(e)

    def get_category_options(self, reload=False):
        return [
            ft.dropdown.Option(category)
            for category in inventree_interface.build_category_tree(reload=reload)
        ]
        
    def reload_categories(self, e):
        self.page.splash.visible = True
        self.page.update()

        # Check connection
        if not inventree_interface.connect_to_server():
            self.show_dialog(DialogType.ERROR, 'ERROR: Failed to connect to InvenTree server')
        else:
            self.fields['Category'].options = self.get_category_options(reload=True)
            self.fields['Category'].update()

        self.page.splash.visible = False
        self.page.update()

    def build_column(self):
        # Update dropdown with category options
        self.fields['Category'].options = self.get_category_options()
        self.fields['Category'].on_change = self.push_data
        self.fields['load_categories'].on_click = self.reload_categories
        # Alternate fields
        self.fields['alternate'].on_change = self.process_alternate
        for alt_field in ['Existing Part ID', 'Existing Part IPN']:
            # Create ref
            ref = ft.Ref[ft.TextField]()
            # Assign ref to field
            ref.current = self.fields[alt_field]
            # Append to alt switch refs
            self.fields['alternate'].refs.append(ref)
            # Assign on_change method
            self.fields[alt_field].on_change = self.push_data

        self.column = ft.Column(
            controls=[
                ft.Row(),
                ft.Row(
                    [
                        self.fields['enable'],
                        self.fields['alternate'],
                        self.fields['load_categories'],
                    ],
                    width=GUI_PARAMS['dropdown_width'],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row([self.fields['Category'],]),
                ft.Row([
                    self.fields['Existing Part ID'],
                    self.fields['Existing Part IPN'],
                ]),
            ],
        )
    
    def did_mount(self):
        return super().did_mount(enable=settings.ENABLE_INVENTREE)


class KicadView(MainView):
    '''KiCad view'''

    title = 'KiCad'
    fields = {
        'enable': ft.Switch(
            label='KiCad',
            value=settings.ENABLE_KICAD,
        ),
        'Symbol Library': DropdownWithSearch(
            label='',
            dr_width=GUI_PARAMS['textfield_width'],
            sr_width=GUI_PARAMS['searchfield_width'],
            dense=GUI_PARAMS['textfield_dense'],
            options=[],
        ),
        'Symbol Template': DropdownWithSearch(
            label='',
            dr_width=GUI_PARAMS['textfield_width'],
            sr_width=GUI_PARAMS['searchfield_width'],
            dense=GUI_PARAMS['textfield_dense'],
            options=[],
        ),
        'Footprint Library': DropdownWithSearch(
            label='',
            dr_width=GUI_PARAMS['textfield_width'],
            sr_width=GUI_PARAMS['searchfield_width'],
            dense=GUI_PARAMS['textfield_dense'],
            options=[],
        ),
        'Footprint': DropdownWithSearch(
            label='',
            dr_width=GUI_PARAMS['textfield_width'],
            sr_width=GUI_PARAMS['searchfield_width'],
            dense=GUI_PARAMS['textfield_dense'],
            options=[],
        ),
        'New Footprint Name': ft.TextField(
            label='New Footprint Name',
            width=GUI_PARAMS['textfield_width'],
            dense=GUI_PARAMS['textfield_dense'],
        ),
        'Check SnapEDA': ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon('search'),
                    ft.Text('Check SnapEDA', size=16),
                ]
            ),
            height=GUI_PARAMS['button_height'],
            width=GUI_PARAMS['button_width'] * 2,
        ),
    }

    def build_alert_dialog(self, symbol: str, footprint: str, download: str, single_result=False):
        modal_content = ft.Row()
        modal_msg = ft.Text('Symbol and footprint are not available on SnapEDA')
        # Build content
        if symbol:
            modal_content.controls.append(ft.Image(symbol))
            modal_msg = ft.Text('Symbol is available on SnapEDA')
        if footprint:
            modal_content.controls.append(ft.Image(footprint))
            if symbol:
                modal_msg = ft.Text('Symbol and footprint are available on SnapEDA')
            else:
                modal_msg = ft.Text('Footprint is available on SnapEDA')
        # Build actions
        modal_actions = []
        if download:
            if not symbol and not footprint:
                if single_result:
                    modal_actions.append(ft.TextButton('Check Part', on_click=lambda _: self.page.launch_url(download)))
                else:
                    modal_msg = ft.Text('Multiple matches found on SnapEDA')
                    modal_actions.append(ft.TextButton('See Results', on_click=lambda _: self.page.launch_url(download)))
            else:
                modal_actions.append(ft.TextButton('Download', on_click=lambda _: self.page.launch_url(download)))
        modal_actions.append(ft.TextButton('Close', on_click=lambda _: self.show_dialog(open=False)))
        
        return ft.AlertDialog(
            modal=True,
            title=modal_msg,
            content=modal_content,
            actions=modal_actions,
            actions_alignment=ft.MainAxisAlignment.END,
            # on_dismiss=None,
        )

    def check_snapeda(self, e):
        if not data_from_views.get('Part Search', {}).get('manufacturer_part_number', ''):
            self.show_dialog(
                d_type=DialogType.ERROR,
                message='Missing Part Data',
            )
            return
        
        self.page.splash.visible = True
        self.page.update()

        response = snapeda_api.fetch_snapeda_part_info(data_from_views['Part Search']['manufacturer_part_number'])
        data = snapeda_api.parse_snapeda_response(response)

        images = {}
        if data['has_symbol'] or data['has_footprint']:
            images = snapeda_api.download_snapeda_images(data)

        self.page.splash.visible = False
        self.page.update()
        
        self.dialog = self.build_alert_dialog(
            images.get('symbol', ''),
            images.get('footprint', ''),
            data.get('part_url', ''),
            data.get('has_single_result', False),
        )
        self.show_dialog(snackbar=False, open=True)

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
            try:
                if 'Footprint Library' in [label, e.control.label]:
                    if value:
                        selected_footprint_library = value
                    else:
                        selected_footprint_library = e.data
                    self.fields['Footprint'].options = self.update_footprint_options(selected_footprint_library)
                    self.fields['Footprint'].update()
            except AttributeError:
                # Handles condition where search field tries to reset dropdown
                pass

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
            # Update callbacks
            if type(field) == ft.ElevatedButton:
                field.on_click = self.check_snapeda
            else:
                if name != 'enable':
                    field.on_change = self.push_data
            # Update options
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

    def did_mount(self):
        if 'InvenTree' in data_from_views:
            # Get value of alternate switch
            if data_from_views['InvenTree'].get('alternate', False):
                self.fields['enable'].disabled = True
                self.fields['enable'].value = False
                self.show_dialog(
                    d_type=DialogType.ERROR,
                    message='InvenTree Alternate switch is enabled',
                )
                return super().did_mount(enable=False)
            else:
                self.fields['enable'].disabled = False
        return super().did_mount(enable=settings.ENABLE_KICAD)


class CreateView(MainView):
    '''Create view'''

    title = 'Create'
    fields = {
        'inventree_progress': ft.ProgressBar(height=32, width=420, value=0),
        'kicad_progress': ft.ProgressBar(height=32, width=420, value=0),
        'create': ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon('build_circle'),
                    ft.Text('Create Part', size=20),
                    ft.Icon('build_circle'),
                ]
            ),
            height=GUI_PARAMS['button_height'],
            width=GUI_PARAMS['button_width'] * 2,
        ),
        'cancel': ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon('highlight_remove'),
                    ft.Text('Cancel', size=20),
                    ft.Icon('highlight_remove'),
                ]
            ),
            height=GUI_PARAMS['button_height'],
            width=GUI_PARAMS['button_width'] * 1.6,
            bgcolor=ft.colors.RED_50,
            disabled=True,
        ),
    }
    inventree_progress_row = None
    kicad_progress_row = None
    create_continue = True

    def show_dialog(self, type: DialogType, message: str):
        if 'create' in self.fields:
            self.enable_create(True)
        return super().show_dialog(type, message)

    def enable_create(self, enable=True):
        self.fields['create'].disabled = not enable
        self.fields['create'].update()
        # Invert cancel button
        self.enable_cancel(enable=not enable)

    def enable_cancel(self, enable=True):
        if enable:
            for item in self.fields['cancel'].content.controls:
                item.color = ft.colors.RED_ACCENT_700
        else:
            for item in self.fields['cancel'].content.controls:
                item.color = None

        self.fields['cancel'].disabled = not enable
        self.fields['cancel'].update()

    def cancel(self, e=None):
        self.create_continue = False

    def process_cancel(self):
        # if settings.ENABLE_INVENTREE:
        #     if self.fields['inventree_progress'].value < 1.0:
        #         self.fields['inventree_progress'].color = "red"
        #         self.fields['inventree_progress'].update()
        # if settings.ENABLE_KICAD:
        #     if self.fields['kicad_progress'].value < 1.0:
        #         self.fields['kicad_progress'].color = "red"
        #         self.fields['kicad_progress'].update()
        self.show_dialog(DialogType.ERROR, 'Action Cancelled')
        self.create_continue = True
        self.enable_create(True)
        return
    
    def reset_progress_bars(self):
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
            self.fields['create'].disabled = True
        else:
            self.fields['create'].disabled = False
        self.fields['create'].update()
        
    def create_part(self, e=None):
        self.reset_progress_bars()

        if not settings.ENABLE_INVENTREE and not settings.ENABLE_KICAD:
            self.show_dialog(DialogType.ERROR, 'Both InvenTree and KiCad are disabled (nothing to create)')

        # print('data_from_views='); cprint(data_from_views)

        # Check data is present
        if not data_from_views.get('Part Search', None):
            self.show_dialog(DialogType.ERROR, 'Missing Part Data (nothing to create)')
            return
        
        # Custom part check
        part_info = copy.deepcopy(data_from_views['Part Search'])
        custom = part_info.pop('custom_part')
        
        if not custom:
            # Part number check
            part_number = data_from_views['Part Search'].get('manufacturer_part_number', None)
            if not part_number:
                self.show_dialog(DialogType.ERROR, 'Missing Part Number')
                return

        # Button update
        self.enable_create(False)

        # KiCad data gathering
        symbol = None
        template = None
        footprint = None
        if settings.ENABLE_KICAD and not settings.ENABLE_ALTERNATE:
            # Check data is present
            if not data_from_views.get('KiCad', None):
                self.show_dialog(DialogType.ERROR, 'Missing KiCad Data')
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
                self.show_dialog(DialogType.ERROR, 'Missing KiCad Data')
                return
        
        if not self.create_continue:
            return self.process_cancel()

        # InvenTree data processing
        if settings.ENABLE_INVENTREE:
            # Check data is present
            if not data_from_views.get('InvenTree', None):
                self.show_dialog(DialogType.ERROR, 'Missing InvenTree Data')
                return
            # Check connection
            if not inventree_interface.connect_to_server():
                self.show_dialog(DialogType.ERROR, 'ERROR: Failed to connect to InvenTree server')
                return
            
            if settings.ENABLE_ALTERNATE:
                # Check mandatory data
                if not data_from_views['InvenTree']['Existing Part ID'] and not data_from_views['InvenTree']['Existing Part IPN']:
                    self.show_dialog(DialogType.ERROR, 'Missing Existing Part ID and Part IPN')
                    return
                # Create alternate
                alt_result = inventree_interface.inventree_create_alternate(
                    part_info=part_info,
                    part_id=data_from_views['InvenTree']['Existing Part ID'],
                    part_ipn=data_from_views['InvenTree']['Existing Part IPN'],
                    show_progress=self.fields['inventree_progress'],
                )
            else:
                # Check mandatory data
                if not data_from_views['Part Search'].get('name', None):
                    self.show_dialog(DialogType.ERROR, 'Missing Part Name')
                    return
                if not data_from_views['Part Search'].get('description', None):
                    self.show_dialog(DialogType.ERROR, 'Missing Part Description')
                    return
                # Get relevant data
                category_tree = data_from_views['InvenTree'].get('Category', None)
                if not category_tree:
                    # Check category is present
                    self.show_dialog(DialogType.ERROR, 'Missing InvenTree Category')
                    return
                else:
                    part_info['category_tree'] = category_tree
                # Create new part
                new_part, part_pk, part_info = inventree_interface.inventree_create(
                    part_info=part_info,
                    kicad=settings.ENABLE_KICAD,
                    symbol=symbol,
                    footprint=footprint,
                    show_progress=self.fields['inventree_progress'],
                    is_custom=custom,
                )
                # print(new_part, part_pk)
                # cprint(part_info)

            if settings.ENABLE_ALTERNATE:
                if alt_result:
                    # Update InvenTree URL
                    if data_from_views['InvenTree']['Existing Part IPN']:
                        part_ref = data_from_views['InvenTree']['Existing Part IPN']
                    else:
                        part_ref = data_from_views['InvenTree']['Existing Part ID']
                    part_info['inventree_url'] = f'{settings.PART_URL_ROOT}{part_ref}/'
                else:
                    self.fields['inventree_progress'].color = "amber"
                # Complete add operation
                self.fields['inventree_progress'].value = progress.MAX_PROGRESS
            else:
                if part_pk:
                    # Update symbol
                    if symbol:
                        symbol = f'{symbol.split(":")[0]}:{part_info["IPN"]}'

                    if not new_part:
                        self.fields['inventree_progress'].color = "amber"
                    # Complete add operation
                    self.fields['inventree_progress'].value = progress.MAX_PROGRESS
                else:
                    self.fields['inventree_progress'].color = "red"
            
            self.fields['inventree_progress'].update()

        if not self.create_continue:
            return self.process_cancel()

        # KiCad data processing
        if settings.ENABLE_KICAD and not settings.ENABLE_ALTERNATE:
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

        if not self.create_continue:
            return self.process_cancel()
        
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

        # Button update
        self.enable_create(True)

    def build_column(self):
        self.inventree_progress_row = ft.Ref[ft.Row]()
        self.kicad_progress_row = ft.Ref[ft.Row]()

        # Update callbacks
        self.fields['create'].on_click = self.create_part
        self.fields['cancel'].on_click = self.cancel

        self.column = ft.Column(
            controls=[
                ft.Row(),
                ft.Row(
                    controls=[
                        self.fields['create'],
                        self.fields['cancel'],
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    width=600,
                ),
                ft.Row(height=16),
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
            ],
        )

    def did_mount(self):
        self.reset_progress_bars()
        return super().did_mount()
