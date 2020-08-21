import os

from common.tools import cprint
from config import settings
from invoke import UnexpectedExit, task


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
		response = c.run('pip install -U python-Levenshtein', hide='both')
		if int(response.exited) != 0:
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
		c.run('rm -r dist build', hide='err')
	except UnexpectedExit:
		pass

@task
def package(c):
	cprint(f'[MAIN]\tPackaging Ki-nTree')
	c.run('cd dist/ && tar -czvf kintree.tgz * && cd -')

@task
def exec(c):
	cprint(f'[MAIN]\tBuilding Ki-nTree into "dist" directory')
	c.run('pyinstaller --clean --onefile '
		  '-p search/digikey_api/ -p kicad/ -p database/inventree-python/ '
		  'kintree_gui.py')

	cprint(f'[MAIN]\tCopying configuration files')
	c.run('mkdir dist/config && mkdir dist/kicad')
	c.run('cp -r config/kicad/ dist/config/')
	c.run('cp -r config/digikey/ dist/config/')
	c.run('cp -r config/inventree/ dist/config/')
	c.run('cp config/version.yaml dist/config/')
	c.run('cp -r kicad/templates/ dist/kicad/')

@task(pre=[clean], post=[package])
def build(c):
	exec(c)

@task
def test(c):
	c.run('python run_tests.py')
