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
    
    def route_change(route):
        print(f'\n--> Routing to {route.route}')
        if '/main' in page.route:
            page.views.clear()
            if 'part' in page.route:
                part_view = PartSearchView(page)
                page.views.append(part_view)
            if 'inventree' in page.route:
                inventree_view = InventreeView(page)
                page.views.append(inventree_view)
            elif 'kicad' in page.route:
                kicad_view = KicadView(page)
                page.views.append(kicad_view)
            elif 'create' in page.route:
                create_view = CreateView(page)
                page.views.append(create_view)
        elif '/settings' in page.route:
            user_settings_view = UserSettingsView(page)
            if '/settings' in page.views[-1].route:
                page.views.pop()
            if 'user' in page.route:
                page.views.append(user_settings_view)
            elif 'supplier' in page.route:
                supplier_settings_view = SupplierSettingsView(page)
                page.views.append(supplier_settings_view)
            elif 'inventree' in page.route:
                inventree_settings_view = InvenTreeSettingsView(page)
                page.views.append(inventree_settings_view)
            elif 'kicad' in page.route:
                kicad_settings_view = KiCadSettingsView(page)
                page.views.append(kicad_settings_view)
            else:
                page.views.append(user_settings_view)
        else:
            page.go('/main/part')

        page.update()

    def view_pop(e):
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
        # if 'part' in top_view.route:
        #     part_view.partial_update()
        # elif 'inventree' in top_view.route:
        #     inventree_view.partial_update()

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go(page.route)
