import flet as ft

from .views.settings import UserSettingsView, SupplierSettingsView, InvenTreeSettingsView, KiCadSettingsView 
from .views.main import SearchView, CategoryView, KicadView


def init_gui(page: ft.Page):
    ''' Initialize window '''
    # Alignments
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Theme
    page.theme_mode = "light"
    theme = ft.Theme()

    # Disable transitions
    theme.page_transitions.android = ft.PageTransitionTheme.NONE
    theme.page_transitions.ios = ft.PageTransitionTheme.NONE
    theme.page_transitions.linux = ft.PageTransitionTheme.NONE
    theme.page_transitions.macos = ft.PageTransitionTheme.NONE
    theme.page_transitions.windows = ft.PageTransitionTheme.NONE

    # Make it more compact
    theme.visual_density = ft.ThemeVisualDensity.COMPACT
    page.theme = theme
    page.scroll = ft.ScrollMode.ALWAYS

    # Creating a progress bar that will be used to show the user that the app is busy doing something.
    page.splash = ft.ProgressBar(visible=False)

    # Update
    page.update()


category_view = None
kicad_view = None
def MainGUI(page: ft.Page):
    # Init
    init_gui(page)
    # Views
    search_view = SearchView(page)
    # Settings
    user_settings_view = UserSettingsView(page)
    # supplier_settings_view = SupplierSettingsView(page)
    inventree_settings_view = InvenTreeSettingsView(page)
    kicad_settings_view = KiCadSettingsView(page)

    def route_change(route):
        global category_view, kicad_view

        print(f'\n--> Routing to {route.route}')
        
        if page.route == '/' or page.route == search_view.route:
            page.views.clear()
            page.views.append(search_view)
        elif '/settings' in page.route:
            if '/settings' in page.views[-1].route:
                page.views.pop()
            if page.route == user_settings_view.route:
                page.views.append(user_settings_view)
            # elif page.route == supplier_settings_view.route:
            #     page.views.append(supplier_settings_view)
            elif page.route == inventree_settings_view.route:
                page.views.append(inventree_settings_view)
            elif page.route == kicad_settings_view.route:
                page.views.append(kicad_settings_view)
            else:
                page.views.append(user_settings_view)
        elif '/add' in page.route:
            page.views.clear()
            # New search: new views
            if search_view.trigger:
                category_view = None
                kicad_view = None
                search_view.trigger = False
            if 'category' in page.route:
                if category_view is None:
                    category_view = CategoryView(page)
                page.views.append(category_view)
            if 'kicad' in page.route:
                if kicad_view is None:
                    kicad_view = KicadView(page)
                else:
                    kicad_view.navigation_rail.selected_index = kicad_view.step
                page.views.append(kicad_view)

        page.update()

    def view_pop(e):
        # print("View pop:", e.view)
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go(page.route)