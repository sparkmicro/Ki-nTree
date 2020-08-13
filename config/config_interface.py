import base64
import os

import yaml
from common.tools import cprint


def load_file(file_path: str) -> dict:
	''' Safe load YAML file '''
	with open(file_path, 'r') as file:
		try:
			data = yaml.safe_load(file)#, Loader=yaml.BaseLoader)
		except yaml.YAMLError as exc:
			print(exc)
			return None

	return data

def dump_file(data: dict, file_path: str) -> bool:
	''' Safe dump YAML file '''
	with open(file_path, 'w') as file:
		try:
			yaml.safe_dump(data, file, default_flow_style=False)
		except yaml.YAMLError as exc:
			print(exc)
			return False

	return True

def load_user_config_files(path_to_templates: str, path_to_user_files: str):
	def load_config(path):
		for template_file in os.listdir(path):
			filename = os.path.basename(template_file)
			template_data = load_file(path + template_file)
			try:
				user_data = load_file(path_to_user_files + filename)
				# Join user data to template data
				user_settings = {**template_data, **user_data}
			except:
				user_settings = template_data

			dump_file(user_settings, path_to_user_files + filename)

	# Load Digi-Key configuration files
	try:
		config_files = os.path.join(path_to_templates, 'digikey', '')
		load_config(config_files)
	except:
		cprint(f'[INFO]\tWarning: Failed to load Digi-Key configuration')
	# Load InvenTree configuration files
	try:
		config_files = os.path.join(path_to_templates, 'inventree', '')
		load_config(config_files)
	except:
		cprint(f'[INFO]\tWarning: Failed to load InvenTree configuration')
	# Load KiCad configuration files
	try:
		config_files = os.path.join(path_to_templates, 'kicad', '')
		load_config(config_files)
	except:
		cprint(f'[INFO]\tWarning: Failed to load KiCad configuration')

def load_inventree_user_settings(user_config_path: str) -> dict:
	''' Load InvenTree user settings from file '''
	user_settings = load_file(user_config_path)

	try:
		# Use base64 encoding to make password unreadable inside the file
		user_settings['PASSWORD'] = base64.b64decode(user_settings['PASSWORD']).decode()
	except:
		user_settings['PASSWORD'] = ''
	
	return user_settings

def save_inventree_user_settings(enable: bool, server: str, username: str, password: str, user_config_path: str):
	''' Save InvenTree user settings to file '''
	user_settings = load_file(user_config_path)
	
	user_settings['ENABLE'] = enable
	user_settings['SERVER_ADDRESS'] = server
	user_settings['USERNAME'] = username
	# Use base64 encoding to make password unreadable inside the file
	user_settings['PASSWORD'] = base64.b64encode(password.encode())

	return dump_file(user_settings, user_config_path)

def load_library_path(user_config_path: str, silent=False):
	''' Load KiCad library from KiCad settings file '''
	user_settings = load_file(user_config_path)

	try:
		if not user_settings['KICAD_SYMBOLS_PATH'] and not silent:
			print(f'[INFO]\tEmpty KiCad library path')
		return user_settings['KICAD_SYMBOLS_PATH']
	except:
		# If not defined: use application root folder
		return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def add_library_path(user_config_path: str, category: str, symbol_library: str) -> bool:
	''' Save KiCad library to KiCad settings file '''
	user_settings = load_file(user_config_path)

	if category:
		index = category
	else:
		index = symbol_library

	if not user_settings['KICAD_LIBRARIES']:
		user_settings['KICAD_LIBRARIES'] = {}

	try:
		if symbol_library not in user_settings['KICAD_LIBRARIES'][index]:
			user_settings['KICAD_LIBRARIES'][index].append(symbol_library)
	except:
		user_settings['KICAD_LIBRARIES'][index] = [symbol_library]

	return dump_file(user_settings, user_config_path)

def load_libraries_paths(user_config_path: str, library_path: str) -> dict:
	''' Construct KiCad library files names and paths from KiCad settings file '''
	user_settings = load_file(user_config_path)

	if not os.path.exists(library_path):
		return None

	found_library_files = []
	for file in os.listdir(library_path):
		if file.endswith('.lib'):
			found_library_files.append(file.replace('.lib',''))

	symbol_libraries_paths = {}
	assigned_files = []
	try:
		for category, libraries in user_settings['KICAD_LIBRARIES'].items():
			symbol_libraries_paths[category] = {}
			if libraries:
				for library in libraries:
					if library in found_library_files:
						symbol_libraries_paths[category][library] = library_path + library + '.lib'
						assigned_files.append(library)
	except:
		pass

	for file in found_library_files:
		if file not in assigned_files:
			try:
				symbol_libraries_paths['uncategorized'].append(file)
			except:
				symbol_libraries_paths['uncategorized'] = [file]
	try:
		symbol_libraries_paths['uncategorized'] = sorted(symbol_libraries_paths['uncategorized'])
	except:
		pass

	# print(symbol_libraries_paths)
	return symbol_libraries_paths

def load_templates_paths(user_config_path: str, template_path: str) -> dict:
	''' Construct KiCad template files names and paths from KiCad settings file '''
	symbol_templates_paths = {}
	if not template_path:
		return symbol_templates_paths

	# Load configuration file
	user_settings = load_file(user_config_path)

	try:
		for category in user_settings['KICAD_TEMPLATES'].keys():
			for subcategory, file_name in user_settings['KICAD_TEMPLATES'][category].items():
				if subcategory == 'Default' and not file_name:
					file_name = 'default'
				if file_name:
					try:
						symbol_templates_paths[category][subcategory] = template_path + file_name + '.lib'
					except:
						symbol_templates_paths[category] = {subcategory: template_path + file_name + '.lib'}
	except:
		pass

	return symbol_templates_paths

def load_footprint_paths(user_config_path: str, footprint_path: str) -> dict:
	''' Construct KiCad footprint folder names and paths from KiCad settings file '''
	user_settings = load_file(user_config_path)

	if not os.path.exists(footprint_path):
		return None

	found_library_folders = [	item.replace('.pretty','') for item in os.listdir(footprint_path) \
								if os.path.isdir(footprint_path + item) ]


	footprint_libraries_paths = {}
	assigned_folders = []
	try:
		for category, libraries in user_settings['KICAD_FOOTPRINTS'].items():
			footprint_libraries_paths[category] = {}
			if libraries:
				for folder in libraries:
					footprint_libraries_paths[category][folder] = footprint_path + folder + '.pretty'
					assigned_folders.append(folder)
	except:
		pass

	for folder in found_library_folders:
		if folder not in assigned_folders:
			try:
				footprint_libraries_paths['uncategorized'].append(folder)
			except:
				footprint_libraries_paths['uncategorized'] = [folder]
	footprint_libraries_paths['uncategorized'] = sorted(footprint_libraries_paths['uncategorized'])

	return footprint_libraries_paths

def add_footprint_library(user_config_path: str, category: str, library_folder: str) -> bool:
	''' Add KiCad footprint folder name to KiCad settings file '''
	user_settings = load_file(user_config_path)

	if category:
		index = category
	else:
		index = library_folder

	if not user_settings['KICAD_FOOTPRINTS']:
		user_settings['KICAD_FOOTPRINTS'] = {}

	try:
		if library_folder not in user_settings['KICAD_FOOTPRINTS'][index]:
				user_settings['KICAD_FOOTPRINTS'][index].append(library_folder)
	except:
		user_settings['KICAD_FOOTPRINTS'][index] = [library_folder]

	return dump_file(user_settings, user_config_path)

def load_supplier_categories(supplier_config_path: str) -> dict:
	''' Load Supplier category mapping from Supplier settings file '''
	try:
		supplier_categories = load_file(supplier_config_path)
	except:
		return None

	# print(supplier_categories)
	return supplier_categories

def load_supplier_categories_inversed(supplier_config_path: str) -> dict:
	''' Load Supplier category mapping from Supplier settings file (inversed relation) '''
	supplier_categories = load_file(supplier_config_path)

	try:
		supplier_categories_inversed = {}
		for category in supplier_categories.keys():
			if supplier_categories[category]:
				for user, supplier in supplier_categories[category].items():
					# Supplier is list type
					if supplier:
						if not category in supplier_categories_inversed.keys():
							supplier_categories_inversed[category] = {}
						for item in supplier:
							supplier_categories_inversed[category][item] = user
	except:
		return None

	# print(supplier_categories_inversed)
	return supplier_categories_inversed

def add_supplier_category(categories: dict, supplier_config_path: str) -> bool:
	''' Add Supplier category mapping to Supplier settings file

		categories = {
			'Capacitors':
				{ 'Tantalum': 'Tantalum Capacitors' }
		}
	'''
	try:
		supplier_categories = load_file(supplier_config_path)
	except:
		return None

	for category in categories.keys():
		for user_subcategory, supplier_category in categories[category].items():
			try:
				supplier_category_keys = supplier_categories[category].keys()
			except:
				supplier_categories[category] = {user_subcategory: [supplier_category]}
				break

			# Function filtered
			inventree_subcategory_filter = '__' + user_subcategory
			if inventree_subcategory_filter in supplier_category_keys:
				try:
					if supplier_category not in supplier_categories[category][inventree_subcategory_filter]:
						supplier_categories[category][inventree_subcategory_filter].append(supplier_category)
					break
				except:
					pass

				try:
					supplier_categories[category][inventree_subcategory_filter] = [supplier_category]
					break
				except:
					pass
			else:
				try:
					if supplier_category not in supplier_categories[category][user_subcategory]:
						supplier_categories[category][user_subcategory].append(supplier_category)
					break
				except:
					pass

				try:
					supplier_categories[category][user_subcategory] = [supplier_category]
					break
				except:
					pass

			return False

	return dump_file(supplier_categories, supplier_config_path)

def load_category_parameters(category: str, supplier_config_path: str) -> dict:
	''' Load Supplier parameters mapping from Supplier settings file '''
	try:
		category_parameters = load_file(supplier_config_path)[category]
	except:
		return None

	# print(category_parameters)
	return category_parameters

def load_category_parameters_inversed(category: str, supplier_config_path: str) -> dict:
	''' Load Supplier parameters mapping from Supplier settings file (inversed relation) '''
	try:
		category_parameters = load_file(supplier_config_path)[category]
	except:
		return None

	category_parameters_inversed = {}
	for parameter in category_parameters.keys():
		if category_parameters[parameter]:
			for supplier_parameter in category_parameters[parameter]:
				category_parameters_inversed[supplier_parameter] = parameter

	# print(category_parameters_inversed)
	return category_parameters_inversed

def load_category_parameters_filters(category: str, supplier_config_path: str) -> list:
	''' Load Supplier parameters filters from Supplier settings file '''
	try:
		parameters_filters = load_file(supplier_config_path)[category]
	except:
		return []

	# print(parameters_filters)
	return parameters_filters

# Obsolete
def load_supplier_map(supplier_config_path: str, map_type: str, supplier='Digi-Key') -> dict:
	''' Construct Supplier categories and parameters map from Supplier settings file '''
	suppliers = ['Digi-Key', ]
	maps = ['category', 'parameter', ]
	# Check if supplier data exists
	if supplier not in suppliers:
		return None
	# Check if map data exists
	if map_type not in maps:
		return None

	try:
		supplier_maps = load_file(supplier_config_path)
	except:
		return None

	# Digi-Key
	if supplier == suppliers[0]:
		if map_type == maps[0]:
			# Return reverse dictionaries
			category_map = supplier_maps['DIGIKEY_CATEGORY_MAP']
			inversed_category_map = {}

			for category in category_map.keys():
				for inventree, supplier in category_map[category].items():
					if type(supplier) is list:
						for item in supplier:
							inversed_category_map[category][item] = inventree
					else:
						try:
							inversed_category_map[category][supplier] = inventree
						except:
							inversed_category_map[category] = {supplier: inventree}

			return inversed_category_map
		elif map_type == maps[1]:
			return supplier_maps['DIGIKEY_PARAMETER_MAP']
		
	return None
