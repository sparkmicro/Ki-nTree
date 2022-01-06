import os
import sys
import platform
from enum import Enum

from ..common.tools import cprint
from .import config_interface

# DEBUG
# Testing
ENABLE_TEST = False
# Silent Mode
SILENT = False
# Debug
HIDE_DEBUG = True


def enable_test_mode():
    global ENABLE_TEST
    global SILENT
    ENABLE_TEST = True
    SILENT = True


# PATHS
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    PROJECT_DIR = os.path.abspath(os.path.dirname(sys.executable))
else:
    PROJECT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
# InvenTree API
sys.path.append(os.path.join(PROJECT_DIR, 'database', 'inventree-python'))
# Digi-Key API
sys.path.append(os.path.join(PROJECT_DIR, 'search', 'digikey_api'))
# KiCad Library Utils
sys.path.append(os.path.join(PROJECT_DIR, 'kicad'))
# Tests
sys.path.append(os.path.join(PROJECT_DIR, 'tests'))

# HOME FOLDER
USER_HOME = os.path.expanduser("~")
# APP NAME
APP_NAME = 'kintree'
# CONFIG PATH
if platform.system() == 'Linux':
    HOME_DIR = os.path.join(USER_HOME, '.config', APP_NAME, '')
else:
    HOME_DIR = os.path.join(USER_HOME, APP_NAME, '')
# Create config path if it does not exists
if not os.path.exists(HOME_DIR):
    os.makedirs(HOME_DIR, exist_ok=True)


# USER AND CONFIG FILES
def load_user_config():
    global USER_SETTINGS
    global CONFIG_ROOT
    global CONFIG_USER_FILES

    USER_SETTINGS = config_interface.load_user_paths(home_dir=HOME_DIR)
    CONFIG_ROOT = os.path.join(PROJECT_DIR, 'config', '')
    CONFIG_USER_FILES = os.path.join(USER_SETTINGS['USER_FILES'], '')

    # Create user files folder if it does not exists
    if not os.path.exists(CONFIG_USER_FILES):
        os.makedirs(CONFIG_USER_FILES)
    # Create user files
    return config_interface.load_user_config_files(path_to_root=CONFIG_ROOT,
                                                   path_to_user_files=CONFIG_USER_FILES,
                                                   silent=HIDE_DEBUG)


# Load user config
if not load_user_config():
    # Check if configuration files already exist
    if not os.path.isfile(os.path.join(CONFIG_USER_FILES, 'categories.yaml')):
        cprint('\n[ERROR]\tSome Ki-nTree configuration files seem to be missing')
        exit(-1)

# Common to search APIs
CONFIG_SUPPLIER_PARAMETERS = os.path.join(CONFIG_USER_FILES, 'supplier_parameters.yaml')

# Digi-Key
CONFIG_DIGIKEY_API = os.path.join(CONFIG_USER_FILES, 'digikey_api.yaml')
CONFIG_DIGIKEY_CATEGORIES = os.path.join(CONFIG_USER_FILES, 'digikey_categories.yaml')
# CONFIG_DIGIKEY_PARAMETERS = os.path.join(CONFIG_USER_FILES, 'digikey_parameters.yaml')

# Mouser
CONFIG_MOUSER_API = os.path.join(CONFIG_USER_FILES, 'mouser_api.yaml')

# KiCad
CONFIG_KICAD = os.path.join(CONFIG_USER_FILES, 'kicad.yaml')
CONFIG_KICAD_CATEGORY_MAP = os.path.join(CONFIG_USER_FILES, 'kicad_map.yaml')

# Inventree
CONFIG_CATEGORIES = os.path.join(CONFIG_USER_FILES, 'categories.yaml')
CONFIG_PARAMETERS = os.path.join(CONFIG_USER_FILES, 'parameters.yaml')
CONFIG_PARAMETERS_FILTERS = os.path.join(
    CONFIG_USER_FILES, 'parameters_filters.yaml')

# INTERNAL PART NUMBERS
CONFIG_IPN = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'internal_part_number.yaml'))
IPN_UNIQUE_ID_LENGTH = CONFIG_IPN.get('IPN_UNIQUE_ID_LENGTH', 6)
IPN_USE_FIXED_PREFIX = CONFIG_IPN.get('IPN_USE_FIXED_PREFIX', False)
if IPN_USE_FIXED_PREFIX:
    IPN_PREFIX = CONFIG_IPN.get('IPN_PREFIX', '')
IPN_USE_VARIANT_SUFFIX = CONFIG_IPN.get('IPN_USE_VARIANT_SUFFIX', True)
if IPN_USE_VARIANT_SUFFIX:
    IPN_VARIANT_SUFFIX = CONFIG_IPN.get('IPN_VARIANT_SUFFIX', '00')

# GENERAL SETTINGS
CONFIG_GENERAL = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'general.yaml'))
AUTOMATIC_BROWSER_OPEN = CONFIG_GENERAL.get('AUTOMATIC_BROWSER_OPEN', False)

# Supported suppliers APIs
SUPPORTED_SUPPLIERS_API = ['Digi-Key', 'Mouser', 'LCSC']

# Digi-Key user configuration
CONFIG_DIGIKEY = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'digikey_config.yaml'))

# LCSC user configuration
CONFIG_LCSC = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'lcsc_config.yaml'))

# Mouser user configuration
CONFIG_MOUSER = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'mouser_config.yaml'))

# Generic API user configuration
CONFIG_SEARCH_API = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'search_api.yaml'))

# Automatic category match confidence level (from 0 to 100)
CATEGORY_MATCH_RATIO_LIMIT = CONFIG_DIGIKEY.get('CATEGORY_MATCH_RATIO_LIMIT', 100)
# Search results caching (stored in files)
CACHE_ENABLED = CONFIG_DIGIKEY.get('CACHE_ENABLED', True)
# Cache validity in days
CACHE_VALID_DAYS = CONFIG_DIGIKEY.get('CACHE_VALID_DAYS', 7)


# Caching settings
def load_cache_settings():
    global search_results
    global search_images
    global CACHE_ENABLED
    global DIGIKEY_STORAGE_PATH
    
    USER_SETTINGS = config_interface.load_user_paths(home_dir=HOME_DIR)

    if CACHE_ENABLED:
        search_results = {
            'directory': os.path.join(USER_SETTINGS['USER_CACHE'], 'search', ''),
            'extension': '.yaml',
        }
        # Create folder if it does not exists
        if not os.path.exists(search_results['directory']):
            os.makedirs(search_results['directory'])

    # Part images
    search_images = os.path.join(USER_SETTINGS['USER_CACHE'], 'images', '')
    # Create folder if it does not exists
    if not os.path.exists(search_images):
        os.makedirs(search_images)

    # API token storage path
    DIGIKEY_STORAGE_PATH = os.path.join(USER_SETTINGS['USER_CACHE'], '')


# Load cache settings
load_cache_settings()

# KICAD
# User Settings
KICAD_SYMBOLS_PATH = ''
KICAD_TEMPLATES_PATH = ''
KICAD_FOOTPRINTS_PATH = ''


def load_kicad_settings():
    global CONFIG_KICAD
    global KICAD_SYMBOLS_PATH
    global KICAD_TEMPLATES_PATH
    global KICAD_FOOTPRINTS_PATH
    global ENABLE_KICAD

    kicad_user_settings = config_interface.load_file(CONFIG_KICAD, silent=False)
    if kicad_user_settings:
        KICAD_SYMBOLS_PATH = kicad_user_settings.get('KICAD_SYMBOLS_PATH', None)
        KICAD_TEMPLATES_PATH = kicad_user_settings.get('KICAD_TEMPLATES_PATH', None)
        KICAD_FOOTPRINTS_PATH = kicad_user_settings.get('KICAD_FOOTPRINTS_PATH', None)
        ENABLE_KICAD = kicad_user_settings.get('KICAD_ENABLE', None)


# Load kicad settings
load_kicad_settings()


# Enable flag
def set_kicad_enable_flag(value: bool, save=False):
    global ENABLE_KICAD
    ENABLE_KICAD = value
    if save:
        global CONFIG_KICAD
        kicad_user_settings = config_interface.load_inventree_user_settings(
            CONFIG_KICAD)
        kicad_user_settings['KICAD_ENABLE'] = value
        config_interface.dump_file(kicad_user_settings, CONFIG_KICAD)
    return


# Library Paths
if not ENABLE_TEST:
    symbol_libraries_paths = config_interface.load_libraries_paths(
        CONFIG_KICAD_CATEGORY_MAP, KICAD_SYMBOLS_PATH)
# cprint(symbol_libraries_paths)

# Template Paths
symbol_templates_paths = config_interface.load_templates_paths(
    CONFIG_KICAD_CATEGORY_MAP, KICAD_TEMPLATES_PATH)
# cprint(symbol_templates_paths)

# Footprint Libraries
footprint_libraries_paths = config_interface.load_footprint_paths(
    CONFIG_KICAD_CATEGORY_MAP, KICAD_FOOTPRINTS_PATH)
# cprint(footprint_libraries_paths)
footprint_name_default = 'TBD'

AUTO_GENERATE_LIB = True
symbol_template_lib = os.path.join(
    PROJECT_DIR, 'kicad', 'templates', 'library_template.kicad_sym')


# INVENTREE
class Environment(Enum):
    '''
    Local Development/Testing: TESTING
    Server/Remote Development: DEVELOPMENT
    Server/Remote Production: PRODUCTION
    '''
    TESTING = 0
    DEVELOPMENT = 1
    PRODUCTION = 2


# Pick environment
environment = CONFIG_GENERAL.get('INVENTREE_ENV', None)
environment = os.environ.get('INVENTREE_ENV', environment)

try:
    environment = int(environment)
except TypeError:
    environment = Environment.TESTING.value

# Load correct user file
if environment == Environment.PRODUCTION.value:
    CONFIG_INVENTREE = os.path.join(CONFIG_USER_FILES, 'inventree_prod.yaml')
elif environment == Environment.DEVELOPMENT.value:
    CONFIG_INVENTREE = os.path.join(CONFIG_USER_FILES, 'inventree_dev.yaml')
else:
    CONFIG_INVENTREE = os.path.join(CONFIG_USER_FILES, 'inventree_test.yaml')

# Load user settings
inventree_settings = config_interface.load_inventree_user_settings(CONFIG_INVENTREE)

# Enable flag
try:
    ENABLE_INVENTREE = inventree_settings.get('ENABLE', False)
except TypeError:
    pass


def set_inventree_enable_flag(value: bool, save=False):
    global ENABLE_INVENTREE
    ENABLE_INVENTREE = value
    if save:
        global CONFIG_INVENTREE
        inventree_settings = config_interface.load_inventree_user_settings(CONFIG_INVENTREE)
        inventree_settings['ENABLE'] = value
        config_interface.save_inventree_user_settings(enable=inventree_settings['ENABLE'],
                                                      server=inventree_settings.get('SERVER_ADDRESS', None),
                                                      username=inventree_settings.get('USERNAME', None),
                                                      password=inventree_settings.get('PASSWORD', None),
                                                      user_config_path=CONFIG_INVENTREE)
    return


# Server settings
def load_inventree_settings():
    global SERVER_ADDRESS
    global USERNAME
    global PASSWORD
    global PART_URL_ROOT

    inventree_settings = config_interface.load_inventree_user_settings(CONFIG_INVENTREE)

    SERVER_ADDRESS = inventree_settings.get('SERVER_ADDRESS', None)
    USERNAME = inventree_settings.get('USERNAME', None)
    PASSWORD = inventree_settings.get('PASSWORD', None)
    # Part URL
    if SERVER_ADDRESS:
        # If missing, append slash to root URL
        root_url = SERVER_ADDRESS
        if not SERVER_ADDRESS.endswith('/'):
            root_url = root_url + '/'
        # Set part URL
        PART_URL_ROOT = root_url + 'part/'


# Default revision
INVENTREE_DEFAULT_REV = inventree_settings.get('INVENTREE_DEFAULT_REV', 'A')

# InvenTree part dictionary template
inventree_part_template = {
    'category': [None, None],
    'name': None,
    'description': None,
    'IPN': None,
    'revision': None,
    'keywords': None,
    'image': None,
    'inventree_url': None,
    'manufacturer': {},
    'datasheet': None,
    'supplier': {},
    'supplier_link': None,
    'parameters': {},
}
