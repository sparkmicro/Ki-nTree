import time

CREATE_PART_PROGRESS: float
MAX_PROGRESS = 1.0
DEFAULT_PROGRESS = 0.1


def reset_progress_bar(progress_bar) -> bool:
    ''' Reset progress bar '''
    global CREATE_PART_PROGRESS

    # Reset progress
    CREATE_PART_PROGRESS = 0
    progress_bar.color = None
    progress_bar.value = 0
    progress_bar.update()
    time.sleep(0.1)

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
        return True

    if increment:
        inc = increment
    else:
        # Default
        inc = DEFAULT_PROGRESS

    current_value = progress_bar.value * 100
    new_value = progress_increment(inc) * 100
    # Smooth progress
    for i in range(int(new_value - current_value)):
        progress_bar.value += i / 100
        progress_bar.update()
        time.sleep(0.05)

    return True
