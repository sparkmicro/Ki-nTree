import os
import sys
from enum import Enum

from common.tools import cprint
from config import config_interface

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


# VERSION
CONFIG_VERSION = os.path.join(PROJECT_DIR, 'config', 'version.yaml')
version_info = config_interface.load_file(CONFIG_VERSION, silent=False)
try:
	version = '.'.join([str(v) for v in version_info.values()])
except:
	version = '0.0.alpha'


# CONFIG FILES
CONFIG_TEMPLATES = os.path.join(PROJECT_DIR, 'config', '')
CONFIG_USER_FILES = os.path.join(PROJECT_DIR, 'config', 'user_files', '')

def create_user_config_files():
	global CONFIG_TEMPLATES
	global CONFIG_USER_FILES

	# Create user files folder if it does not exists
	if not os.path.exists(CONFIG_USER_FILES):
		os.makedirs(CONFIG_USER_FILES)
	# Create user files
	return config_interface.load_user_config_files(path_to_templates=CONFIG_TEMPLATES,
												   path_to_user_files=CONFIG_USER_FILES)

# Create user configuration files
create_user_config_files()

# Digi-Key
CONFIG_DIGIKEY_API = os.path.join(CONFIG_USER_FILES, 'digikey_api.yaml')
CONFIG_DIGIKEY_CATEGORIES = os.path.join(
	CONFIG_USER_FILES, 'digikey_categories.yaml')
CONFIG_DIGIKEY_PARAMETERS = os.path.join(
	CONFIG_USER_FILES, 'digikey_parameters.yaml')

# KiCad
CONFIG_KICAD = os.path.join(CONFIG_USER_FILES, 'kicad.yaml')
CONFIG_KICAD_CATEGORY_MAP = os.path.join(CONFIG_USER_FILES, 'kicad_map.yaml')

# Inventree
CONFIG_CATEGORIES = os.path.join(CONFIG_USER_FILES, 'categories.yaml')
CONFIG_PARAMETERS = os.path.join(CONFIG_USER_FILES, 'parameters.yaml')
CONFIG_PARAMETERS_FILTERS = os.path.join(
	CONFIG_USER_FILES, 'parameters_filters.yaml')


# DIGI-KEY
# API storage path
DIGIKEY_STORAGE_PATH = os.path.join(PROJECT_DIR, 'search', '')
# Automatic category match confidence level (from 0 to 100)
CATEGORY_MATCH_RATIO_LIMIT = 100
# Search results caching (stored in files)
CACHE_ENABLED = True
# Cache validity in days
CACHE_VALID_DAYS = 7
# Caching settings
if CACHE_ENABLED:
	search_results = {
		'directory': os.path.join(PROJECT_DIR, 'search', 'results', ''),
		'extension': '.yaml',
	}
	# Create folder if it does not exists
	if not os.path.exists(search_results['directory']):
		os.makedirs(search_results['directory'])

# Part images
search_images = os.path.join(PROJECT_DIR, 'search', 'images', '')
# Create folder if it does not exists
if not os.path.exists(search_images):
	os.makedirs(search_images)


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


# Load user settings
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
	PROJECT_DIR, 'kicad', 'templates', 'library_template.lib')


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
try:
	environment = int(os.environ.get('INVENTREE_ENV', Environment.TESTING.value))
except ValueError:
	environment = 1

# Load correct user file
if int(environment) == Environment.PRODUCTION.value:
	CONFIG_INVENTREE = os.path.join(CONFIG_USER_FILES, 'inventree_prod.yaml')
elif environment == Environment.DEVELOPMENT.value:
	CONFIG_INVENTREE = os.path.join(CONFIG_USER_FILES, 'inventree_dev.yaml')
else:
	CONFIG_INVENTREE = os.path.join(CONFIG_USER_FILES, 'inventree_test.yaml')

# Load user settings
inventree_settings = config_interface.load_inventree_user_settings(CONFIG_INVENTREE)

# Enable flag
try:
	ENABLE_INVENTREE = inventree_settings['ENABLE']
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
													  server=inventree_settings['SERVER_ADDRESS'],
													  username=inventree_settings['USERNAME'],
													  password=inventree_settings['PASSWORD'],
													  user_config_path=CONFIG_INVENTREE)
	return

# Server settings
def load_inventree_settings():
	global SERVER_ADDRESS
	global USERNAME
	global PASSWORD
	global PART_URL_ROOT

	inventree_settings = config_interface.load_inventree_user_settings(
		CONFIG_INVENTREE)

	SERVER_ADDRESS = inventree_settings['SERVER_ADDRESS']
	USERNAME = inventree_settings['USERNAME']
	PASSWORD = inventree_settings['PASSWORD']
	# Part URL
	PART_URL_ROOT = SERVER_ADDRESS + 'part/'

# Default revision
INVENTREE_DEFAULT_REV = 'A'

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
	'supplier': {},
	'manufacturer': {},
	'datasheet': None,
	'parameters': {},
}
