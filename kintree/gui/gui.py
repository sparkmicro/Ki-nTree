import flet as ft

from .views.common import update_theme, handle_transition
from .views.main import (
    PartSearchView,
    InventreeView,
    KicadView,
    CreateView,
)
from .views.settings import (
    UserSettingsView,
    SupplierSettingsView,
    InvenTreeSettingsView,
    KiCadSettingsView,
)


def init_gui(page: ft.Page):
    '''Initialize page'''
    # Alignments
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ALWAYS
    
    # Theme
    update_theme(page)

    # Creating a progress bar that will be used
    # to show the user that the app is busy doing something
    page.splash = ft.ProgressBar(visible=False)

    # Init dialogs
    page.snack_bar = ft.SnackBar(
        content=None,
        open=False,
    )
    page.banner = ft.Banner()
    page.dialog = ft.AlertDialog()

    # Update
    page.update()


def kintree_gui(page: ft.Page):
    '''Ki-nTree GUI'''
    # Init
    init_gui(page)
    # Create main views
    part_view = PartSearchView(page)
    inventree_view = InventreeView(page)
    kicad_view = KicadView(page)
    create_view = CreateView(page)
    # Create settings views
    user_settings_view = UserSettingsView(page)
    supplier_settings_view = SupplierSettingsView(page)
    inventree_settings_view = InvenTreeSettingsView(page)
    kicad_settings_view = KiCadSettingsView(page)

    # Routing
    def route_change(route):
        # print(f'\n--> Routing to {route.route}')
        if '/main' in page.route or page.route == '/':
            page.views.clear()
            if 'part' in page.route or page.route == '/':
                page.views.append(part_view)
            if 'inventree' in page.route:
                page.views.append(inventree_view)
            elif 'kicad' in page.route:
                page.views.append(kicad_view)
            elif 'create' in page.route:
                page.views.append(create_view)
        elif '/settings' in page.route:
            if '/settings' in page.views[-1].route:
                page.views.pop()
            if 'user' in page.route:
                page.views.append(user_settings_view)
            elif 'supplier' in page.route:
                page.views.append(supplier_settings_view)
            elif 'inventree' in page.route:
                page.views.append(inventree_settings_view)
            elif 'kicad' in page.route:
                page.views.append(kicad_settings_view)
            else:
                page.views.append(user_settings_view)
        page.update()

    def view_pop(view):
        '''Pop setting view'''
        page.views.pop()
        top_view = page.views[-1]
        if 'main' in top_view.route:
            handle_transition(page, transition=True)
        # Route and render
        page.go(top_view.route)
        if 'main' in top_view.route:
            handle_transition(
                page,
                transition=False,
                update_page=True,
                timeout=0.3,
            )
        if '/main/part' in top_view.route or '/main/inventree' in top_view.route:
            top_view.partial_update()

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go(page.route)
