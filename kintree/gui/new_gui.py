import flet as ft

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

def nav_rail(page: ft.Page, selected_index=0):
    ''' Navigation rail '''

    rail = ft.NavigationRail(
        selected_index=selected_index,
        label_type=ft.NavigationRailLabelType.ALL,
        # expand=True,
        min_width=100,
        min_extended_width=400,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.SEARCH,
                selected_icon=ft.icons.MANAGE_SEARCH,
                label="Search"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_INPUT_COMPONENT_OUTLINED,
                selected_icon=ft.icons.SETTINGS_INPUT_COMPONENT,
                label="KiCad",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.INVENTORY_2_OUTLINED,
                selected_icon_content=ft.Icon(ft.icons.INVENTORY),
                label_content=ft.Text("InvenTree"),
            ),
        ],
        on_change=lambda e: page.go(NAV_BAR_INDEX[e.control.selected_index]),
    )

    return rail


def MainGUI(page: ft.Page):
    # Init
    init_gui(page)

    # Views
    settings_view = SettingsView()

    search_view = SearchView(page)
    search_view.build_controls()

    kicad_view = KicadView(page)
    kicad_view.build_controls()

    inventree_view = InvenTreeView(page)
    inventree_view.build_controls()

    # Routing
    print(f'Initial route {page.route}')

    def route_change(route):
        print(f'New route {page.route}')
        
        if page.route in ['/', '/search']:
            page.views.clear()
            page.views.append(search_view)
        elif '/kicad' in page.route:
            page.views.clear()
            page.views.append(kicad_view)
        elif '/inventree' in page.route:
            page.views.clear()
            page.views.append(inventree_view)
        elif '/settings' in page.route:
            page.views.append(settings_view)

        page.update()

    def view_pop(e):
        # print("View pop:", e.view)
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go(page.route)
