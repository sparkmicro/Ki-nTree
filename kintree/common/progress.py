import time

# PySimpleGUI
import PySimpleGUI as sg

CREATE_PART_PROGRESS: float
MAX_PROGRESS = 1.0
DEFAULT_PROGRESS = 0.05


def reset_progress_bar(progress_bar) -> bool:
    ''' Reset progress bar '''
    global CREATE_PART_PROGRESS

    # Reset progress
    CREATE_PART_PROGRESS = 0
    progress_bar.value = 0
    progress_bar.update()

    return True

def progress_increment(inc):
    ''' Increment progress '''
    global CREATE_PART_PROGRESS, MAX_PROGRESS

    if CREATE_PART_PROGRESS + inc < MAX_PROGRESS:
        CREATE_PART_PROGRESS += inc
    else:
        CREATE_PART_PROGRESS = MAX_PROGRESS

    return CREATE_PART_PROGRESS


def update_progress_bar(progress_bar, increment=0) -> bool:
    ''' Update progress bar during part creation '''
    global DEFAULT_PROGRESS

    if not progress_bar:
        return False

    if increment:
        inc = increment
    else:
        # Default
        inc = DEFAULT_PROGRESS

    progress_bar.value = progress_increment(inc)
    progress_bar.update()

    # if event in ['Cancel', sg.WIN_CLOSED]:
    #     on_going_progress = False
    #     close_progress_bar_window()
    # else:
    #     # Smooth effect
    #     for i in range(inc):
    #         progress_increment()
    #         progress_bar.update(CREATE_PART_PROGRESS, MAX_PROGRESS)
    #         if inc < MAX_PROGRESS:
    #             time.sleep(0.02)
    #         else:
    #             time.sleep(0.005)

    return True
