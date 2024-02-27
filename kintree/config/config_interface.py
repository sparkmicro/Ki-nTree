import base64
import copy
import os
from sys import platform

import yaml
from ..common.tools import cprint

FUNCTION_FILTER_KEY = '__'


def load_file(file_path: str, silent=True) -> dict:
    ''' Safe load YAML file '''
    try:
        with open(file_path, 'r') as file:
            try:
                data = yaml.safe_load(file)
            except yaml.YAMLError as exc:
                print(exc)
                return None
    except FileNotFoundError:
        cprint(f'[ERROR]\tFile {file_path} does not exists!', silent=silent)
        return None

    return data


def dump_file(data: dict, file_path: str) -> bool:
    ''' Safe dump YAML file '''
    with open(file_path, 'w') as file:
        try:
            if platform == "win32":
                yaml.safe_dump(data, file, default_flow_style=False)
            else:
                yaml.safe_dump(data, file, default_flow_style=False, allow_unicode=True)
        except yaml.YAMLError as exc:
            print(exc)
            return False

    return True


def load_user_paths(home_dir='') -> dict:
    ''' Load user config and cache paths '''

    user_settings_file = os.path.join(home_dir, 'settings.yaml')
    user_config = load_file(user_settings_file)

    if not user_config:
        user_config = {
            'USER_FILES': os.path.join(home_dir, 'user', ''),
            'USER_CACHE': os.path.join(home_dir, 'cache', ''),
        }
        dump_file(user_config, user_settings_file)

    return user_config


def load_user_config_files(path_to_root: str, path_to_user_files: str, silent=True) -> bool:
    ''' Load user configuration files '''
    result = True

    def load_config(path):
        for template_file in os.listdir(path):
            filename = os.path.basename(template_file)
            template_data = load_file(os.path.join(path, filename))
            try:
                user_data = load_file(os.path.join(path_to_user_files, filename))
                if list(template_data.keys()) == list(user_data.keys()):
                    # Join user data to template data
                    user_settings = {**template_data, **user_data}
                else:
                    user_settings = user_data
            except (TypeError, AttributeError):
                cprint(f'[INFO]\tCreating new {filename} configuration file', silent=silent)
                # Config file does not exists
                user_settings = template_data

            dump_file(user_settings, os.path.join(path_to_user_files, filename))

    for dir in ['user', 'inventree', 'kicad', 'digikey', 'mouser', 'element14', 'lcsc', 'tme']:
        try:
            # Load configuration
            config_files = os.path.join(path_to_root, dir, '')
            load_config(config_files)
        except FileNotFoundError:
            cprint(f'[INFO]\tWarning: Failed to load {dir.title()} configuration', silent=silent)
            result = False

    return result


def load_inventree_user_settings(user_config_path: str) -> dict:
    ''' Load InvenTree user settings from file '''
    user_settings = load_file(user_config_path)

    try:
        password = user_settings.get('PASSWORD', None)
    except AttributeError:
        return user_settings

    try:
        # Use base64 encoding to make password unreadable inside the file
        user_settings['PASSWORD'] = base64.b64decode(password).decode()
    except TypeError:
        user_settings['PASSWORD'] = ''

    if 'ENABLE_PROXY' not in user_settings:
        user_settings['ENABLE_PROXY'] = False
    proxies = user_settings.get('PROXIES', None)
    if not proxies:
        user_settings['PROXY'] = ''
    else:
        # loading the proxy independent if it is http or https
        user_settings['PROXY'] = list(proxies.values())[0]

    if 'DATASHEET_UPLOAD' not in user_settings:
        user_settings['DATASHEET_UPLOAD'] = False
    if 'PRICING_UPLOAD' not in user_settings:
        user_settings['PRICING_UPLOAD'] = False
    return user_settings


def save_inventree_user_settings(enable: bool,
                                 server: str,
                                 username: str,
                                 password: str,
                                 enable_proxy: bool,
                                 proxies: dict,
                                 datasheet_upload: bool,
                                 pricing_upload: bool,
                                 user_config_path: str):
    ''' Save InvenTree user settings to file '''
    user_settings = {}

    user_settings['ENABLE'] = enable
    user_settings['SERVER_ADDRESS'] = server
    user_settings['USERNAME'] = username
    # Use base64 encoding to make password unreadable inside the file
    user_settings['PASSWORD'] = base64.b64encode(password.encode())
    user_settings['ENABLE_PROXY'] = enable_proxy
    user_settings['PROXIES'] = proxies
    user_settings['DATASHEET_UPLOAD'] = datasheet_upload
    user_settings['PRICING_UPLOAD'] = pricing_upload

    return dump_file(user_settings, user_config_path)


def load_library_path(user_config_path: str, silent=False):
    ''' Load KiCad library from KiCad settings file '''
    user_settings = load_file(user_config_path)

    try:
        if not user_settings['KICAD_SYMBOLS_PATH'] and not silent:
            print('[INFO]\tEmpty KiCad library path')
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
        if file.endswith('.kicad_sym'):
            found_library_files.append(file.replace('.kicad_sym', ''))

    symbol_libraries_paths = {}
    assigned_files = []
    try:
        for category, libraries in user_settings['KICAD_LIBRARIES'].items():
            symbol_libraries_paths[category] = {}
            if libraries:
                for library in libraries:
                    if library in found_library_files:
                        symbol_libraries_paths[category][library] = library_path + \
                            library + '.kicad_sym'
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
        symbol_libraries_paths['uncategorized'] = sorted(
            symbol_libraries_paths['uncategorized'])
    except:
        pass

    # Check that library paths are loaded
    path_loaded = False
    for category, paths in symbol_libraries_paths.items():
        if paths:
            path_loaded = True
            break
    if not path_loaded:
        return None

    # print(symbol_libraries_paths)
    return symbol_libraries_paths


def load_templates_paths(user_config_path: str, template_path: str) -> dict:
    ''' Construct KiCad template files names and paths from KiCad settings file '''
    symbol_templates_paths = {}
    if not template_path or not os.path.exists(template_path):
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
                        symbol_templates_paths[category][subcategory] = template_path + \
                            file_name + '.kicad_sym'
                    except KeyError:
                        symbol_templates_paths[category] = {
                            subcategory: template_path + file_name + '.kicad_sym'
                        }
    except:
        pass

    return symbol_templates_paths


def load_footprint_paths(user_config_path: str, footprint_path: str) -> dict:
    ''' Construct KiCad footprint folder names and paths from KiCad settings file '''
    user_settings = load_file(user_config_path)

    if not os.path.exists(footprint_path):
        return None

    found_library_folders = [item.replace('.pretty', '') for item in os.listdir(footprint_path)
                             if os.path.isdir(footprint_path + item)]

    footprint_libraries_paths = {}
    assigned_folders = []
    try:
        for category, libraries in user_settings['KICAD_FOOTPRINTS'].items():
            footprint_libraries_paths[category] = {}
            if libraries:
                for folder in libraries:
                    footprint_libraries_paths[category][folder] = footprint_path + \
                        folder + '.pretty'
                    assigned_folders.append(folder)
    except:
        pass

    for folder in found_library_folders:
        if folder not in assigned_folders:
            try:
                footprint_libraries_paths['uncategorized'].append(folder)
            except:
                footprint_libraries_paths['uncategorized'] = [folder]

        # Sort uncategorized library paths
        footprint_libraries_paths['uncategorized'] = sorted(
            footprint_libraries_paths.get('uncategorized', []))

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


def load_supplier_categories(supplier_config_path: str, clean=False) -> dict:
    ''' Load Supplier category mapping from Supplier settings file '''
    supplier_categories = load_file(supplier_config_path)

    if clean:
        clean_supplier_categories = copy.deepcopy(supplier_categories)

        for category in supplier_categories:
            for subcategory in supplier_categories[category]:
                if FUNCTION_FILTER_KEY in subcategory:
                    clean_supplier_categories[category][subcategory.replace(FUNCTION_FILTER_KEY, '')] \
                        = supplier_categories[category][subcategory]
                    del clean_supplier_categories[category][subcategory]

        return clean_supplier_categories

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
                        if category not in supplier_categories_inversed.keys():
                            supplier_categories_inversed[category] = {}
                        for item in supplier:
                            supplier_categories_inversed[category][item] = user
    except:
        return None

    # print(supplier_categories_inversed)
    return supplier_categories_inversed


def sync_inventree_supplier_categories(inventree_config_path: str, supplier_config_path: str) -> dict:
    ''' Synchronize supplier categories dict from InvenTree categories '''
    inventree_categories = load_file(inventree_config_path)['CATEGORIES']
    supplier_categories = load_supplier_categories(supplier_config_path, clean=True)
    updated_supplier_categories = copy.deepcopy(supplier_categories)

    try:
        for category in inventree_categories:
            if category not in supplier_categories.keys():
                updated_supplier_categories[category] = inventree_categories[category]
    except:
        pass

    return updated_supplier_categories


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
                supplier_categories[category] = {
                    user_subcategory: [supplier_category]}
                break

            # Function filtered
            inventree_subcategory_filter = FUNCTION_FILTER_KEY + user_subcategory
            if inventree_subcategory_filter in supplier_category_keys:
                try:
                    if supplier_category not in supplier_categories[category][inventree_subcategory_filter]:
                        supplier_categories[category][inventree_subcategory_filter].append(
                            supplier_category)
                    break
                except:
                    pass

                try:
                    supplier_categories[category][inventree_subcategory_filter] = [
                        supplier_category]
                    break
                except:
                    pass
            else:
                try:
                    if supplier_category not in supplier_categories[category][user_subcategory]:
                        supplier_categories[category][user_subcategory].append(
                            supplier_category)
                    break
                except:
                    pass

                try:
                    supplier_categories[category][user_subcategory] = [
                        supplier_category]
                    break
                except:
                    pass

            return False

    return dump_file(supplier_categories, supplier_config_path)


def load_category_parameters(categories: list, supplier_config_path: str) -> dict:
    ''' Load Supplier parameters mapping from Supplier settings file '''
    def find_parameters(output_dict, category_list):
        category_parameters = None
        combined = ''
        for category in reversed(category_list):
            if category:
                combined = category + combined
            if combined in category_file:
                category_parameters = category_file[combined]
                break
            if category in category_file:
                category_parameters = category_file[category]
                break
            combined = '/' + combined
        if not category_parameters:
            return
        if 'parent' in category_parameters:
            for parent in category_parameters['parent']:
                find_parameters(output_dict, [parent])
            del category_parameters['parent']

        for parameter in category_parameters.keys():
            if category_parameters[parameter]:
                for supplier_parameter in category_parameters[parameter]:
                    output_dict[supplier_parameter] = parameter

    try:
        category_file = load_file(supplier_config_path)
    except:
        return None
    category_parameters_inversed = {}

    find_parameters(category_parameters_inversed, categories)

    return category_parameters_inversed


def load_category_parameters_filters(category: str, supplier_config_path: str) -> list:
    ''' Load Supplier parameters filters from Supplier settings file '''
    try:
        parameters_filters = load_file(supplier_config_path)[category]
    except:
        return []

    # print(parameters_filters)
    return parameters_filters
