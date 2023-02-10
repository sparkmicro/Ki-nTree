import flet as ft
# Common view
from .common import CommonView, Collapsible, MenuButton
from ...common.tools import cprint
# Settings
from ...config import settings, config_interface
# InvenTree
from ...database import inventree_interface

# Main AppBar
main_appbar = ft.AppBar(
    leading=ft.Icon(ft.icons.DOUBLE_ARROW),
    leading_width=40,
    title=ft.Text('Ki-nTree | 0.7.0dev'),
    center_title=False,
    bgcolor=ft.colors.SURFACE_VARIANT,
    actions=[],
)

# Main NavRail
main_navrail = ft.NavigationRail(
    selected_index=0,
    label_type=ft.NavigationRailLabelType.ALL,
    min_width=100,
    min_extended_width=400,
    group_alignment=-0.9,
    destinations=[],
    on_change=None,
)


class MainView(CommonView):
    '''Main view'''

    route = '/'
    # Navigation indexes
    STEP_INDEX = {
        0: '/search',
        1: '/add/category',
        2: '/add/kicad',
    }
    step = None

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page=page, appbar=main_appbar, navigation_rail=main_navrail)

        # Update application bar
        if not self.appbar.actions:
            self.appbar.actions.append(ft.IconButton(ft.icons.SETTINGS, on_click=lambda e: self.page.go('/settings')))

        # Update navigation rail
        if not self.navigation_rail.on_change:
            self.navigation_rail.on_change = lambda e: self.page.go(self.STEP_INDEX[e.control.selected_index])

        if len(self.navigation_rail.destinations) > self.step + 1:
            self.navigation_rail.destinations.pop()

        if len(self.navigation_rail.destinations) < self.step + 1:
            self.navigation_rail.destinations.append(self.get_rail_destination())

        self.navigation_rail.selected_index = self.step

    def get_rail_destination(self):
        return ft.NavigationRailDestination()


class SearchView(MainView):
    '''Search view'''

    route = '/search'
    step = 0
    trigger = False
    form_data = {}
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
        'enable_inventree': ft.Switch(label='InvenTree', value=False, disabled=True),
        'enable_kicad': ft.Switch(label='KiCad', value=False, disabled=True),
        # 'enable_alternate': ft.Switch(label='Alternate', value=False),
        'add_button': ft.ElevatedButton('Add', icon=ft.icons.ADD, disabled=True),
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

    def get_rail_destination(self):
        return ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.SEARCH, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.MANAGE_SEARCH, size=40),
            label_content=ft.Text("Search", size=16),
            padding=10,
        )

    def enable_search_fields(self):
        self.fields['enable_inventree'].disabled = False
        self.fields['enable_kicad'].disabled = False
        self.fields['add_button'].disabled = False
        for form_field in self.fields['search_form'].values():
            form_field.disabled = False
        self.page.update()
        return

    def run_search(self):
        self.page.splash.visible = True
        self.page.update()

        if not self.fields['part_number'].value and not self.fields['supplier'].value:
            self.enable_search_fields()
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
                    self.enable_search_fields()

        self.page.splash.visible = False
        self.page.update()
        return

    def run_add(self):
        self.add_to['inventree'] = self.fields["enable_inventree"].value
        self.add_to['kicad'] = self.fields["enable_kicad"].value
        print(f'{self.add_to=}')

        for key, field in self.fields['search_form'].items():
            self.form_data[key] = field.value
        cprint(self.form_data)

        # Reset views and navigation rail
        self.trigger = True
        self.navigation_rail.destinations = [self.get_rail_destination()]
        self.page.go(CategoryView.route)

    def build_column(self):
        for name, field in self.fields.items():
            if type(field) == ft.ElevatedButton:
                field.width = 100
                field.height = 48
            if name == 'search_button':
                field.on_click = lambda e: self.run_search()
            elif name == 'add_button':
                field.on_click = lambda e: self.run_add()

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
                ft.Row(
                    controls=[
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        self.fields['enable_inventree'],
                                        self.fields['enable_kicad'],
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                            expand=True,
                        ),
                        ft.Column(
                            [
                                self.fields['add_button'],
                            ],
                            alignment=ft.MainAxisAlignment.END,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            expand=True,
                        ),
                    ],
                ),
                ft.Divider(),
            ],
            alignment=ft.MainAxisAlignment.START,
            scroll=ft.ScrollMode.HIDDEN,
            expand=True,
        )


class CategoryView(MainView):
    '''InvenTree categories view'''

    route = '/add/category'
    step = 1
    selected_category = None

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page)

    def get_rail_destination(self):
        return ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.CATEGORY_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.CATEGORY, size=40),
            label_content=ft.Text("Category", size=16),
            padding=10,
        )

    def update_selected_category(self, selected_category: str):
        self.selected_category = selected_category

    def process_selected_category(self):
        print(f'{self.selected_category=}')
        self.page.go(KicadView.route)

    def build_column(self):
        print('Populate categories')
        subcategories = []
        for i in [1, 4, 7, 10]:
            subcategories.append(
                ft.Column(
                    [
                        MenuButton(f'Subcategory {i}', radio=ft.Radio(value=f'Subcategory {i}', label=f'Subcategory {i}')),
                        MenuButton(f'Subcategory {i+1}', radio=ft.Radio(value=f'Subcategory {i+1}', label=f'Subcategory {i+1}')),
                        MenuButton(f'Subcategory {i+2}', radio=ft.Radio(value=f'Subcategory {i+2}', label=f'Subcategory {i+2}')),
                    ],
                    spacing=3,
                )
            )

        scale = 1.0
        return ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        controls=[
                                ft.ElevatedButton('Next', icon=ft.icons.ARROW_RIGHT, width=100, height=48, on_click=lambda _: self.process_selected_category()),
                                ft.RadioGroup(
                                    content=ft.Column(
                                        [
                                            Collapsible(
                                                'Category 1',
                                                radio=ft.Radio(value='Category 1', label='Category 1'),
                                                content=subcategories[0],
                                                scale=scale,
                                            ),
                                            Collapsible(
                                                'Category 2',
                                                radio=ft.Radio(value='Category 2', label='Category 2'),
                                                content=subcategories[1],
                                                scale=scale,
                                            ),
                                            Collapsible(
                                                'Category 3',
                                                radio=ft.Radio(value='Category 3', label='Category 3'),
                                                content=subcategories[2],
                                                scale=scale,
                                            ),
                                            Collapsible(
                                                'Category 4',
                                                radio=ft.Radio(value='Category 4', label='Category 4'),
                                                content=subcategories[3],
                                                scale=scale,
                                            ),
                                        ],
                                        width=450,
                                    ),
                                    on_change=lambda e: self.update_selected_category(e.data),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START
                        ),
                        expand=True,
                ),
            ],
            width=500,
            alignment=ft.MainAxisAlignment.START,
            scroll=ft.ScrollMode.HIDDEN,
        )


class KicadView(MainView):
    '''KiCad view'''

    route = '/add/kicad'
    step = 2
    fields = {
        'Pick Symbol Library': ft.Dropdown(),
        'Pick Symbol Template': ft.Dropdown(),
        'Pick Footprint Library': ft.Dropdown(),
        'Pick Footprint': ft.Dropdown(),
        'New Footprint Name': ft.TextField(),
    }

    def __init__(self, page: ft.Page):
        # Init view
        super().__init__(page)

    def get_rail_destination(self):
        return ft.NavigationRailDestination(
            icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT_OUTLINED, size=40),
            selected_icon_content=ft.Icon(name=ft.icons.SETTINGS_INPUT_COMPONENT, size=40),
            label_content=ft.Text("KiCad", size=16),
            padding=10,
        )

    def build_library_options(self, type: str):
        import os
        found_libraries = []
        if type == 'symbol':
            found_libraries = [file.replace('.kicad_sym', '') for file in sorted(os.listdir(settings.KICAD_SYMBOLS_PATH))
                                if file.endswith('.kicad_sym')]
        elif type == 'footprint':
            found_libraries = [folder.replace('.pretty', '') for folder in sorted(os.listdir(settings.KICAD_FOOTPRINTS_PATH))
                                if os.path.isdir(os.path.join(settings.KICAD_FOOTPRINTS_PATH, folder))]
        
        options = [ft.dropdown.Option(lib_name) for lib_name in found_libraries]
        return options

    def create_part(self):
        print('Create Part')

    def build_column(self):
        column = ft.Column(
            [],
            alignment=ft.MainAxisAlignment.START,
            expand=True,
        )
        kicad_inputs = []
        for name, field in self.fields.items():
            field.label = name
            field.dense = True
            if name == 'Pick Symbol Library':
                field.options = self.build_library_options(type='symbol')
            elif name == 'Pick Footprint Library':
                field.options = self.build_library_options(type='footprint')
            kicad_inputs.append(field)
        column.controls.extend(kicad_inputs)
        column.controls.append(ft.ElevatedButton('Create', icon=ft.icons.ARROW_RIGHT, width=150, height=48, on_click=lambda _: self.create_part()))
        return column
