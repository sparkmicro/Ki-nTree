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
from ...common.tools import cprint, download_with_retry
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
    leading=ft.Container(
        content=ft.Image(
            src=os.path.join(settings.PROJECT_DIR, 'gui', 'logo.png'),
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

# Load navigation indexes
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
        else:
            self.appbar.actions[0].on_click = self.call_settings

        # Update navigation rail
        self.navigation_rail.on_change = self.nav_rail_redirect

        # Init data
        self.data = {}

        # Process enable switch
        if 'enable' in self.fields:
            self.fields['enable'].on_change = self.process_enable

        # Add floating button to reset view
        self.floating_action_button = ft.FloatingActionButton(
            icon=ft.icons.REPLAY, on_click=self.reset_view,
        )

    def nav_rail_redirect(self, e):
        self._page.go(NAV_BAR_INDEX[e.control.selected_index])

    def call_settings(self, e):
        handle_transition(self._page, transition=True)
        self._page.go('/settings')

    def reset_view(self, e, ignore=['enable'], hidden={}):
        def reset_field(field):
            if isinstance(field, ft.ProgressBar):
                field.value = 0
            else:
                field.value = None

        for name, field in self.fields.items():
            if isinstance(field, dict):
                for key, value in field.items():
                    value.disabled = True
                    reset_field(value)
            else:
                if name not in ignore:
                    reset_field(field)

        if hidden:
            for key, value in hidden.items():
                if not value:
                    self.data[key] = value
                else:
                    self.data[key] = None

        # Clear data
        self.push_data()
        self._page.update()

    def partial_update(self):
        '''Process partial view updates'''
        return

    def process_enable(self, e, value=None, ignore=['enable']):
        disabled = False
        if e.data.lower() == 'false':
            disabled = True

        # Overwrite with value
        if value is not None:
            disabled = not value

        key = e.control.label.lower()
        settings.set_enable_flag(key, not disabled)

        for name, field in self.fields.items():
            if name not in ignore:
                field.disabled = disabled
                field.update()
        self.push_data(e)

    def sanitize_data(self):
        return

    def push_data(self, e=None, hidden={}):
        for key, field in self.fields.items():
            try:
                self.data[key] = field.value
            except AttributeError:
                pass

        if hidden:
            for key, value in hidden.items():
                self.data[key] = value

        # Sanitize data before pushing
        self.sanitize_data()
        # Push
        data_from_views[self.title] = self.data

    def did_mount(self, enable=False):
        handle_transition(self._page, transition=False, update_page=True)
        if self.fields.get('enable', None) is not None:
            # Create enable event
            e = ft.ControlEvent(
                target=None,
                name='did_mount_enable',
                data='true' if enable else 'false',
                page=self._page,
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
            width=250,
            expand=True,
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
        'parameter_view': ft.Switch(
            label='View Parameters',
            disabled=True
        ),
        'search_form': {},
        'parameter_form': {},
    }

    def reset_view(self, e, ignore=['enable']):
        hidden_fields = {
            'searched_part_number': '',
            'custom_part': None,
        }
        self.fields['parameter_form'] = {}
        try:
            self.fields['part_number'].focus()
        except AssertionError:
            pass
        return super().reset_view(e, ignore=ignore, hidden=hidden_fields)

    def enable_search_fields(self):
        for form_field in self.fields['search_form'].values():
            form_field.disabled = False
        self.fields['parameter_view'].disabled = False
        self._page.update()
        return

    def run_search(self, e):
        # Reset view
        self.reset_view(e, ignore=['part_number', 'supplier'])
        self.switch_view()
        # Validate form
        if bool(self.fields['part_number'].value) != bool(self.fields['supplier'].value):
            if not self.fields['part_number'].value:
                error_msg = 'Missing Part Number'
            else:
                error_msg = 'Missing Supplier'
            self.show_dialog(
                d_type=DialogType.ERROR,
                message=error_msg,
            )
        else:
            self.fields['part_number'].value = self.fields['part_number'].value.strip()
            self._page.splash.visible = True
            self._page.update()

            if not self.fields['part_number'].value and not self.fields['supplier'].value:
                self.data['custom_part'] = True
                self.enable_search_fields()
            else:
                self.data['custom_part'] = False

                # Get supplier
                supplier = inventree_interface.get_supplier_name(self.fields['supplier'].value)
                # Supplier search
                part_supplier_info = inventree_interface.supplier_search(
                    supplier,
                    self.fields['part_number'].value
                )

                part_supplier_form = None

                if part_supplier_info:
                    # Translate to user form format
                    part_supplier_form = inventree_interface.translate_supplier_to_form(
                        supplier=supplier,
                        part_info=part_supplier_info,
                    )
                    if part_supplier_form:
                        for field_idx, field_name in enumerate(self.fields['search_form'].keys()):
                            # print(field_idx, field_name, get_default_search_keys()[field_idx], search_form_field[field_name])
                            try:
                                self.fields['search_form'][field_name].value = part_supplier_form.get(field_name, '')
                            except IndexError:
                                pass
                            # Enable editing
                            self.enable_search_fields()
                    # Stitch parameters
                    if part_supplier_info.get('parameters', None):
                        self.data['parameters'] = part_supplier_info['parameters']
                        for parameter, value in self.data['parameters'].items():
                            text_field = ft.TextField(
                                label=parameter,
                                value=value,
                                expand=True,
                                on_change=self.push_data,
                            )
                            self.fields['parameter_form'][parameter] = text_field
                    # and pricing
                    if part_supplier_info.get('pricing', None):
                        self.data['pricing'] = part_supplier_info['pricing']
                        self.data['currency'] = part_supplier_info.get('currency', None)

            # Add to data buffer
            self.push_data()
            self._page.splash.visible = False

            if not self.data['supplier_part_number'] and not self.data['custom_part']:
                self.show_dialog(
                    d_type=DialogType.ERROR,
                    message='Part not found',
                )
            elif not self.data['manufacturer_part_number']:
                self.show_dialog(
                    d_type=DialogType.ERROR,
                    message='Found part has no manufacturer part number',
                )
            elif self.data['searched_part_number'].lower() != self.data['manufacturer_part_number'].lower():
                self.show_dialog(
                    d_type=DialogType.WARNING,
                    message='Found manufacturer part number does not match the requested part number',
                )
            self._page.update()
        return

    def push_data(self, e=None):
        hidden_fields = {
            'searched_part_number': self.fields['part_number'].value,
            'custom_part': self.data.get('custom_part', None),
        }
        for key, field in self.fields['search_form'].items():
            self.data[key] = field.value
        for key, field in self.fields['parameter_form'].items():
            self.data['parameters'][key] = field.value
        return super().push_data(e, hidden=hidden_fields)
        
    def partial_update(self):
        # Update supplier options
        self.update_suppliers()
    
    def update_suppliers(self):
        # Reload suppliers
        self.fields['supplier'].options = [
            ft.dropdown.Option(supplier) for supplier in settings.SUPPORTED_SUPPLIERS_API
        ]
        if len(self.fields['supplier'].options) == 1:
            self.fields['supplier'].value = self.fields['supplier'].options[0].key
        else:
            self.fields['supplier'].value = None
        try:
            self.fields['supplier'].update()
        except AssertionError:
            # Control not added to page yet
            pass

    def switch_view(self, e=None):
        # show parameters instead of part information
        parameters_view = self.fields['parameter_view'].value
        self.column.controls[0].content.controls = [
            ft.Row(),
            ft.Row(
                controls=[
                    self.fields['part_number'],
                    self.fields['supplier'],
                    self.fields['search_button'],
                    self.fields['parameter_view'],
                ],
            ),
            ft.Divider(),
        ]
        if not parameters_view:
            for field, text_field in self.fields['search_form'].items():
                self.column.controls[0].content.controls.append(ft.Row([text_field]))
        else:
            for field, text_field in self.fields['parameter_form'].items():
                self.column.controls[0].content.controls.append(ft.Row([text_field]))
        self._page.update()

    def perform_pn_search(self, e):
        self.run_search(e)
        try:
            self.fields['part_number'].focus()
        except AssertionError:
            pass

    def build_column(self):
        self.update_suppliers()
        # Enable search method
        self.fields['search_button'].on_click = self.run_search
        self.fields['parameter_view'].on_change = self.switch_view
        self.fields['part_number'].on_submit = self.perform_pn_search

        self.column = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(),
                            ft.Row(
                                controls=[
                                    self.fields['part_number'],
                                    self.fields['supplier'],
                                    self.fields['search_button'],
                                    self.fields['parameter_view'],
                                ],
                            ),
                            ft.Divider(),
                        ],
                        scroll=ft.ScrollMode.HIDDEN,
                    ),
                    expand=True,
                ),
            ],
            alignment=ft.MainAxisAlignment.END,
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
            self.column.controls[0].content.controls.append(ft.Row([text_field]))
            self.fields['search_form'][field] = text_field

    def did_mount(self, enable=False):
        if (
            not self.fields['part_number'].value
            and self.fields['supplier'].value is None
            and self.data.get('custom_part', None) is None
        ):
            self.show_dialog(
                d_type=DialogType.WARNING,
                message='To create a Custom Part click on the Submit button',
            )
        return super().did_mount(enable)


class InventreeView(MainView):
    '''InvenTree categories view'''

    title = 'InvenTree'
    fields = {
        'enable': ft.Switch(
            label='InvenTree',
            value=settings.ENABLE_INVENTREE,
        ),
        'alternate': ft.Switch(
            label='Update existing',
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
        'load_stock_locations': ft.ElevatedButton(
            'Reload InvenTree Stock locations',
            width=GUI_PARAMS['button_width'] * 2.8,
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
        'IPN: Category Code': ft.Dropdown(
            label='IPN: Category Code',
            width=GUI_PARAMS['textfield_width'] / 2 - 5,
            dense=GUI_PARAMS['textfield_dense'],
            # disabled=settings.CONFIG_IPN.get('IPN_CATEGORY_CODE', False),
            options=[],
        ),
        'Create New Code': SwitchWithRefs(
            label='Create New Code',
        ),
        'check_existing': ft.Switch(
            label='Check for existing Parts',
            value=settings.CHECK_EXISTING if settings.ENABLE_INVENTREE else False,
            disabled=not settings.ENABLE_INVENTREE,
        ),
        'New Category Code': ft.TextField(
            label='New Category Code',
            width=GUI_PARAMS['textfield_width'] / 2 - 5,
            dense=GUI_PARAMS['textfield_dense'],
            visible=False,
        ),
        'Existing Part ID': ft.TextField(
            label='Existing Part ID',
            width=GUI_PARAMS['textfield_width'] / 2 - 5,
            dense=GUI_PARAMS['textfield_dense'],
            visible=True,
        ),
        'Existing Part IPN': ft.TextField(
            label='Existing Part IPN',
            width=GUI_PARAMS['textfield_width'] / 2 - 5,
            dense=GUI_PARAMS['textfield_dense'],
            visible=True,
        ),
        'Update Parameter': SwitchWithRefs(
            label='Update Parameter',
            value=settings.UPDATE_INVENTREE if settings.ENABLE_INVENTREE else False,
            disabled=not settings.ENABLE_INVENTREE,
        ),
        'Create stock': SwitchWithRefs(
            label='Create Stock',
            disabled=not settings.ENABLE_INVENTREE,
        ),
        'Stock location': DropdownWithSearch(
            label='Stock Location',
            disabled=not settings.ENABLE_INVENTREE,
            dr_width=GUI_PARAMS['textfield_width'],
            sr_width=GUI_PARAMS['searchfield_width'],
            dense=GUI_PARAMS['textfield_dense'],
            options=[],
        ),
        'Stock quantity': ft.TextField(
            label='Stock Quantity',
            disabled=not settings.ENABLE_INVENTREE,
            keyboard_type=ft.KeyboardType.NUMBER,
            value='1',
        ),
        'Make stock location default': ft.Checkbox(
            label="Set this location as the part\'s default location",
            disabled=not settings.ENABLE_INVENTREE,
            value=False,
        ),
    }

    def __init__(self, page: ft.Page):
        self.category_row_ref = ft.Ref[ft.Row]()
        self.ipncode_row_ref = ft.Ref[ft.Row]()
        self.alternate_row_ref = ft.Ref[ft.Row]()
        self.create_stock_widgets_ref = ft.Ref[ft.Row]()
        super().__init__(page)

    def partial_update(self):
        # Update IPN row
        self.process_ipncode()
    
    def sanitize_data(self):
        category_tree = self.data.get('Category', None)
        if category_tree:
            self.data['Category'] = inventree_interface.split_category_tree(category_tree)
        stock_location_tree = self.data.get('Stock location', None)
        if stock_location_tree:
            self.data['Stock location'] = inventree_interface.split_category_tree(stock_location_tree)

    def process_enable(self, e):
        inventree_enable = True
        # Switch control: override
        if e.data.lower() == 'false':
            inventree_enable = False
        
        super().process_enable(e, value=inventree_enable, ignore=['enable', 'IPN: Category Code'])
        if not inventree_enable:
            # If InvenTree disabled
            self.fields['alternate'].value = inventree_enable
            self.fields['alternate'].update()
            self.process_alternate(e, value=inventree_enable)
            self.process_create_stock(e, value=inventree_enable)
        else:
            alternate_enable = self.fields['alternate'].value
            self.process_alternate(e, value=alternate_enable)
            stock_create_enabled = self.fields['Create stock'].value
            self.process_create_stock(e, value=stock_create_enabled)

        self.process_ipncode()

    def process_alternate(self, e, value=None):
        if value is not None:
            alt_visible = value
        else:
            # Switch control
            # Reset view
            self.reset_view(e, ignore=['enable', 'alternate'])
            self.fields['New Category Code'].visible = False
            # Get switch value
            alt_visible = False
            if e.data.lower() == 'true':
                alt_visible = True

        # Load category button
        self.fields['load_categories'].disabled = alt_visible
        self.fields['load_categories'].update()

        # Category row visibility
        self.category_row_ref.current.visible = not alt_visible
        self.category_row_ref.current.update()

        # Alternate row visibility
        self.alternate_row_ref.current.visible = alt_visible
        self.alternate_row_ref.current.update()

        # Update settings
        settings.set_enable_flag('alternate', alt_visible)
        settings.set_enable_flag('update', alt_visible)
        # User dialog
        if alt_visible:
            self.show_dialog(
                d_type=DialogType.WARNING,
                message='Alternate Mode Enabled: Enter Existing Part ID or Part IPN',
            )

        self.push_data(e)

    def process_update(self, e, value=None):
        if value is not None:
            update_enabled = value
        else:
            # Get switch value
            update_enabled = False
            if e.data.lower() == 'true':
                update_enabled = True
        settings.set_enable_flag('update', update_enabled)
        self.push_data(e)

    def process_button(self, e, value=None):
        if value is not None:
            button_enabled = value
        else:
            # Get switch value
            button_enabled = False
            if e.data.lower() == 'true':
                button_enabled = True
        if e.control.label == 'Update existing':
            settings.set_enable_flag('update', button_enabled)
        elif e.control.label == 'Check for existing Parts':
            settings.set_enable_flag('check_existing', button_enabled)
        self.push_data(e)

    def process_category(self, e=None, label=None, value=None):
        parent_category = None
        if isinstance(self.fields['Category'].value, str):
            parent_category = inventree_interface.split_category_tree(self.fields['Category'].value)[0]
        # Check for category codes
        options = self.get_code_options()
        if options:
            self.fields['IPN: Category Code'].options = options
            # Select category code corresponding to selected category
            code = config_interface.load_file(settings.CONFIG_CATEGORIES)['CODES'].get(parent_category, None)
            if code and not self.fields['Create New Code'].value:
                self.fields['IPN: Category Code'].value = code
            self.fields['IPN: Category Code'].update()
        self.push_data(e)

    def process_location(self, e=None, label=None, value=None):
        self.fields['Stock location'].options = self.get_stock_location_options()
        self.push_data(e)

    def process_ipncode(self):
        ipncode_enable = bool(
            settings.CONFIG_IPN.get('IPN_ENABLE_CREATE', False) and settings.CONFIG_IPN.get('IPN_CATEGORY_CODE', False)
        )
        self.ipncode_row_ref.current.visible = ipncode_enable
        self.ipncode_row_ref.current.update()

    def process_create_stock(self, e, value=None):
        if value is not None:
            create_stock_visible = value
        else:
            self.fields['New Category Code'].visible = False
            # Get switch value
            create_stock_visible = False
            if e.data.lower() == 'true':
                create_stock_visible = True

        # Stock create row visibility
        self.create_stock_widgets_ref.current.visible = create_stock_visible
        self.create_stock_widgets_ref.current.update()

    def get_code_options(self):
        try:
            return [
                ft.dropdown.Option(code)
                for code in config_interface.load_file(settings.CONFIG_CATEGORIES)['CODES'].values()
            ]
        except AttributeError:
            return []

    def get_category_options(self, reload=False):
        return [
            ft.dropdown.Option(category)
            for category in inventree_interface.build_category_tree(reload=reload)
        ]

    def get_stock_location_options(self, reload=False):
        return [
            ft.dropdown.Option(location)
            for location in inventree_interface.build_stock_location_tree(reload=reload)
        ]
        
    def reload_categories(self, e):
        self._page.splash.visible = True
        self._page.update()

        # Check connection
        if not inventree_interface.connect_to_server():
            self.show_dialog(DialogType.ERROR, 'ERROR: Failed to connect to InvenTree server')
        else:
            self.fields['Category'].options = self.get_category_options(reload=True)
            self.fields['Category'].update()

        self._page.splash.visible = False
        self._page.update()

    def reload_stock_locations(self, e):
        self._page.splash.visible = True
        self._page.update()

        # Check connection
        if not inventree_interface.connect_to_server():
            self.show_dialog(DialogType.ERROR, 'ERROR: Failed to connect to InvenTree server')
        else:
            self.fields['Stock location'].options = self.get_stock_location_options(reload=True)
            self.fields['Stock location'].update()

        self._page.splash.visible = False
        self._page.update()

    def create_ipn_code(self, e):
        # Get switch value
        new_code = True
        if e.data.lower() == 'false':
            new_code = False

        self.fields['IPN: Category Code'].disabled = new_code
        self.fields['IPN: Category Code'].update()
        if not new_code:
            self.process_category()
        else:
            self.push_data(e)

    def build_column(self):
        # Update dropdown with category options
        self.fields['Category'].options = self.get_category_options()
        self.fields['Category'].on_change = self.process_category
        self.fields['load_categories'].on_click = self.reload_categories
        # Category codes
        self.fields['IPN: Category Code'].options = self.get_code_options()
        self.fields['IPN: Category Code'].on_change = self.push_data
        self.fields['Create New Code'].on_change = self.create_ipn_code
        self.fields['New Category Code'].on_change = self.push_data
        # Other Settings
        self.fields['check_existing'].on_change = self.process_button
        # Alternate fields
        self.fields['alternate'].on_change = self.process_alternate
        self.fields['Existing Part ID'].on_change = self.push_data
        self.fields['Existing Part IPN'].on_change = self.push_data
        self.fields['Update Parameter'].on_change = self.process_update
        # Create stock location
        self.fields['Stock location'].options = self.get_stock_location_options()
        self.fields['Stock location'].on_change = self.process_location
        self.fields["Create stock"].on_change = self.process_create_stock
        self.fields['Stock location'].on_change = self.push_data
        self.fields['Stock quantity'].on_change = self.push_data
        self.fields['Make stock location default'].on_change = self.push_data
        self.fields['load_stock_locations'].on_click = self.reload_stock_locations

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
                ft.Row(
                    ref=self.category_row_ref,
                    controls=[
                        ft.Column(
                            [
                                ft.Row([self.fields['Category'],]),
                                ft.Row(
                                    ref=self.ipncode_row_ref,
                                    controls=[
                                        ft.Column(
                                            [
                                                ft.Row(
                                                    [
                                                        self.fields['IPN: Category Code'],
                                                        self.fields['Create New Code'],
                                                    ]
                                                ),
                                                ft.Row([self.fields['New Category Code']]),
                                            ],
                                        ),
                                    ],
                                ),
                                ft.Row(
                                    [
                                        self.fields['check_existing'],
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Column(
                    ref=self.alternate_row_ref,
                    controls=[
                        ft.Row(
                            controls=[
                                self.fields['Existing Part ID'],
                                self.fields['Existing Part IPN'],
                            ],
                        ),
                        ft.Row(
                            controls=[self.fields['Update Parameter']]
                        )
                    ]
                ),
                ft.Column(
                    ref=self.create_stock_widgets_ref,
                    controls=[
                        ft.Row(
                            controls=[
                                self.fields['Create stock'],
                                self.fields['load_stock_locations']
                            ]
                        )
                    ]
                ),
                ft.Column(
                    ref=self.create_stock_widgets_ref,
                    controls=[
                        ft.Row(
                            controls=[self.fields['Stock location']],
                        ),
                        ft.Row(
                            controls=[self.fields['Stock quantity']],
                        ),
                        ft.Row(
                            controls=[self.fields['Make stock location default']],
                        ),
                    ]
                )
            ],
        )

        # Connect New Category Code fields
        cc_ref = ft.Ref[ft.TextField]()
        cc_ref.current = self.fields['New Category Code']
        self.fields['Create New Code'].refs = [cc_ref]
    
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
        'New Footprint': SwitchWithRefs(
            label='New Footprint',
        ),
        'New Footprint Name': ft.TextField(
            label='New Footprint Name',
            width=GUI_PARAMS['textfield_width'],
            dense=GUI_PARAMS['textfield_dense'],
            visible=False,
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
                    modal_actions.append(ft.TextButton('Check Part', on_click=lambda _: self._page.launch_url(download)))
                else:
                    modal_msg = ft.Text('Multiple matches found on SnapEDA')
                    modal_actions.append(ft.TextButton('See Results', on_click=lambda _: self._page.launch_url(download)))
            else:
                modal_actions.append(ft.TextButton('Download', on_click=lambda _: self._page.launch_url(download)))
        modal_actions.append(ft.TextButton('Close', on_click=lambda _: self.show_dialog(open=False)))
        
        return ft.AlertDialog(
            modal=True,
            title=modal_msg,
            content=modal_content,
            actions=modal_actions,
            actions_alignment=ft.MainAxisAlignment.END,
            # on_dismiss=None,
        )
    
    def process_enable(self, e, value=None, ignore=['enable']):
        super().process_enable(e, value, ignore)
        if self.fields['enable'].value:
            self.fields['Footprint'].disabled = self.fields['New Footprint'].value
            self.fields['Footprint'].update()
        
    def push_data(self, e=None, label=None, value=None):
        super().push_data(e)
        if label or e:
            try:
                if 'Footprint Library' in [label, e.control.label]:
                    if value:
                        selected_footprint_library = value
                    else:
                        selected_footprint_library = e.data
                    self.update_footprint_options(selected_footprint_library)
            except AttributeError:
                # Handles condition where search field tries to reset dropdown
                pass

    def check_snapeda(self, e):
        if not data_from_views.get('Part Search', {}).get('manufacturer_part_number', ''):
            self.show_dialog(
                d_type=DialogType.ERROR,
                message='Missing Manufacturer Part Number',
            )
            return
        
        self._page.splash.visible = True
        self._page.update()

        response = snapeda_api.fetch_snapeda_part_info(data_from_views['Part Search']['manufacturer_part_number'])
        data = snapeda_api.parse_snapeda_response(response)

        images = {}
        if data['has_symbol'] or data['has_footprint']:
            images = snapeda_api.download_snapeda_images(data)

        self._page.splash.visible = False
        self._page.update()
        
        self.dialog = self.build_alert_dialog(
            images.get('symbol', ''),
            images.get('footprint', ''),
            data.get('part_url', ''),
            data.get('has_single_result', False),
        )
        self.show_dialog(snackbar=False, open=True)

    def update_footprint_options(self, library: str):
        footprint_options = []
        if library is None:
            return footprint_options
        
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

        self.fields['Footprint'].options = footprint_options
        self.fields['Footprint'].update()

    def get_footprint_libraries(self) -> dict:
        footprint_libraries = {}
        try:
            for folder in sorted(os.listdir(settings.KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'])):
                if os.path.isdir(os.path.join(settings.KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'], folder)):
                    footprint_libraries[folder.replace('.pretty', '')] = os.path.join(
                        settings.KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'],
                        folder
                    )
        except FileNotFoundError:
            pass
        return footprint_libraries

    def find_libraries(self, type: str) -> list:
        found_libraries = []
        if type == 'symbol':
            try:
                found_libraries = [
                    file.replace('.kicad_sym', '')
                    for file in sorted(os.listdir(settings.KICAD_SETTINGS['KICAD_SYMBOLS_PATH']))
                    if file.endswith('.kicad_sym')
                ]
            except FileNotFoundError:
                pass
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

    def build_library_options(self, type: str):
        options = []
        found_libraries = self.find_libraries(type)
        if found_libraries:
            options = [ft.dropdown.Option(lib_name) for lib_name in found_libraries]
        return options
    
    def create_footprint(self, e):
        # Get switch value
        new_footprint = True
        if e.data.lower() == 'false':
            new_footprint = False

        self.fields['Footprint'].disabled = new_footprint
        self.fields['Footprint'].update()
        if not new_footprint:
            self.update_footprint_options(self.fields['Footprint Library'].value)
        self.push_data(e)

    def build_column(self):
        # Library options checks
        self.checks = []

        self.column = ft.Column(
            controls=[ft.Row()],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
        kicad_inputs = []
        for name, field in self.fields.items():
            # Update callbacks
            if isinstance(field, ft.ElevatedButton):
                field.on_click = self.check_snapeda
            # Update options
            elif isinstance(field, DropdownWithSearch):
                field.label = name
                if name == 'Symbol Library':
                    field.options = self.build_library_options(type='symbol')
                elif name == 'Symbol Template':
                    field.options = self.build_library_options(type='template')
                elif name == 'Footprint Library':
                    field.options = self.build_library_options(type='footprint')
                if not field.options and name != 'Footprint':
                    self.checks.append(f'KiCad {name} path does not exists or folder is empty')

            if name != 'enable':
                field.on_change = self.push_data

            kicad_inputs.append(field)
        
        self.column.controls.extend(kicad_inputs)

        # Connect New Footprint fields
        fp_ref = ft.Ref[ft.TextField]()
        fp_ref.current = self.fields['New Footprint Name']
        self.fields['New Footprint'].refs = [fp_ref]
        self.fields['New Footprint'].on_change = self.create_footprint
        
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

        # Process checks
        if self.checks:
            error_msg = f'{self.checks[0]}'
            for check in self.checks[1:]:
                error_msg += f'\n{check}'
            self.show_dialog(
                d_type=DialogType.ERROR,
                message=error_msg,
            )

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
        
        # Part number check
        part_number = data_from_views['Part Search'].get('manufacturer_part_number', None)
        if not custom:
            if not part_number:
                self.show_dialog(DialogType.ERROR, 'Missing Manufacturer Part Number')
                return
            else:
                # Update IPN (later overwritten)
                part_info['IPN'] = part_number

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
                if data_from_views['KiCad'].get('New Footprint', False):
                    new_footprint = data_from_views['KiCad'].get('New Footprint Name', 'TBD')
                    footprint = f"{footprint_lib}:{new_footprint}"
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
                if len(data_from_views['Part Search'].get('name', None)) > 100:
                    self.show_dialog(DialogType.ERROR, 'Part Name too long (>100 characters)')
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
                # Category code
                if settings.CONFIG_IPN.get('IPN_CATEGORY_CODE', False):
                    if data_from_views['InvenTree'].get('Create New Code', False):
                        part_info['category_code'] = data_from_views['InvenTree'].get('New Category Code', '')
                    else:
                        part_info['category_code'] = data_from_views['InvenTree'].get('IPN: Category Code', '')

                stock = None
                if data_from_views['InvenTree'].get('Create stock'):
                    stock_tree = data_from_views['InvenTree'].get('Stock location', None)
                    if not stock_tree:
                        # Check category is present
                        self.show_dialog(DialogType.ERROR, 'Missing InvenTree Stock location')
                        return

                    stock = {
                        'location': inventree_interface.get_inventree_stock_location_id(data_from_views['InvenTree'].get('Stock location')),
                        'quantity': data_from_views['InvenTree'].get('Stock quantity'),
                        'make_default': data_from_views['InvenTree'].get('Make stock location default'),
                    }

                # Create new part
                new_part, part_pk, part_info = inventree_interface.inventree_create(
                    part_info=part_info,
                    kicad=settings.ENABLE_KICAD,
                    symbol=symbol,
                    footprint=footprint,
                    show_progress=self.fields['inventree_progress'],
                    is_custom=custom,
                    stock=stock,
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

                    self.fields['inventree_progress'].color = 'green'
                    if not new_part:
                        self.fields['inventree_progress'].color = 'amber'
                    # Complete add operation
                    self.fields['inventree_progress'].value = progress.MAX_PROGRESS
                else:
                    self.fields['inventree_progress'].color = 'red'
            
            self.fields['inventree_progress'].update()

        if not self.create_continue:
            return self.process_cancel()

        # KiCad data processing
        if settings.ENABLE_KICAD and not settings.ENABLE_ALTERNATE:
            # Store "pseudo-category" as re-used in multiple places
            pseudo_category = symbol.split(':')[0]
            # Translate part info if InvenTree not enabled
            if not settings.ENABLE_INVENTREE:
                part_info = inventree_interface.translate_form_to_inventree(
                    part_info=part_info,
                    category_tree=[pseudo_category],
                    is_custom=custom,
                )
                # Also add datasheet URL as part page URL
                part_info['inventree_url'] = part_info['datasheet']
            part_info['Symbol'] = symbol
            part_info['Template'] = template.split('/')
            part_info['Footprint'] = footprint

            symbol_library_path = os.path.join(
                settings.KICAD_SETTINGS['KICAD_SYMBOLS_PATH'],
                f'{pseudo_category}.kicad_sym',
            )

            # Reset progress
            progress.CREATE_PART_PROGRESS = 0
            # Add part symbol to KiCAD
            cprint('\n[MAIN]\tAdding part to KiCad', silent=settings.SILENT)
            kicad_success, kicad_new_part, kicad_part_name = kicad_interface.inventree_to_kicad(
                part_data=part_info,
                library_path=symbol_library_path,
                show_progress=self.fields['kicad_progress'],
            )
            # print(kicad_success, kicad_new_part)
            # Update symbol name in InvenTree
            if settings.ENABLE_INVENTREE and part_pk:
                old_state = settings.UPDATE_INVENTREE
                settings.UPDATE_INVENTREE = True
                inventree_interface.inventree_process_parameters(
                    part_pk,
                    {'Symbol': f"{symbol_lib}:{kicad_part_name}"},
                    show_progress=self.fields['inventree_progress'],
                )
                settings.UPDATE_INVENTREE = old_state

            # Complete add operation
            if kicad_success:
                self.fields['kicad_progress'].color = 'green'
                if not kicad_new_part:
                    self.fields['kicad_progress'].color = 'amber'
                    self.fields['kicad_progress'].update()
                self.fields['kicad_progress'].value = progress.MAX_PROGRESS
                self.fields['kicad_progress'].update()
            else:
                self.fields['kicad_progress'].color = 'red'
                self.fields['kicad_progress'].update()

        if not self.create_continue:
            return self.process_cancel()
        
        # Final operations
        # Download a local version of the part datasheet
        if settings.DATASHEET_SAVE_ENABLED:
            filename = os.path.join(
                settings.DATASHEET_SAVE_PATH,
                f'{part_info.get("IPN", "datasheet")}.pdf',
            )
            if settings.DATASHEET_UPLOAD and os.path.isfile(filename):
                # Datasheet was already downloaded
                cprint('\n[MAIN]\tDatasheet')
                cprint(f'[INFO]\tSuccess: Datasheet file exists ({filename})')
            else:
                # Datasheet needs to be downloaded
                datasheet_url = part_info.get('datasheet', None)
                if datasheet_url:
                    cprint('\n[MAIN]\tDownloading Datasheet')
                    if download_with_retry(datasheet_url, filename, filetype='PDF', timeout=10):
                        cprint(f'[INFO]\tSuccess: Datasheet saved to {filename}')
        # Open browser
        if settings.ENABLE_INVENTREE:
            if part_info.get('inventree_url', None):
                if settings.AUTOMATIC_BROWSER_OPEN:
                    # Auto-Open Browser Window
                    cprint(
                        f'\n[MAIN]\tOpening URL {part_info["inventree_url"]} in browser',
                        silent=settings.SILENT
                    )
                    try:
                        self._page.launch_url(part_info['inventree_url'])
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
