import copy
import os

from ..config import settings
from ..common import part_tools, progress
from ..common.tools import cprint
from ..config import config_interface
from ..database import inventree_api
from fuzzywuzzy import fuzz
from ..search import search_api, digikey_api, mouser_api, lcsc_api


def connect_to_server(timeout=5) -> bool:
    ''' Connect to InvenTree server using user settings '''
    connect = False
    settings.load_inventree_settings()

    try:
        connect = inventree_api.connect(server=settings.SERVER_ADDRESS,
                                        username=settings.USERNAME,
                                        password=settings.PASSWORD,
                                        connect_timeout=timeout)
    except TimeoutError:
        pass

    if not connect:
        if not settings.SERVER_ADDRESS:
            cprint('[TREE]\tError connecting to InvenTree server: missing server address')
            return connect
        if not settings.USERNAME:
            cprint('[TREE]\tError connecting to InvenTree server: missing username')
            return connect
        if not settings.PASSWORD:
            cprint('[TREE]\tError connecting to InvenTree server: missing password')
            return connect
        cprint('[TREE]\tError connecting to InvenTree server: invalid address, username or password')
    else:
        env = [env_type.name for env_type in settings.Environment
               if env_type.value == settings.environment][0]
        cprint(f'[TREE]\tSuccessfully connected to InvenTree server (ENV={env})', silent=settings.SILENT)

    return connect


def get_categories(part_info: dict, supplier_only=False) -> list:
    ''' Find categories from part supplier data, use "somewhat automatic" matching '''
    categories = [None, None]

    try:
        supplier_category = str(part_info['category'])
        supplier_subcategory = str(part_info['subcategory'])
    except KeyError:
        return categories

    # Return supplier category, if match not needed
    if supplier_only:
        categories[0] = supplier_category
        categories[1] = supplier_subcategory
        return categories

    function_filter = False
    # TODO: Make 'filter_parameter' user defined?
    filter_parameter = 'Function Type'

    # Check existing matches
    # Load inversed category map
    category_map = config_interface.load_supplier_categories_inversed(supplier_config_path=settings.CONFIG_DIGIKEY_CATEGORIES)

    try:
        for inventree_category in category_map.keys():
            for key, inventree_subcategory in category_map[inventree_category].items():
                if supplier_subcategory == key:
                    categories[0] = inventree_category
                    # Check if filtering by function
                    if inventree_subcategory.startswith(config_interface.FUNCTION_FILTER_KEY):
                        function_filter = True

                    # Save subcategory if not function filtered
                    if not function_filter:
                        categories[1] = inventree_subcategory

                    break
    except:
        pass

    # Function Filter
    if not categories[1] and function_filter:
        cprint(f'[INFO]\tSubcategory is filtered using "{filter_parameter}" parameter', silent=settings.SILENT, end='')
        # Load parameter map
        parameter_map = config_interface.load_category_parameters(categories[0], settings.CONFIG_SUPPLIER_PARAMETERS)
        # Build compare list
        compare = []
        for supplier_parameter, inventree_parameter in parameter_map.items():
            if (supplier_parameter in part_info['parameters'].keys() and inventree_parameter == filter_parameter):
                compare.append(part_info['parameters'][supplier_parameter])

        # Load subcategory map
        category_map = config_interface.load_supplier_categories(supplier_config_path=settings.CONFIG_DIGIKEY_CATEGORIES)[categories[0]]
        for inventree_subcategory in category_map.keys():
            for item in compare:
                fuzzy_match = fuzz.partial_ratio(inventree_subcategory, item)
                display_result = f'"{inventree_subcategory}" ?= "{item}"'.ljust(50)
                cprint(f'{display_result} => {fuzzy_match}', silent=settings.HIDE_DEBUG)
                if fuzzy_match >= settings.CATEGORY_MATCH_RATIO_LIMIT:
                    categories[1] = inventree_subcategory.replace(config_interface.FUNCTION_FILTER_KEY, '')
                    break

            if categories[1]:
                cprint('\t[ PASS ]', silent=settings.SILENT)
                break

    if not categories[1] and function_filter:
        cprint('\t[ FAILED ]', silent=settings.SILENT)

    # Automatic Match
    if not (categories[0] and categories[1]):
        # Load category map
        category_map = config_interface.load_supplier_categories(supplier_config_path=settings.CONFIG_DIGIKEY_CATEGORIES)

        def find_supplier_category_match(supplier_category: str, ignore_categories=False):
            # Check for match with Inventree categories
            category_match = None
            subcategory_match = None

            for inventree_category in category_map.keys():
                fuzzy_match = 0
                
                if not ignore_categories:
                    fuzzy_match = fuzz.partial_ratio(supplier_category, inventree_category)
                    display_result = f'"{supplier_category}" ?= "{inventree_category}"'.ljust(50)
                    cprint(f'{display_result} => {fuzzy_match}', silent=settings.HIDE_DEBUG)

                if fuzzy_match < settings.CATEGORY_MATCH_RATIO_LIMIT and category_map[inventree_category]:
                    # Compare to subcategories
                    for inventree_subcategory in category_map[inventree_category]:
                        fuzzy_match = fuzz.partial_ratio(supplier_category, inventree_subcategory)
                        display_result = f'"{supplier_category}" ?= "{inventree_subcategory}"'.ljust(50)
                        cprint(f'{display_result} => {fuzzy_match}', silent=settings.HIDE_DEBUG)

                        if fuzzy_match >= settings.CATEGORY_MATCH_RATIO_LIMIT:
                            subcategory_match = inventree_subcategory
                            break

                if fuzzy_match >= settings.CATEGORY_MATCH_RATIO_LIMIT:
                    category_match = inventree_category
                    break

            return category_match, subcategory_match

        # Find category and subcategories match
        category, subcategory = find_supplier_category_match(supplier_category)
        if category:
            categories[0] = category
        if subcategory:
            categories[1] = subcategory

        # Run match with supplier subcategory
        if not categories[0] or not categories[1]:
            if categories[0]:
                # If category was found: ignore them for the comparison
                category, subcategory = find_supplier_category_match(supplier_subcategory, ignore_categories=True)
            else:
                category, subcategory = find_supplier_category_match(supplier_subcategory)

        if category and not categories[0]:
            categories[0] = category
        if subcategory and not categories[1]:
            categories[1] = subcategory

    # Final checks
    if not categories[0]:
        cprint(f'[INFO]\tWarning: "{part_info["category"]}" did not match any supplier category ', silent=settings.SILENT)
    else:
        cprint(f'[INFO]\tCategory: "{categories[0]}"', silent=settings.SILENT)
    if not categories[1]:
        cprint(f'[INFO]\tWarning: "{part_info["subcategory"]}" did not match any supplier subcategory ', silent=settings.SILENT)
    else:
        cprint(f'[INFO]\tSubcategory: "{categories[1]}"', silent=settings.SILENT)

    return categories


def translate_form_to_inventree(part_info: dict, categories: list, is_custom=False) -> dict:
    ''' Using supplier part data and categories, fill-in InvenTree part dictionary '''

    # Copy template
    inventree_part = copy.deepcopy(settings.inventree_part_template)

    # Translate form data to inventree part
    inventree_part['category'][0] = categories[0]
    inventree_part['category'][1] = categories[1]
    inventree_part['name'] = part_info['name']
    inventree_part['description'] = part_info['description']
    inventree_part['revision'] = part_info['revision']
    inventree_part['keywords'] = part_info['keywords']
    inventree_part['supplier'] = {
        part_info['supplier_name']: [
            part_info['supplier_part_number'],
        ],
    }
    inventree_part['manufacturer'] = {
        part_info['manufacturer_name']: [
            part_info['manufacturer_part_number'],
        ],
    }
    # Replace whitespaces in URL
    inventree_part['supplier_link'] = part_info['supplier_link'].replace(' ', '%20')
    inventree_part['datasheet'] = part_info['datasheet'].replace(' ', '%20')
    # Image URL is not shown to user so force default key/value
    inventree_part['image'] = part_info['image'].replace(' ', '%20')

    # Load parameters map
    parameter_map = config_interface.load_category_parameters(category=inventree_part["category"][0],
                                                              supplier_config_path=settings.CONFIG_SUPPLIER_PARAMETERS, )

    if not is_custom:
        # Add Parameters
        if parameter_map:
            for supplier_param, inventree_param in parameter_map.items():
                # Some parameters may not be mapped
                if inventree_param not in inventree_part['parameters'].keys():
                    if supplier_param != 'Manufacturer Part Number':
                        try:
                            parameter_value = part_tools.clean_parameter_value(category=categories[0],
                                                                               name=supplier_param,
                                                                               value=part_info['parameters'][supplier_param])
                            inventree_part['parameters'][inventree_param] = parameter_value
                        except:
                            cprint(f'[INFO]\tWarning: Parameter "{supplier_param}" not found in supplier data', silent=settings.SILENT)
                    else:
                        inventree_part['parameters'][inventree_param] = part_info['manufacturer_part_number']

            # Check for missing parameters and fill value with dash
            for inventree_param in parameter_map.values():
                if inventree_param not in inventree_part['parameters'].keys():
                    inventree_part['parameters'][inventree_param] = '-'
        else:
            cprint(f'[INFO]\tWarning: Parameter map for "{categories[0]}" does not exist or is empty', silent=settings.SILENT)

    return inventree_part


def translate_supplier_to_form(supplier: str, part_info: dict) -> dict:
    ''' Translate supplier data to user form format '''

    part_form = {}

    def get_value_from_user_key(user_key: str, default_key: str, default_value=None) -> str:
        ''' Get value mapped from user search key, else default search key '''
        user_search_key = None
        if supplier == 'Digi-Key':
            user_search_key = settings.CONFIG_DIGIKEY.get(user_key, None)
        elif supplier == 'Mouser':
            user_search_key = settings.CONFIG_MOUSER.get(user_key, None)
        elif supplier == 'LCSC':
            user_search_key = settings.CONFIG_LCSC.get(user_key, None)
        else:
            return default_value
        
        # If no user key, use default
        if not user_search_key:
            return part_info.get(default_key, default_value)

        # Get value for user key, return value from default key if not found
        return part_info.get(user_search_key, part_info.get(default_key, default_value))

    def get_supplier_name(supplier: str) -> str:
        ''' Get InvenTree supplier name '''
        # Check that supplier is supported
        if supplier not in settings.SUPPORTED_SUPPLIERS_API:
            return ''

        if supplier == 'Digi-Key':
            supplier_name = settings.CONFIG_DIGIKEY.get('SUPPLIER_INVENTREE_NAME', None)
        elif supplier == 'Mouser':
            supplier_name = settings.CONFIG_MOUSER.get('SUPPLIER_INVENTREE_NAME', None)
        elif supplier == 'LCSC':
            supplier_name = settings.CONFIG_LCSC.get('SUPPLIER_INVENTREE_NAME', None)
        else:
            supplier_name = supplier
        
        return supplier_name

    # Check that supplier argument is valid
    if not supplier or (supplier != 'custom' and supplier not in settings.SUPPORTED_SUPPLIERS_API):
        return part_form
    # Get default keys
    if supplier == 'Digi-Key':
        default_search_keys = digikey_api.get_default_search_keys()
    elif supplier == 'Mouser':
        default_search_keys = mouser_api.get_default_search_keys()
    elif supplier == 'LCSC':
        default_search_keys = lcsc_api.get_default_search_keys()
    else:
        # Empty array of default search keys
        default_search_keys = [''] * len(digikey_api.get_default_search_keys())

    # Translate supplier data to form fields
    part_form['name'] = get_value_from_user_key('SEARCH_NAME', default_search_keys[0], default_value='')
    part_form['description'] = get_value_from_user_key('SEARCH_DESCRIPTION', default_search_keys[1], default_value='')
    part_form['revision'] = get_value_from_user_key('SEARCH_REVISION', default_search_keys[2], default_value=settings.INVENTREE_DEFAULT_REV)
    part_form['keywords'] = get_value_from_user_key('SEARCH_KEYWORDS', default_search_keys[1], default_value='')
    part_form['supplier_name'] = get_supplier_name(supplier)
    part_form['supplier_part_number'] = get_value_from_user_key('SEARCH_SKU', default_search_keys[4], default_value='')
    part_form['supplier_link'] = get_value_from_user_key('SEARCH_SUPPLIER_URL', default_search_keys[7], default_value='')
    part_form['manufacturer_name'] = get_value_from_user_key('SEARCH_MANUFACTURER', default_search_keys[5], default_value='')
    part_form['manufacturer_part_number'] = get_value_from_user_key('SEARCH_MPN', default_search_keys[6], default_value='')
    part_form['datasheet'] = get_value_from_user_key('SEARCH_DATASHEET', default_search_keys[8], default_value='')
    part_form['image'] = get_value_from_user_key('', default_search_keys[9], default_value='')
    
    return part_form


def supplier_search(supplier: str, part_number: str, test_mode=False) -> dict:
    ''' Wrapper for supplier search, allow use of cached data (limited daily API calls) '''
    part_info = {}
    # Check part number exist
    if not part_number:
        cprint('\n[MAIN]\tError: Missing Part Number', silent=settings.SILENT)
        return part_info

    # Load from file if cache is enabled
    search_filename = settings.search_results['directory'] + supplier + '_' + part_number + settings.search_results['extension']

    # Get cached data
    part_info = search_api.load_from_file(search_filename, test_mode)
    if part_info:
        cprint(f'\n[MAIN]\tUsing {supplier} cached data for {part_number}', silent=settings.SILENT)
    else:
        cprint(f'\n[MAIN]\t{supplier} search for {part_number}', silent=settings.SILENT)
        if supplier == 'Digi-Key':
            part_info = digikey_api.fetch_part_info(part_number)
        elif supplier == 'Mouser':
            part_info = mouser_api.fetch_part_info(part_number)
        elif supplier == 'LCSC':
            part_info = lcsc_api.fetch_part_info(part_number)

    # Check supplier data exist
    if not part_info:
        cprint(f'[INFO]\tError: Failed to fetch data for "{part_number}"', silent=settings.SILENT)

    # Save search results
    if part_info:
        search_api.save_to_file(part_info, search_filename)

    return part_info


def inventree_create(part_info: dict, categories: list, kicad=False, symbol=None, footprint=None, show_progress=True, is_custom=False):
    ''' Create InvenTree part from supplier part data and categories '''

    part_pk = 0
    new_part = False

    # Translate to InvenTree part format
    inventree_part = translate_form_to_inventree(part_info=part_info,
                                                 categories=categories,
                                                 is_custom=is_custom)

    if not inventree_part:
        cprint('\n[MAIN]\tError: Failed to process form data', silent=settings.SILENT)

    # Fetch category info from InvenTree part
    category_name = inventree_part['category'][0]
    subcategory_name = inventree_part['category'][1]
    category_pk = inventree_api.get_inventree_category_id(category_name)
    category_select = category_pk

    # Check if subcategory exists
    if subcategory_name:
        # Fetch subcategory id
        subcategory_pk = inventree_api.get_inventree_category_id(category_name=subcategory_name,
                                                                 parent_category_id=category_pk)
        if subcategory_pk > 0:
            category_select = subcategory_pk
        else:
            cprint(f'\n[TREE]\tWarning: Subcategory "{subcategory_name}" does not exist', silent=settings.SILENT)

    # Progress Update
    if show_progress and not progress.update_progress_bar_window():
        return new_part, part_pk, inventree_part

    if category_select <= 0:
        cprint(f'[ERROR]\tCategories ({category_name} - {subcategory_name}) does not exist in InvenTree', silent=settings.SILENT)
    else:
        # Check if part already exists
        part_pk = inventree_api.is_new_part(category_select, inventree_part)
        # Part exists
        if part_pk > 0:
            cprint('[INFO]\tPart already exists, skipping.', silent=settings.SILENT)
            ipn = inventree_api.get_part_number(part_pk)
            # Update InvenTree part number
            inventree_part['IPN'] = ipn
            # Update InvenTree URL
            inventree_part['inventree_url'] = f'{settings.PART_URL_ROOT}{inventree_part["IPN"]}/'
        # Part is new
        else:
            new_part = True
            # Create a new Part
            # Use the pk (primary-key) of the category
            part_pk = inventree_api.create_part(category_id=category_select,
                                                name=inventree_part['name'],
                                                description=inventree_part['description'],
                                                revision=inventree_part['revision'],
                                                image=inventree_part['image'],
                                                keywords=inventree_part['keywords'])

            # Check part primary key
            if not part_pk:
                return new_part, part_pk, inventree_part
            # Progress Update
            if show_progress and not progress.update_progress_bar_window():
                return new_part, part_pk, inventree_part

            # Generate Internal Part Number
            cprint('\n[MAIN]\tGenerating Internal Part Number', silent=settings.SILENT)
            ipn = part_tools.generate_part_number(category_name, part_pk)
            cprint(f'[INFO]\tInternal Part Number = {ipn}', silent=settings.SILENT)
            # Update InvenTree part number
            ipn_update = inventree_api.set_part_number(part_pk, ipn)
            if not ipn_update:
                cprint('\n[INFO]\tError updating IPN', silent=settings.SILENT)
            inventree_part['IPN'] = ipn
            # Update InvenTree URL
            inventree_part['inventree_url'] = f'{settings.PART_URL_ROOT}{inventree_part["IPN"]}/'

    # Progress Update
    if show_progress and not progress.update_progress_bar_window():
        return new_part, part_pk, inventree_part

    if part_pk > 0:
        if new_part:
            cprint('[INFO]\tSuccess: Added new part to InvenTree', silent=settings.SILENT)
            if inventree_part['image']:
                # Add image
                image_result = inventree_api.upload_part_image(inventree_part['image'], part_pk)
                if not image_result:
                    cprint('[TREE]\tWarning: Failed to upload part image', silent=settings.SILENT)

        if kicad:
            # Create mandatory parameters (symbol & footprint)
            if symbol and ipn:
                kicad_symbol = symbol + ':' + ipn
            else:
                try:
                    kicad_symbol = settings.symbol_libraries_paths[category_name].split(os.sep)[-1].split('.')[0] + ':' + ipn
                except:
                    kicad_symbol = category_name.replace(' ', '_') + ':TBD'
            if footprint:
                kicad_footprint = footprint
            else:
                try:
                    supplier_package = inventree_part['parameters']['Package Type']
                    kicad_footprint = settings.footprint_lookup_table[category_name][supplier_package]
                except:
                    kicad_footprint = category_name.replace(' ', '_') + ':TBD'

            # Add symbol & footprint to InvenTree part
            inventree_part['parameters']['Symbol'] = kicad_symbol
            inventree_part['parameters']['Footprint'] = kicad_footprint

        if not inventree_part['parameters']:
            category_parameters = inventree_api.get_category_parameters(category_select)

            # Add category-defined parameters
            for parameter in category_parameters:
                inventree_part['parameters'][parameter[0]] = parameter[1]

        # Create parameters
        if len(inventree_part['parameters']) > 0:
            cprint('\n[MAIN]\tCreating parameters', silent=settings.SILENT)
            parameters_lists = [
                [],  # Store new parameters
                [],  # Store existings parameters
            ]
            for name, value in inventree_part['parameters'].items():
                parameter, is_new_parameter = inventree_api.create_parameter(part_id=part_pk, template_name=name, value=value)
                # Progress Update
                if show_progress and not progress.update_progress_bar_window(3):
                    return new_part, part_pk, inventree_part

                if is_new_parameter:
                    parameters_lists[0].append(name)
                else:
                    parameters_lists[1].append(name)

            if parameters_lists[0]:
                cprint('[INFO]\tSuccess: The following parameters were created:', silent=settings.SILENT)
                for item in parameters_lists[0]:
                    cprint(f'--->\t{item}', silent=settings.SILENT)
            if parameters_lists[1]:
                cprint('[TREE]\tWarning: The following parameters were skipped:', silent=settings.SILENT)
                for item in parameters_lists[1]:
                    cprint(f'--->\t{item}', silent=settings.SILENT)

        # Create manufacturer part(s)
        # TODO: Support multiple MPNs?
        for manufacturer_name, manufacturer_mpns in inventree_part['manufacturer'].items():
            # Get MPN
            manufacturer_mpn = manufacturer_mpns[0]

            if manufacturer_mpn:
                cprint('\n[MAIN]\tCreating manufacturer part', silent=settings.SILENT)
                is_new_manufacturer_part = inventree_api.is_new_manufacturer_part(manufacturer_name=manufacturer_name,
                                                                                  manufacturer_mpn=manufacturer_mpn)

                if not is_new_manufacturer_part:
                    cprint('[INFO]\tManufacturer part already exists, skipping.', silent=settings.SILENT)
                else:
                    # Create a new manufacturer part
                    is_manufacturer_part_created = inventree_api.create_manufacturer_part(part_id=part_pk,
                                                                                          manufacturer_name=manufacturer_name,
                                                                                          manufacturer_mpn=manufacturer_mpn,
                                                                                          datasheet=inventree_part['datasheet'],
                                                                                          description=inventree_part['description'])

                    if is_manufacturer_part_created:
                        cprint('[INFO]\tSuccess: Added new manufacturer part', silent=settings.SILENT)

        # Create supplier part(s)
        # TODO: Support multiple SKUs?
        for supplier_name, supplier_skus in inventree_part['supplier'].items():
            # Get SKU
            supplier_sku = supplier_skus[0]

            if supplier_sku:
                cprint('\n[MAIN]\tCreating supplier part', silent=settings.SILENT)
                is_new_supplier_part = inventree_api.is_new_supplier_part(supplier_name=supplier_name,
                                                                          supplier_sku=supplier_sku)

                if not is_new_supplier_part:
                    cprint('[INFO]\tSupplier part already exists, skipping.', silent=settings.SILENT)
                else:
                    # Create a new supplier part
                    is_supplier_part_created = inventree_api.create_supplier_part(part_id=part_pk,
                                                                                  manufacturer_name=manufacturer_name,
                                                                                  manufacturer_mpn=manufacturer_mpn,
                                                                                  supplier_name=supplier_name,
                                                                                  supplier_sku=inventree_part['supplier'][supplier_name],
                                                                                  description=inventree_part['description'],
                                                                                  link=inventree_part['supplier_link'])

                    if is_supplier_part_created:
                        cprint('[INFO]\tSuccess: Added new supplier part', silent=settings.SILENT)

    # Progress Update
    if show_progress and not progress.update_progress_bar_window(3):
        pass

    return new_part, part_pk, inventree_part
