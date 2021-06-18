import webbrowser

from common.tools import cprint
from invoke import UnexpectedExit, task


@task
def install(c, is_install=True):
	if is_install:
		cprint('[MAIN]\tInstalling required dependencies')
		c.run('pip install -U wheel', hide='out')
	else:
		cprint('[MAIN]\tUpdating required dependencies')
	c.run('pip install -U -r requirements.txt', hide='out')
	# Install wrapt_timeout_decorator library from GitHub
	c.run('pip install git+https://github.com/bitranox/wrapt_timeout_decorator.git', hide='out')

	if is_install:
		cprint('[MAIN]\tInstalling optional dependencies')
		try:
			c.run('pip install -U python-Levenshtein', hide=True)
		except UnexpectedExit:
			cprint('\n[INFO]\tFailed to install python-Levenshtein...\t'
					'You may be missing python3.x-dev')

@task
def update(c):
	install(c, is_install=False)

@task
def clean(c):
	cprint('[MAIN]\tCleaning project directory')
	c.run('find . -name __pycache__ | xargs rm -r')
	try:
		c.run('rm .coverage', hide='err')
	except UnexpectedExit:
		pass
	try:
		c.run('rm .coverage.*', hide='err')
	except UnexpectedExit:
		pass
	try:
		c.run('rm -r dist build htmlcov', hide='err')
	except UnexpectedExit:
		pass

@task
def package(c):
	import os
	import shutil
	
	cdir = os.getcwd()
	dist = os.path.join(cdir, 'dist')
	
	cprint('[MAIN]\tPackaging Ki-nTree')
	
	# Delete previous files
	try:
		c.run('rm dist/kintree.tgz', hide='err')
	except UnexpectedExit:
		pass
	try:
		c.run('rm dist/kintree.zip', hide='err')
	except UnexpectedExit:
		pass
		
	# Create ZIP
	shutil.make_archive(os.path.join(cdir, 'kintree'), 'zip', dist)
	# Create TGZ
	c.run(f'cd {dist} && tar -czvf kintree.tgz * && cd {cdir}', hide=True)
	# Move ZIP file into dist folder
	c.run(f'mv kintree.zip {dist}', hide=False)

@task
def exec(c):
	cprint(f'[MAIN]\tBuilding Ki-nTree into "dist" directory')
	c.run('pyinstaller --clean --onefile '
		  '-p search/digikey_api/ -p kicad/ -p database/inventree-python/ '
		  'kintree_gui.py', hide=True)

@task
def copy_configuration(c):
	import os

	cdir = os.getcwd()
	dist = os.path.join(cdir, 'dist')
	config = os.path.join(dist, 'config')
	kicad = os.path.join(dist, 'kicad')

	cprint(f'[MAIN]\tCopying configuration files')
	c.run(f'mkdir {config} && mkdir {kicad}', hide=False)
	c.run('cp -r config/kicad/ dist/config/', hide=False)
	c.run('cp -r config/digikey/ dist/config/', hide=False)
	c.run('cp -r config/inventree/ dist/config/', hide=False)
	c.run('cp -r config/settings/ dist/config/', hide=False)
	c.run('cp config/version.yaml dist/config/', hide=False)
	c.run('cp -r kicad/templates/ dist/kicad/', hide=False)

@task(pre=[clean], post=[package])
def build(c):
	exec(c)
	copy_configuration(c)

@task
def setup_inventree(c):
	c.run('python setup_inventree.py')

@task
def coverage_report(c, open_browser=True):
	cprint('[MAIN]\tBuilding coverage report')
	c.run('coverage report')
	c.run('coverage html')
	if open_browser:
		webbrowser.open('htmlcov/index.html', new=2)

@task
def refresh_api_token(c):
	from search.digikey_api import test_digikey_api_connect
	test_digikey_api_connect()

@task
def save_api_token(c):
	c.run('cp search/token_storage.json tests/files/', hide=True)

@task
def test(c, setup=True):
	try:
		c.run('pip show coverage', hide=True)
	except UnexpectedExit:
		c.run('pip install -U coverage', hide=True)

	cprint('[MAIN]\tRunning tests using coverage\n-----')
	if setup:
		c.run('cd InvenTree/InvenTree/ && python manage.py runserver',
			  asynchronous=True)
		c.run('cd ../.. && sleep 5')
		setup_inventree = c.run('coverage run --parallel-mode setup_inventree.py')
		cprint('\n-----')
		if setup_inventree.exited == 0:
			run_tests = c.run('coverage run --parallel-mode run_tests.py')
			if run_tests.exited == 0:
				c.run('coverage combine')
				coverage_report(c, open_browser=False)
	else:
		run_tests = c.run('coverage run run_tests.py')
		if run_tests.exited == 0:
			coverage_report(c, open_browser=False)

@task
def make_python_badge(c):
	cprint('[MAIN]\tInstall pybadges')
	c.run('pip install pybadges pip-autoremove', hide=True)
	cprint('[MAIN]\tCreate badge')
	c.run('python -m pybadges --left-text="Python" --right-text="3.6 | 3.7 | 3.8" '
		  '--whole-link="https://www.python.org/" --browser --embed-logo '
		  '--logo="https://dev.w3.org/SVG/tools/svgweb/samples/svg-files/python.svg"')
	cprint('[MAIN]\tUninstall pybadges')
	c.run('pip-autoremove pybadges -y', hide=True)
	c.run('pip uninstall pip-autoremove -y', hide=True)

@task
def style(c):
    """
    Run PEP style checks against Ki-nTree sourcecode
    """

    print("Running PEP style checks...")
    c.run('flake8 kintree_gui.py run_tests.py setup_inventree.py common/ config/ database/')