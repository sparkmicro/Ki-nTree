import PySimpleGUI as sg

CREATE_PART_PROGRESS: int
MAX_PROGRESS = 100

def create_progress_bar_window():
	''' Create window for part creation progress '''
	global CREATE_PART_PROGRESS, MAX_PROGRESS
	global progress_window

	progress_layout = [[sg.Text('Creating part...')],
					  [sg.ProgressBar(MAX_PROGRESS, orientation='h', size=(20, 20), key='progressbar')],
					  [sg.Cancel()]]
	progress_window = sg.Window('Part Creation Progress', progress_layout, location=(500, 500))
	progress_bar = progress_window['progressbar']

	event, values = progress_window.read(timeout=10)

	# Reset progress
	CREATE_PART_PROGRESS = 0
	progress_bar.UpdateBar(CREATE_PART_PROGRESS)

	return progress_window

def close_progress_bar_window():
	''' Close progress bar window after part creation '''
	global progress_window

	if progress_window:
		progress_window.close()

def progress_increment(inc=5):
	''' Increment progress '''
	global CREATE_PART_PROGRESS, MAX_PROGRESS

	if CREATE_PART_PROGRESS + inc < MAX_PROGRESS:
		CREATE_PART_PROGRESS += inc
	else:
		CREATE_PART_PROGRESS = MAX_PROGRESS

def update_progress_bar_window() -> bool:
	''' Update progress bar during part creation '''
	global CREATE_PART_PROGRESS
	global progress_window

	stop = False

	if not progress_window:
		return stop

	# progress_bar = window['progressbar']
	progress_bar = progress_window.FindElement('progressbar')

	event, values = progress_window.read(timeout=10)
	print(f'{event=}')

	if not event:
		print('Uneventful')

	# if event in ['Cancel', sg.WIN_CLOSED]:
	# 	stop = True
	# else:
	print(f'{progress_bar=}')
	progress_increment()
	print(f'{CREATE_PART_PROGRESS} / {MAX_PROGRESS}')
	print(progress_bar.UpdateBar(CREATE_PART_PROGRESS, MAX_PROGRESS))

	return stop

