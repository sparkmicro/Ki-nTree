import flet as ft


class CommonView(ft.View):
    '''Common view to all GUI views'''

    page = None
    navigation_rail = None
    navidx = None
    NAV_BAR_INDEX = {}
    column = None
    fields = {}
    
    def __init__(self, page: ft.Page, appbar: ft.NavigationBar, navigation_rail: ft.NavigationRail):
        # Store page pointer
        self.page = page

        # Init view
        super().__init__(route=self.route, appbar=appbar)

        # Set navigation rail
        if not self.navigation_rail:
            self.navigation_rail = navigation_rail

        # Build column
        if not self.column:
            self.column = self.build_column()

        # Build controls
        if not self.controls:
            self.controls = self.build_controls()

    def build_column(self):
        # Empty column (to be set inside the children views)
        return ft.Column()

    def build_controls(self):
        return [
            ft.Row(
                controls=[
                    self.navigation_rail,
                    ft.VerticalDivider(width=1),
                    self.column,
                ],
                expand=True,
            ),
        ]
