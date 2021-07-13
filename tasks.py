import webbrowser

from kintree.common.tools import cprint
from invoke import UnexpectedExit, task


@task
def install(c, is_install=True):
    """
    Install Ki-nTree dependencies
    """

    if is_install:
        cprint('[MAIN]\tInstalling required dependencies')
        c.run('pip install -U wheel', hide='out')
    else:
        cprint('[MAIN]\tUpdating required dependencies')
    c.run('pip install -U -r requirements.txt', hide='out')

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
    try:
        c.run('find . -name __pycache__ | xargs rm -r', hide='err')
    except UnexpectedExit:
        pass
    try:
        c.run('rm .coverage', hide='err')
    except UnexpectedExit:
        pass
    try:
        c.run('rm .coverage.*', hide='err')
    except UnexpectedExit:
        pass
    try:
        c.run('rm -r dist/ htmlcov', hide='err')
    except UnexpectedExit:
        pass


@task
def package(c):
    import os

    cdir = os.getcwd()
    build = os.path.join(cdir, 'kintree', 'build')
    dist = os.path.join(cdir, 'kintree', 'dist')

    cprint('[MAIN]\tPackaging Ki-nTree into "dist" directory')

    # Move dist folder to root
    c.run(f'mv {dist} {cdir}', hide=True)
    # Remove build folder
    try:
        c.run(f'rm -r {build}', hide='err')
    except UnexpectedExit:
        pass


@task
def exec(c):
    cprint('[MAIN]\tBuilding Ki-nTree')
    c.run('cd kintree/ && pyinstaller --clean --onefile kintree_gui.py && cd -', hide=True)


@task(pre=[clean], post=[package])
def build(c):
    """
    Build Ki-nTree into executable file
    """

    try:
        c.run('pip show pyinstaller', hide=True)
    except UnexpectedExit:
        c.run('pip install -U pyinstaller', hide=True)

    # Uninstall typing
    c.run('pip uninstall typing -y', hide=True)
    exec(c)


@task
def setup_inventree(c):
    """
    Setup InvenTree server
    """

    c.run('python -m kintree.setup_inventree')


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
    """
    Run Ki-nTree tests
    """

    try:
        c.run('pip show coverage', hide=True)
    except UnexpectedExit:
        c.run('pip install -U coverage', hide=True)

    cprint('[MAIN]\tRunning tests using coverage\n-----')
    if setup:
        c.run('cd InvenTree/ && inv server && cd ..', asynchronous=True)
        c.run('sleep 5')
        setup_inventree = c.run('coverage run --parallel-mode -m kintree.setup_inventree')
        cprint('\n-----')
        c.run('cp -r tests/ kintree/')
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
    """
    Make badge for supported versions of Python
    """

    cprint('[MAIN]\tInstall pybadges')
    c.run('pip install pybadges pip-autoremove', hide=True)
    cprint('[MAIN]\tCreate badge')
    c.run('python -m pybadges --left-text="Python" --right-text="3.7 - 3.9" '
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

    c.run('pip install -U flake8', hide=True)
    print("Running PEP style checks...")
    c.run('flake8 tasks.py run_tests.py kintree/kintree_gui.py kintree/setup_inventree.py \
        kintree/common/ kintree/config/ kintree/database/ kintree/kicad/*.py kintree/search/*.py')
