import webbrowser

from common.tools import cprint
from invoke import UnexpectedExit, task

try:
	from search import digikey_api
except ModuleNotFoundError:
	pass


@task
def install(c, is_install=True):
	if is_install:
		cprint(f'[MAIN]\tInstalling required dependencies')
		c.run('pip install -U wheel', hide='out')
	else:
		cprint(f'[MAIN]\tUpdating required dependencies')
	c.run('pip install -U -r requirements.txt', hide='out')

	if is_install:
		cprint(f'[MAIN]\tInstalling optional dependencies')
		try:
			c.run('pip install -U python-Levenshtein', hide=True)
		except UnexpectedExit:
			cprint(f'\n[INFO]\tFailed to install python-Levenshtein...\t'
					'You may be missing python3.x-dev')

@task
def update(c):
	install(c, is_install=False)

@task
def clean(c):
	cprint(f'[MAIN]\tCleaning project directory')
	c.run('find . -name __pycache__ | xargs rm -r')
	try:
		c.run('rm .coverage.*', hide='err')
	except UnexpectedExit:
		pass
	try:
		c.run('rm -r dist build', hide='err')
	except UnexpectedExit:
		pass
	try:
		c.run('rm -r search/results', hide='err')
	except UnexpectedExit:
		pass

@task
def package(c):
	cprint(f'[MAIN]\tPackaging Ki-nTree')
	try:
		c.run('rm dist/kintree.tgz', hide='err')
	except UnexpectedExit:
		pass
	c.run('cd dist/ && tar -czvf kintree.tgz * && cd -', hide=True)

@task
def exec(c):
	cprint(f'[MAIN]\tBuilding Ki-nTree into "dist" directory')
	c.run('pyinstaller --clean --onefile '
		  '-p search/digikey_api/ -p kicad/ -p database/inventree-python/ '
		  'kintree_gui.py', hide=True)

	cprint(f'[MAIN]\tCopying configuration files')
	c.run('mkdir dist/config && mkdir dist/kicad', hide=True)
	c.run('cp -r config/kicad/ dist/config/', hide=True)
	c.run('cp -r config/digikey/ dist/config/', hide=True)
	c.run('cp -r config/inventree/ dist/config/', hide=True)
	c.run('cp config/version.yaml dist/config/', hide=True)
	c.run('cp -r kicad/templates/ dist/kicad/', hide=True)

@task(pre=[clean], post=[package])
def build(c):
	exec(c)

@task
def setup_inventree(c):
	c.run('python setup_inventree.py', hide=True)

@task
def coverage(c):
	cprint(f'\n[MAIN]\tSaving coverage report to "htmlcov" folder')
	c.run('coverage html', hide=True)
	c.run('coverage report')

@task
def refresh_api_token(c):
	result = digikey_api.test_digikey_api_connect()
	if result:
		c.run('cp search/token_storage.json tests/files/', hide=True)

	return result

@task
def test(c):
	api_token = refresh_api_token(c)
	if api_token:
		try:
			c.run('pip show coverage', hide=True)
		except UnexpectedExit:
			c.run('pip install -U coverage', hide=True)

		cprint(f'[MAIN]\tRunning tests using coverage')
		run_inventree = c.run('cd InvenTree/InvenTree/ && python manage.py runserver',
							  asynchronous=True)
		c.run('cd ../.. && sleep 5')
		setup_inventree = c.run('coverage run --parallel-mode setup_inventree.py')
		run_tests = c.run('coverage run --parallel-mode run_tests.py')
		if setup_inventree.exited == 0 and run_tests.exited == 0:
			c.run('coverage combine')
			coverage(c)
	else:
		cprint(f'[MAIN]\tFailed updating Digi-Key API token')
		sys.exit(-1)

@task
def show_coverage(c):
	webbrowser.open('htmlcov/index.html', new=2)

@task
def make_python_badge(c):
	cprint(f'[MAIN]\tInstall pybadges')
	c.run('pip install pybadges pip-autoremove', hide=True)
	cprint(f'[MAIN]\tCreate badge')
	c.run('python -m pybadges --left-text="Python" --right-text="3.6 | 3.7 | 3.8" '
		  '--whole-link="https://www.python.org/" --browser --embed-logo '
		  '--logo="https://dev.w3.org/SVG/tools/svgweb/samples/svg-files/python.svg"')
	cprint(f'[MAIN]\tUninstall pybadges')
	c.run('pip-autoremove pybadges -y', hide=True)
	c.run('pip uninstall pip-autoremove -y', hide=True)
