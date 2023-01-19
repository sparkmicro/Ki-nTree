import flet as ft

from .views import NAV_BAR_INDEX
from .views import SettingsView, SearchView, KicadView, InvenTreeView


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


def MainGUI(page: ft.Page):
    # Init
    init_gui(page)
    
    # Views
    settings_view = SettingsView(page)
    search_view = SearchView(page)
    kicad_view = KicadView(page)
    inventree_view = InvenTreeView(page)

    def route_change(route):
        print(f'Routing to {route.route}')
        
        if page.route == '/':
            page.views.append(search_view)
        elif page.route == '/settings':
            page.views.append(settings_view)
        else:
            page.views.clear()
            if page.route == NAV_BAR_INDEX[0]:
                page.views.append(search_view)
            elif page.route == NAV_BAR_INDEX[1]:
                page.views.append(kicad_view)
            elif page.route == NAV_BAR_INDEX[2]:
                page.views.append(inventree_view)

        page.update()

    def view_pop(e):
        # print("View pop:", e.view)
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go(page.route)
