from flet import *
import flet

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

def custom_dropdown(width=200, *args, **kwrds):
    
    def update_option_list(input: str):
        new_list_options = []
        for option in list_options:
            if input.lower() in option.key.lower():
                new_list_options.append(option)
        return new_list_options

    def on_search(me):
        current_value = dr.value
        if sb.value.replace(" ", ""):
            dr.options = update_option_list(sb.value)
            if len(dr.options) == 1:
                dr.value = dr.options[0].key
            else:
                dr.value = None
        else:
            dr.options = list_options
        dr.update()

    def search_now(me):
        sc.width = 200
        sc.update()
        sb.border = "outline"
        sb.update()
        sb.focus()
        if sb.value:
            on_search(me)
    
    def done_search(me):
        sc.width = 0
        sc.update()
        sb.border = "none"
        sb.update()
        dr.options = list_options
        dr.update()

    main_cont = flet.Container(border_radius=12)
    main_row = flet.Row(alignment="center")

    dr = flet.Dropdown(width=width, dense=True, *args, **kwrds)
    sb = flet.TextField(width=200, height=56, border="none", on_change=on_search, on_submit=done_search)
    sc = flet.Container(
        content=sb,
        width=0,
        height=56,
        animate=flet.animation.Animation(100),
    )
    
    main_row.controls.append(dr)
    main_row.controls.append(sc)

    search_btn = flet.IconButton("SEARCH", on_click=search_now)
    main_row.controls.append(search_btn)    
    
    main_cont.content = main_row
    return main_row

def h(page: flet.Page):
    def update_text(e):
        if not control.controls[0].value:
            text.value = f'Please pick a number!'
        else:
            text.value = f'You picked {control.controls[0].value}'
        text.update()

    page.theme_mode = "light"

    confirm_btn = flet.ElevatedButton("Confirm", height=56, on_click=update_text)
    control = custom_dropdown(width=200, label="numbers", options=list_options)
    control.controls.append(confirm_btn)
    text = flet.Text('', text_align=flet.TextAlign.CENTER)
    text_ctnr = flet.Container(
        content=flet.Row(
            [text],
            alignment="center"
        ),
    )
    
    page.add(control)
    page.add(text_ctnr)

flet.app(target=h)