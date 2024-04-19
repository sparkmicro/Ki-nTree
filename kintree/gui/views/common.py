from enum import Enum
from math import pi
from typing import Optional, List

import flet as ft

GUI_PARAMS = {
    'nav_rail_min_width': 100,
    'nav_rail_width': 400,
    'nav_rail_alignment': -0.9,
    'nav_rail_icon_size': 40,
    'nav_rail_text_size': 16,
    'nav_rail_padding': 10,
    'textfield_width': 600,
    'textfield_dense': True,
    'textfield_space_after': 3,
    'dropdown_width': 600,
    'dropdown_dense': False,
    'searchfield_width': 300,
    'button_width': 110,
    'button_height': 56,
    'icon_size': 40,
    'text_size': 16,
}
# Contains data from all views
data_from_views = {}


class DialogType(Enum):
    VALID = 'valid'
    WARNING = 'warning'
    ERROR = 'error'


def handle_transition(page: ft.Page, transition: bool, update_page=False, timeout=0):
    # print(f'{transition=} | {update_page=} | {timeout=}')
    if transition:
        transition = ft.PageTransitionTheme.CUPERTINO
        page.theme.page_transitions.android = transition
        page.theme.page_transitions.ios = transition
        page.theme.page_transitions.linux = transition
        page.theme.page_transitions.macos = transition
        page.theme.page_transitions.windows = transition
    else:
        page.theme.page_transitions.android = ft.PageTransitionTheme.NONE
        page.theme.page_transitions.ios = ft.PageTransitionTheme.NONE
        page.theme.page_transitions.linux = ft.PageTransitionTheme.NONE
        page.theme.page_transitions.macos = ft.PageTransitionTheme.NONE
        page.theme.page_transitions.windows = ft.PageTransitionTheme.NONE

    # Wait
    if timeout:
        import time
        time.sleep(timeout)

    # Update
    if update_page:
        page.update()


def update_theme(page: ft.Page, mode='light', transition=False, compact=True):
    # Color theme
    page.theme_mode = mode

    # UI theme
    theme = ft.Theme()
    page.theme = theme

    # Make it more compact
    if compact:
        page.theme.visual_density = ft.ThemeVisualDensity.COMPACT
    else:
        page.theme.visual_density = ft.ThemeVisualDensity.STANDARD

    # Disable transitions by default
    handle_transition(page, transition=False)


class CommonView(ft.View):
    '''Common view to all GUI views'''

    _page = None
    navigation_rail = None
    title = None
    column = None
    fields = None
    data = None
    dialog = None
    
    def __init__(self, page: ft.Page, appbar: ft.AppBar, navigation_rail: ft.NavigationRail):
        # Store page pointer
        self._page = page

        # Init view
        super().__init__(route=self.route, appbar=appbar)

        # Set navigation rail
        if not self.navigation_rail:
            self.navigation_rail = navigation_rail

    def build_column(self):
        # Empty column (to be set inside the children views)
        self.column = ft.Column()

    def build(self):
        # Build column
        if not self.column:
            self.build_column()
        # Set view controls
        self.controls = [
            ft.Row(
                controls=[
                    self.navigation_rail,
                    ft.VerticalDivider(width=1),
                    self.column,
                ],
                expand=True,
            ),
        ]

    def build_dialog(self):
        return None
    
    def build_snackbar(self, d_type: DialogType, message: str):
        if d_type == DialogType.VALID:
            self.dialog = ft.SnackBar(
                bgcolor=ft.colors.GREEN_100,
                content=ft.Text(
                    message,
                    color=ft.colors.GREEN_700,
                    size=GUI_PARAMS['nav_rail_text_size'],
                    weight=ft.FontWeight.BOLD,
                ),
            )
        elif d_type == DialogType.WARNING:
            self.dialog = ft.SnackBar(
                bgcolor=ft.colors.AMBER_100,
                content=ft.Text(
                    message,
                    color=ft.colors.AMBER_800,
                    size=GUI_PARAMS['nav_rail_text_size'],
                    weight=ft.FontWeight.BOLD,
                ),
            )
        elif d_type == DialogType.ERROR:
            self.dialog = ft.SnackBar(
                bgcolor=ft.colors.RED_100,
                content=ft.Text(
                    message,
                    color=ft.colors.RED_700,
                    size=GUI_PARAMS['nav_rail_text_size'],
                    weight=ft.FontWeight.BOLD,
                ),
            )

    def show_dialog(
            self,
            d_type: Optional[DialogType] = None,
            message: Optional[str] = None,
            snackbar=True,
            open=True,
    ):
        if snackbar:
            self.build_snackbar(d_type, message)
        if isinstance(self.dialog, ft.SnackBar):
            self._page.snack_bar = self.dialog
            self._page.snack_bar.open = True
        elif isinstance(self.dialog, ft.Banner):
            self._page.banner = self.dialog
            self._page.banner.open = open
        elif isinstance(self.dialog, ft.AlertDialog):
            self._page.dialog = self.dialog
            self._page.dialog.open = open
        self._page.update()


class SwitchWithRefs(ft.Switch):
    '''Link the visibility of other fields to a switch value'''

    linked_refs = []
    
    def __init__(
        self,
        refs: List[ft.Ref] = None,
        reverse_dir: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if refs:
            self.refs = refs
            self.enable_refs(self.value)
        self.reverse_dir = reverse_dir

    def enable_refs(self, enable):
        if self.reverse_dir:
            enable = not enable
        for ref in self.linked_refs:
            ref.current.visible = enable
            try:
                ref.current.update()
            except AssertionError:
                # Control not added to page yet
                pass
    
    def process_change(self, e, handler, *args, **kwargs):
        enable = False
        if e.data == 'true':
            enable = True
        self.enable_refs(enable)
        handler(e, *args, **kwargs)

    @property
    def refs(self):
        return self.linked_refs
    
    @refs.setter
    def refs(self, references: List[ft.Ref]):
        if references:
            self.linked_refs = []
            for ref in references:
                try:
                    if ref.current is None:
                        raise Exception(f'Reference "{ref.current}" needs to be added to the page first')
                except AttributeError:
                    raise Exception(f'"{ref}" is not a Flet Ref (type: {type(ref)})')
                # if ft.Control not in ref.current.__class__.__mro__:
                #     raise Exception(f'"{ref.current}" is not a Flet Control ({type(ref.current)})')
                self.linked_refs.append(ref)
            if self.linked_refs:
                self.enable_refs(self.value)

    @ft.Switch.on_change.setter
    def on_change(self, handler, *args, **kwargs):
        ft.Switch.on_change.fset(
            self,
            lambda e: self.process_change(e, handler, *args, **kwargs)
        )


class DropdownWithSearch(ft.UserControl):
    '''Implements a dropdown with search box'''

    dropdown = None
    search_button = None
    search_field = None
    search_box = None
    search_width = None
    
    def build(self):
        return ft.Row([
            self.dropdown,
            self.search_box,
            self.search_button,
        ])
    
    def __str__(self):
        return f'dropdown_with_search {{dropdown: {self.dropdown}, search_field: {self.search_field}}}'

    def __init__(
        self,
        label: Optional[str] = None,
        dr_width: Optional[int] = None,
        sr_width: Optional[int] = None,
        dense: Optional[bool] = None,
        disabled=False,
        sr_animate=100,
        options=None,
        on_change=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._options = options
        self.dropdown = ft.Dropdown(
            label=label,
            width=dr_width,
            dense=dense,
            options=options,
            on_change=on_change,
        )
        self.search_button = ft.IconButton(
            'search',
            on_click=self.search_now
        )
        self.search_field = ft.TextField(
            border="none",
            width=sr_width,
            dense=dense,
            on_change=self.on_search,
        )
        self.search_box = ft.Container(
            content=self.search_field,
            width=0,
            animate=ft.Animation(sr_animate),
        )
        self.disabled = disabled
        self.search_width = sr_width

    @property
    def label(self):
        return self.dropdown.label
    
    @label.setter
    def label(self, label):
        self.dropdown.label = label
        
    @property
    def value(self):
        return self.dropdown.value
    
    @value.setter
    def value(self, value):
        self.dropdown.value = value
        if value is None:
            self.search_field.value = None
            self.done_search()

    @property
    def disabled(self):
        return self.dropdown.disabled
    
    @disabled.setter
    def disabled(self, disabled):
        try:
            self.dropdown.disabled = disabled
            self.dropdown.update()
            self.search_button.disabled = disabled
            self.search_button.update()
            self.search_field.disabled = disabled
            self.search_field.update()
            self.search_box.disabled = disabled
            self.done_search()
        except (AttributeError, AssertionError):
            pass
    
    @property
    def options(self):
        return self.dropdown.options
    
    @options.setter
    def options(self, options):
        self._options = options
        self.dropdown.options = self._options

    @property
    def on_change(self):
        return self.dropdown.on_change
    
    @on_change.setter
    def on_change(self, on_change):
        self.dropdown.on_change = on_change

    def update_option_list(self, input: str):
        new_list_options = []
        for option in self._options:
            if input.lower() in option.key.lower():
                new_list_options.append(option)
        return new_list_options

    def on_search(self, e):
        if self.search_field.value.replace(' ', ''):
            self.dropdown.options = self.update_option_list(self.search_field.value)
            if len(self.dropdown.options) == 1:
                self.dropdown.value = self.dropdown.options[0].key
                self.on_change(e, label=self.label, value=self.value)
            else:
                self.dropdown.value = None
        else:
            self.dropdown.options = self._options
        self.dropdown.update()
        self.on_change()

    def search_now(self, e):
        self.search_box.width = self.search_width
        self.search_box.update()
        self.search_button.icon = 'highlight_remove'
        self.search_button.on_click = self.done_search
        self.search_button.update()
        self.search_field.border = "outline"
        self.search_field.update()
        self.search_field.focus()
        if self.search_field.value:
            self.on_search(e)
    
    def done_search(self, e=None):
        self.search_box.width = 0
        self.search_box.update()
        self.search_button.icon = 'search'
        self.search_button.on_click = self.search_now
        self.search_button.update()
        self.search_field.border = "none"
        self.search_field.update()
        self.options = self._options
        self.dropdown.update()


class Collapsible(ft.Column):
    def __init__(
        self,
        title: str,
        content: ft.Control,
        icon: Optional[ft.Control] = None,
        spacing: float = 3,
        radio: Optional[ft.Radio] = None,
        scale: ft.types.ScaleValue = 1,
    ):
        super().__init__()
        self.icon = icon
        self.title = title
        self.scale = scale
        self.shevron = ft.Icon(
            ft.icons.KEYBOARD_ARROW_RIGHT_ROUNDED,
            animate_rotation=100,
            rotate=0,
            scale=self.scale,
        )
        self.content = ft.Column(
            [ft.Container(height=spacing), content],
            height=0,
            spacing=0,
            animate_size=100,
            opacity=0,
            animate_opacity=100,
            scale=self.scale,
        )
        self.spacing = 0
        self.radio = radio
        self.radio.scale = self.scale

    def header_click(self, e):
        self.content.height = None if self.content.height == 0 else 0
        self.content.opacity = 0 if self.content.height == 0 else 1
        self.shevron.rotate = pi / 2 if self.shevron.rotate == 0 else 0
        self.update()

    def build(self):
        title_row = ft.Row()
        if self.icon is not None:
            title_row.controls.append(self.icon)
        if self.radio:
            title_row.controls.append(self.radio)
        else:
            title_row.controls.append(ft.Text(self.title))
        self.controls = [
            ft.Container(
                ft.Row([title_row, self.shevron], alignment="spaceBetween"),
                padding=ft.padding.only(left=8, right=8),
                height=38,
                border_radius=4,
                ink=True,
                on_click=self.header_click,
            ),
            self.content,
        ]

        
class MenuButton(ft.Container):
    def __init__(
        self,
        title: str,
        icon: Optional[ft.Control] = None,
        selected: bool = False,
        radio: Optional[ft.Radio] = None,
    ):
        super().__init__()
        self.icon = icon
        self.title = title
        self._selected = selected
        self.padding = ft.padding.only(left=43)
        self.height = 38
        self.border_radius = 4
        self.ink = True
        self.on_click = self.item_click
        self.radio = radio

    def item_click(self, _):
        pass

    def build(self):
        row = ft.Row()
        if self.icon is not None:
            row.controls.append(self.icon)
        if self.radio:
            row.controls.append(self.radio)
        else:
            row.controls.append(ft.Text(self.title))
        self.content = row

    def _before_build_command(self):
        self.bgcolor = "surfacevariant" if self._selected else None
        super()._before_build_command()
