from flet import *
import flet
from views.common import DropdownWithSearch

list_options = [
    flet.dropdown.Option("one"),
    flet.dropdown.Option("two"),
    flet.dropdown.Option("three"),
    flet.dropdown.Option("four"),
    flet.dropdown.Option("five"),
    flet.dropdown.Option("six"),
    flet.dropdown.Option("seven"),
    flet.dropdown.Option("eight"),
    flet.dropdown.Option("nine"),
    flet.dropdown.Option("ten"),
    flet.dropdown.Option("twenty"),
    flet.dropdown.Option("thirty"),
    flet.dropdown.Option("fourty"),
    flet.dropdown.Option("fifty"),
    flet.dropdown.Option("hundred"),
]

def h(page: flet.Page):
    def update_text(e):
        if not dropdown.value:
            text.value = f'Please pick a number!'
        else:
            text.value = f'You picked {dropdown.value}'
        text.update()

    page.theme_mode = "light"

    dropdown = DropdownWithSearch(label="numbers", width=400, dense=True, options=list_options)
    confirm_btn = flet.ElevatedButton("Confirm", height=56, on_click=update_text)
    
    text = flet.Text('', text_align=flet.TextAlign.CENTER)
    text_ctnr = flet.Container(
        content=flet.Row(
            [text],
            alignment="center",
        ),
    )
    
    page.add(
        flet.Row(
            [
                dropdown.container,
                confirm_btn,
            ],
            alignment="center",
        ),
        text_ctnr,
    )

flet.app(target=h)