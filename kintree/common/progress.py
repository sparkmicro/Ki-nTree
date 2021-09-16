import time

# PySimpleGUI
import PySimpleGUI as sg

CREATE_PART_PROGRESS: int
MAX_PROGRESS = 100
DEFAULT_PROGRESS = 5


def create_progress_bar_window(font=None, location=None) -> bool:
    ''' Create window for part creation progress '''
    global CREATE_PART_PROGRESS, MAX_PROGRESS
    global progress_window

    progress_layout = [
        [sg.Text('Creating part...')],
        [sg.ProgressBar(MAX_PROGRESS, orientation='h', size=(20, 30), key='progressbar')],
        [sg.Cancel()]
    ]
    progress_window = sg.Window('Part Creation Progress', progress_layout, font=font, location=location)
    # progress_bar = progress_window['progressbar']

    event, values = progress_window.read(timeout=10)

    # Reset progress
    CREATE_PART_PROGRESS = 0
    update_progress_bar_window()

    if progress_window:
        return True

    return False


def close_progress_bar_window():
    ''' Close progress bar window after part creation '''
    global progress_window

    try:
        if progress_window:
            progress_window.close()
    except NameError:
        return


def progress_increment():
    ''' Increment progress '''
    global CREATE_PART_PROGRESS, MAX_PROGRESS

    if CREATE_PART_PROGRESS + 1 < MAX_PROGRESS:
        CREATE_PART_PROGRESS += 1
    else:
        CREATE_PART_PROGRESS = MAX_PROGRESS


def update_progress_bar_window(increment=0) -> bool:
    ''' Update progress bar during part creation '''
    global CREATE_PART_PROGRESS, MAX_PROGRESS, DEFAULT_PROGRESS
    global progress_window

    on_going_progress = True

    try:
        if not progress_window:
            return False
    except NameError:
        return False

    if increment:
        inc = increment
    else:
        # Default
        inc = DEFAULT_PROGRESS

    progress_bar = progress_window['progressbar']

    event, values = progress_window.read(timeout=10)

    if event in ['Cancel', sg.WIN_CLOSED]:
        on_going_progress = False
        close_progress_bar_window()
    else:
        # Smooth effect
        for i in range(inc):
            progress_increment()
            progress_bar.update(CREATE_PART_PROGRESS, MAX_PROGRESS)
            if inc < MAX_PROGRESS:
                time.sleep(0.02)
            else:
                time.sleep(0.005)

    return on_going_progress
