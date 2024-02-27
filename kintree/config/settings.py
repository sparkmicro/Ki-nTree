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
USER_CONFIG_FILE = os.path.join(HOME_DIR, 'settings.yaml')
if not load_user_config():
    # Check if configuration files already exist
    if not os.path.isfile(os.path.join(CONFIG_USER_FILES, 'categories.yaml')):
        cprint('\n[ERROR]\tSome Ki-nTree configuration files seem to be missing')
        exit(-1)

# KiCad
KICAD_CONFIG_PATHS = os.path.join(CONFIG_USER_FILES, 'kicad.yaml')
KICAD_CONFIG_CATEGORY_MAP = os.path.join(CONFIG_USER_FILES, 'kicad_map.yaml')

# Inventree
CONFIG_CATEGORIES = os.path.join(CONFIG_USER_FILES, 'categories.yaml')
CONFIG_STOCK_LOCATIONS = os.path.join(CONFIG_USER_FILES, 'stock_locations.yaml')
CONFIG_PARAMETERS = os.path.join(CONFIG_USER_FILES, 'parameters.yaml')
CONFIG_PARAMETERS_FILTERS = os.path.join(
    CONFIG_USER_FILES, 'parameters_filters.yaml')

# INTERNAL PART NUMBERS
CONFIG_IPN_PATH = os.path.join(CONFIG_USER_FILES, 'internal_part_number.yaml')


def load_ipn_settings():
    global CONFIG_IPN
    CONFIG_IPN = config_interface.load_file(CONFIG_IPN_PATH)


load_ipn_settings()

# GENERAL SETTINGS
CONFIG_GENERAL_PATH = os.path.join(CONFIG_USER_FILES, 'general.yaml')
CONFIG_GENERAL = config_interface.load_file(CONFIG_GENERAL_PATH)
# Datasheets
DATASHEET_SAVE_ENABLED = CONFIG_GENERAL.get('DATASHEET_SAVE_ENABLED', False)
DATASHEET_SAVE_PATH = CONFIG_GENERAL.get('DATASHEET_SAVE_PATH', '')
# Open Browser
AUTOMATIC_BROWSER_OPEN = CONFIG_GENERAL.get('AUTOMATIC_BROWSER_OPEN', False)
# Default Supplier
DEFAULT_SUPPLIER = CONFIG_GENERAL.get('DEFAULT_SUPPLIER', 'Digi-Key')


# Load enable flags
def reload_enable_flags():
    global ENABLE_KICAD
    global ENABLE_INVENTREE
    global ENABLE_ALTERNATE
    global UPDATE_INVENTREE
    global CHECK_EXISTING

    try:
        ENABLE_KICAD = CONFIG_GENERAL.get('ENABLE_KICAD', False)
        ENABLE_INVENTREE = CONFIG_GENERAL.get('ENABLE_INVENTREE', False)
        ENABLE_ALTERNATE = CONFIG_GENERAL.get('ENABLE_ALTERNATE', False)
        UPDATE_INVENTREE = CONFIG_GENERAL.get('UPDATE_INVENTREE', False)
        CHECK_EXISTING = CONFIG_GENERAL.get('CHECK_EXISTING', True)
        return True
    except TypeError:
        pass

    return False


reload_enable_flags()

# Supported suppliers APIs
CONFIG_SUPPLIERS_PATH = os.path.join(CONFIG_USER_FILES, 'suppliers.yaml')
CONFIG_SUPPLIERS = config_interface.load_file(CONFIG_SUPPLIERS_PATH)
SUPPORTED_SUPPLIERS_API = []


# Load suppliers
def load_suppliers():
    global CONFIG_SUPPLIERS
    global SUPPORTED_SUPPLIERS_API

    SUPPORTED_SUPPLIERS_API = []
    for supplier, data in CONFIG_SUPPLIERS.items():
        if data['enable']:
            if data['name']:
                SUPPORTED_SUPPLIERS_API.append(data['name'])
            else:
                SUPPORTED_SUPPLIERS_API.append(supplier)


load_suppliers()

# Generic API user configuration
CONFIG_SUPPLIER_PARAMETERS = os.path.join(CONFIG_USER_FILES, 'supplier_parameters.yaml')
CONFIG_SEARCH_API_PATH = os.path.join(CONFIG_USER_FILES, 'search_api.yaml')
CONFIG_SEARCH_API = config_interface.load_file(CONFIG_SEARCH_API_PATH)

# Digi-Key user configuration
CONFIG_DIGIKEY = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'digikey_config.yaml'))
CONFIG_DIGIKEY_API = os.path.join(CONFIG_USER_FILES, 'digikey_api.yaml')
CONFIG_DIGIKEY_CATEGORIES = os.path.join(CONFIG_USER_FILES, 'digikey_categories.yaml')

# Mouser user configuration
CONFIG_MOUSER = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'mouser_config.yaml'))
CONFIG_MOUSER_API = os.path.join(CONFIG_USER_FILES, 'mouser_api.yaml')

# Element14 user configuration (includes Farnell, Newark and Element14)
CONFIG_ELEMENT14 = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'element14_config.yaml'))
CONFIG_ELEMENT14_API = os.path.join(CONFIG_USER_FILES, 'element14_api.yaml')

# LCSC user configuration
CONFIG_LCSC = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'lcsc_config.yaml'))
CONFIG_LCSC_API = os.path.join(CONFIG_USER_FILES, 'lcsc_api.yaml')

# TME user configuration
CONFIG_TME = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'tme_config.yaml'))
CONFIG_TME_API = os.path.join(CONFIG_USER_FILES, 'tme_api.yaml')

# Automatic category match confidence level (from 0 to 100)
CATEGORY_MATCH_RATIO_LIMIT = CONFIG_SEARCH_API.get('CATEGORY_MATCH_RATIO_LIMIT', 100)
# Search results caching (stored in files)
CACHE_ENABLED = CONFIG_SEARCH_API.get('CACHE_ENABLED', True)
# Cache validity in days
CACHE_VALID_DAYS = int(CONFIG_SEARCH_API.get('CACHE_VALID_DAYS', '7'))


# Caching settings
def load_cache_settings():
    global search_results
    global search_images
    global search_datasheets
    global CACHE_ENABLED
    global DIGIKEY_STORAGE_PATH

    USER_SETTINGS = config_interface.load_user_paths(home_dir=HOME_DIR)

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

    # Part images
    search_datasheets = os.path.join(
        USER_SETTINGS['USER_CACHE'], 'datasheets', '')
    # Create folder if it does not exists
    if not os.path.exists(search_datasheets):
        os.makedirs(search_datasheets)

    # API token storage path
    DIGIKEY_STORAGE_PATH = os.path.join(USER_SETTINGS['USER_CACHE'], '')


# Load cache settings
load_cache_settings()

# KICAD
# User Settings
KICAD_SETTINGS = {}


def load_kicad_settings():
    global KICAD_CONFIG_PATHS
    global KICAD_SETTINGS

    kicad_user_settings = config_interface.load_file(KICAD_CONFIG_PATHS, silent=False)
    if kicad_user_settings:
        KICAD_SETTINGS['KICAD_SYMBOLS_PATH'] = kicad_user_settings.get('KICAD_SYMBOLS_PATH', None)
        KICAD_SETTINGS['KICAD_TEMPLATES_PATH'] = kicad_user_settings.get('KICAD_TEMPLATES_PATH', None)
        KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'] = kicad_user_settings.get('KICAD_FOOTPRINTS_PATH', None)


# Load kicad settings
load_kicad_settings()


def set_default_supplier(value: str, save=False):
    global DEFAULT_SUPPLIER
    DEFAULT_SUPPLIER = value
    if save:
        user_settings = config_interface.load_file(os.path.join(CONFIG_USER_FILES, 'general.yaml'))
        user_settings['DEFAULT_SUPPLIER'] = value
        config_interface.dump_file(user_settings, os.path.join(CONFIG_USER_FILES, 'general.yaml'))
    return


# Library Paths
if not ENABLE_TEST:
    symbol_libraries_paths = config_interface.load_libraries_paths(
        KICAD_CONFIG_CATEGORY_MAP,
        KICAD_SETTINGS['KICAD_SYMBOLS_PATH'],
    )
# cprint(symbol_libraries_paths)

# Template Paths
symbol_templates_paths = config_interface.load_templates_paths(
    KICAD_CONFIG_CATEGORY_MAP,
    KICAD_SETTINGS['KICAD_TEMPLATES_PATH'],
)
# cprint(symbol_templates_paths)

# Footprint Libraries
footprint_libraries_paths = config_interface.load_footprint_paths(
    KICAD_CONFIG_CATEGORY_MAP,
    KICAD_SETTINGS['KICAD_FOOTPRINTS_PATH'],
)
# cprint(footprint_libraries_paths)
footprint_name_default = 'TBD'

AUTO_GENERATE_LIB = True
symbol_template_lib = os.path.join(
    PROJECT_DIR,
    'kicad',
    'templates',
    'library_template.kicad_sym'
)


# INVENTREE
class Environment(Enum):
    '''
    Server/Remote Development: DEVELOPMENT
    Server/Remote Production: PRODUCTION
    '''
    DEVELOPMENT = 0
    PRODUCTION = 1


# Pick environment
environment = CONFIG_GENERAL.get('INVENTREE_ENV', None)
environment = os.environ.get('INVENTREE_ENV', environment)

try:
    environment = int(environment)
except TypeError:
    environment = 0

# Load correct user file
if environment == Environment.PRODUCTION.value:
    INVENTREE_CONFIG = os.path.join(CONFIG_USER_FILES, 'inventree_prod.yaml')
else:
    INVENTREE_CONFIG = os.path.join(CONFIG_USER_FILES, 'inventree_dev.yaml')

# Load user settings
inventree_settings = config_interface.load_inventree_user_settings(INVENTREE_CONFIG)


# Server settings
def load_inventree_settings():
    global SERVER_ADDRESS
    global USERNAME
    global PASSWORD
    global ENABLE_PROXY
    global PROXIES
    global PART_URL_ROOT
    global DATASHEET_UPLOAD
    global PRICING_UPLOAD

    inventree_settings = config_interface.load_inventree_user_settings(INVENTREE_CONFIG)

    SERVER_ADDRESS = inventree_settings.get('SERVER_ADDRESS', None)
    USERNAME = inventree_settings.get('USERNAME', None)
    PASSWORD = inventree_settings.get('PASSWORD', None)
    ENABLE_PROXY = inventree_settings.get('ENABLE_PROXY', False)
    PROXIES = inventree_settings.get('PROXIES', None)
    DATASHEET_UPLOAD = inventree_settings.get('DATASHEET_UPLOAD', False)
    PRICING_UPLOAD = inventree_settings.get('PRICING_UPLOAD', False)
    # Part URL
    if SERVER_ADDRESS:
        # If missing, append slash to root URL
        root_url = SERVER_ADDRESS
        if not SERVER_ADDRESS.endswith('/'):
            root_url = root_url + '/'
        # Set part URL
        PART_URL_ROOT = root_url + 'part/'


# InvenTree part dictionary template
inventree_part_template = {
    'name': None,
    'description': None,
    'IPN': None,
    'revision': None,
    'keywords': None,
    'image': None,
    'inventree_url': None,
    'manufacturer_name': None,
    'manufacturer_part_number': None,
    'datasheet': None,
    'supplier_name': None,
    'supplier_part_number': None,
    'supplier_link': None,
    'parameters': {},
}


# Enable flags
def set_enable_flag(key: str, value: bool):
    global CONFIG_GENERAL

    user_settings = CONFIG_GENERAL
    if key in ['kicad', 'inventree', 'alternate', 'update', 'check_existing']:
        if key == 'kicad':
            user_settings['ENABLE_KICAD'] = value
        elif key == 'inventree':
            user_settings['ENABLE_INVENTREE'] = value
        elif key == 'alternate':
            user_settings['ENABLE_ALTERNATE'] = value
        elif key == 'update':
            user_settings['UPDATE_INVENTREE'] = value
        elif key == 'check_existing':
            user_settings['CHECK_EXISTING'] = value

        # Save
        config_interface.dump_file(
            data=user_settings,
            file_path=os.path.join(CONFIG_USER_FILES, 'general.yaml'),
        )

    return reload_enable_flags()
