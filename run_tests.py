import os
import sys

import kintree.config.settings as settings
from kintree.common.tools import cprint, create_library, download_image
from kintree.config import config_interface
from kintree.database import inventree_api, inventree_interface
from kintree.kicad import kicad_interface
from kintree.search import digikey_api, mouser_api, element14_api, lcsc_api
from kintree.search.snapeda_api import test_snapeda_api
from kintree.setup_inventree import setup_inventree

# SETTINGS
# Enable InvenTree tests
ENABLE_INVENTREE = True
# Enable KiCad tests
ENABLE_KICAD = True
# Enable test samples deletion
ENABLE_DELETE = True
AUTO_DELETE = True
# Set categories to test
PART_CATEGORIES = [
    # 'Capacitors',
    # 'Circuit Protections',
    # 'Connectors',
    # 'Crystals and Oscillators',
    # 'Diodes',
    # 'Inductors',
    'Integrated Circuits',
    # 'Mechanicals',
    # 'Power Management',
    # 'Resistors',
    # 'RF',
    # 'Transistors',
]
# Enable tests on extra methods
ENABLE_TEST_METHODS = True
###


# Pretty test printing
def pretty_test_print(message: str):
    cprint(message.ljust(65), end='')


# Check result
def check_result(status: str, new_part: bool) -> bool:
    # Build result
    success = False
    if (status == 'original') or (status == 'fake_alternate'):
        if new_part:
            success = True
    elif status == 'alternate_mpn':
        if not new_part:
            success = True
    else:
        pass

    return success


# --- SETUP ---

# Enable test mode
settings.enable_test_mode()
# Enable InvenTree and KiCad
settings.set_enable_flag('inventree', True)
settings.set_enable_flag('alternate', False)
settings.set_enable_flag('kicad', True)
# Load user configuration files
settings.load_user_config()
# Set path to test libraries
test_library_path = os.path.join(settings.PROJECT_DIR, 'tests', 'TEST.kicad_sym')
symbol_libraries_test_path = os.path.join(settings.PROJECT_DIR, 'tests', 'files', 'SYMBOLS')
footprint_libraries_test_path = os.path.join(settings.PROJECT_DIR, 'tests', 'files', 'FOOTPRINTS', '')
# Disable Digi-Key API logging
digikey_api.disable_api_logger()

# # Test Digi-Key API
# if 'Digi-Key' in settings.SUPPORTED_SUPPLIERS_API:
#     pretty_test_print('[MAIN]\tDigi-Key API Test')
#     if not digikey_api.test_api(check_content=True):
#         cprint('[ FAIL ]')
#         cprint('[INFO]\tFailed to get Digi-Key API token, aborting.')
#         sys.exit(-1)
#     else:
#         cprint('[ PASS ]')

# # Test Mouser API
# if 'Mouser' in settings.SUPPORTED_SUPPLIERS_API:
#     pretty_test_print('[MAIN]\tMouser API Test')
#     if not mouser_api.test_api():
#         cprint('[ FAIL ]')
#         sys.exit(-1)
#     else:
#         cprint('[ PASS ]')

# # Test Element14 API
# if 'Element14' in settings.SUPPORTED_SUPPLIERS_API:
#     pretty_test_print('[MAIN]\tElement14 API Test')
#     if not element14_api.test_api() or not element14_api.test_api(store_url='www.newark.com'):
#         cprint('[ FAIL ]')
#         sys.exit(-1)
#     else:
#         cprint('[ PASS ]')

# # Test LCSC API
# if 'LCSC' in settings.SUPPORTED_SUPPLIERS_API:
#     pretty_test_print('[MAIN]\tLCSC API Test')
#     if not lcsc_api.test_api():
#         cprint('[ FAIL ]')
#         sys.exit(-1)
#     else:
#         cprint('[ PASS ]')

# Setup InvenTree
cprint('\n-----')
setup_inventree()
cprint('\n-----')

# Load test samples
samples = config_interface.load_file(os.path.abspath(
    os.path.join('tests', 'test_samples.yaml')))
PART_TEST_SAMPLES = {}
for category in PART_CATEGORIES:
    PART_TEST_SAMPLES.update({category: samples[category]})

# Store results
exit_code = 0
kicad_results = {}
inventree_results = {}

# --- TESTS ---
if __name__ == '__main__':
    if settings.ENABLE_TEST:
        if ENABLE_INVENTREE:
            pretty_test_print('\n[MAIN]\tConnecting to Inventree')
            inventree_connect = inventree_interface.connect_to_server()
            if inventree_connect:
                cprint('[ PASS ]')
            else:
                cprint('[ FAIL ]')
                sys.exit(-1)

        if ENABLE_KICAD or ENABLE_INVENTREE:
            for category in PART_TEST_SAMPLES.keys():
                cprint(f'\n[MAIN]\tCategory: {category.upper()}')

                # For last category, combine creation of KiCad and InvenTree parts
                last_category = False
                if ENABLE_KICAD and ENABLE_INVENTREE and category == list(PART_TEST_SAMPLES.keys())[-1]:
                    last_category = True

                for number, status in PART_TEST_SAMPLES[category].items():
                    kicad_result = False
                    inventree_result = False
                    # Fetch supplier data
                    supplier_info = inventree_interface.supplier_search(supplier='Digi-Key', part_number=number, test_mode=True)
                    # Translate to form
                    part_info = inventree_interface.translate_supplier_to_form(supplier='Digi-Key', part_info=supplier_info)
                    # Stitch categories and parameters
                    part_info.update({
                        'category_tree': [supplier_info['category'], supplier_info['subcategory']],
                        'parameters': supplier_info['parameters'],
                        'Symbol': f'{category}:{number}',
                    })
                    # Update categories
                    part_info['category_tree'] = inventree_interface.get_categories_from_supplier_data(part_info)
                    print(part_info['category_tree'])
                    # Display part to be tested
                    pretty_test_print(f'[INFO]\tChecking "{number}" ({status})')

                    if ENABLE_INVENTREE:
                        # Adding part information to InvenTree
                        categories = [None, None]
                        new_part = False
                        part_pk = 0
                        part_data = {}

                        # Create part in InvenTree
                        new_part, part_pk, part_data = inventree_interface.inventree_create(
                            part_info=part_info,
                            kicad=last_category,
                            symbol=part_info['Symbol'],
                            show_progress=False,
                        )

                        inventree_result = check_result(status, new_part)
                        pk_list = [data[0] for data in inventree_results.values()]

                        if part_pk != 0 and part_pk not in pk_list:
                            delete = True
                        else:
                            delete = False

                        # Log results
                        inventree_results.update({number: [part_pk, inventree_result, delete]})

                    if ENABLE_KICAD:
                        if settings.AUTO_GENERATE_LIB:
                            create_library(
                                os.path.dirname(test_library_path),
                                'TEST',
                                settings.symbol_template_lib,
                            )

                        kicad_result, kicad_new_part = kicad_interface.inventree_to_kicad(
                            part_data=part_info,
                            library_path=test_library_path,
                            show_progress=False,
                        )

                        # Log result
                        if number not in kicad_results.keys():
                            kicad_results.update({number: kicad_result})

                    # Combine KiCad and InvenTree for less verbose
                    result = False
                    if ENABLE_KICAD and ENABLE_INVENTREE:
                        result = kicad_result and inventree_result
                    else:
                        result = kicad_result or inventree_result

                    # Print live results
                    if result:
                        cprint('[ PASS ]')
                    else:
                        cprint('[ FAIL ]')
                        exit_code = -1
                        if ENABLE_KICAD:
                            cprint(f'[DBUG]\tkicad_result = {kicad_result}')
                            cprint(f'[DBUG]\tkicad_new_part = {kicad_new_part}')
                        if ENABLE_INVENTREE:
                            cprint(f'[DBUG]\tinventree_result = {inventree_result}')
                            cprint(f'[DBUG]\tnew_part = {new_part}')
                            cprint(f'[DBUG]\tpart_pk = {part_pk}')

            # if True:
            # 	if ENABLE_KICAD:
            # 		cprint(f'\nKiCad Results\n-----', silent=not(settings.ENABLE_TEST))
            # 		cprint(kicad_results, silent=not(settings.ENABLE_TEST))
            # 	if ENABLE_INVENTREE:
            # 		cprint(f'\nInvenTree Results\n-----', silent=not(settings.ENABLE_TEST))
            # 		cprint(inventree_results, silent=not(settings.ENABLE_TEST))

        if ENABLE_TEST_METHODS:
            methods = [
                'Fuzzy category matching',
                'Custom parts form',
                'Digi-Key search missing part number',
                'Load KiCad library paths',
                'Add symbol library to user file',
                'Add footprint library to user file',
                'Add supplier category',
                'Sync InvenTree and supplier categories',
                'SnapEDA API methods',
                'Download image method',
                'Get category parameters',
                'Add valid alternate supplier part using part ID',
                'Add invalid alternate supplier part using part IPN',
                'Save InvenTree settings',
                'Load configuration files with incorrect paths',
            ]
            method_success = True
            # Line return
            cprint('')
            cprint('[MAIN]\tChecking untested methods'.ljust(65))

            for method_idx, method_name in enumerate(methods):
                pretty_test_print(method_name)

                if method_idx == 0:
                    # Fuzzy category matching
                    part_info = {
                        'category_tree': ['Capacitors', 'Super',],
                    }
                    categories = tuple(inventree_interface.get_categories_from_supplier_data(part_info))
                    if not (categories[0] and categories[1]):
                        method_success = False

                elif method_idx == 1:
                    # Custom part form
                    try:
                        inventree_interface.translate_form_to_inventree(part_info, categories)
                        # If the above function does not fail, it's a problem
                        method_success = False
                    except KeyError:
                        pass
                    
                    part_info = {
                        'name': 'part_name',
                        'description': 'part_desc',
                        'revision': 'part_rev',
                        'keywords': 'part_key',
                        'supplier_name': 'part_supplier',
                        'supplier_part_number': 'part_sku',
                        'supplier_link': 'part_link',
                        'manufacturer_name': 'part_man',
                        'manufacturer_part_number': 'part_mpn',
                        'datasheet': 'part_data',
                        'image': 'part_image',
                    }
                    if not inventree_interface.translate_form_to_inventree(part_info, categories, is_custom=True):
                        method_success = False

                elif method_idx == 2:
                    # Digi-Key search missing part number
                    search = inventree_interface.supplier_search(supplier='Digi-Key', part_number='')
                    if search:
                        method_success = False

                elif method_idx == 3:
                    # Load KiCad library paths
                    config_interface.load_library_path(settings.KICAD_CONFIG_PATHS, silent=True)
                    symbol_libraries_paths = config_interface.load_libraries_paths(settings.KICAD_CONFIG_CATEGORY_MAP, symbol_libraries_test_path)
                    footprint_libraries_paths = config_interface.load_footprint_paths(settings.KICAD_CONFIG_CATEGORY_MAP, footprint_libraries_test_path)
                    if not (symbol_libraries_paths and footprint_libraries_paths):
                        method_success = False

                elif method_idx == 4:
                    # Add symbol library to user file
                    add_symbol_lib = config_interface.add_library_path(user_config_path=settings.KICAD_CONFIG_CATEGORY_MAP,
                                                                       category='category_test',
                                                                       symbol_library='symbol_library_test')
                    if not add_symbol_lib:
                        method_success = False

                elif method_idx == 5:
                    # Add footprint library to user file
                    add_footprint_lib = config_interface.add_footprint_library(user_config_path=settings.KICAD_CONFIG_CATEGORY_MAP,
                                                                               category='category_test',
                                                                               library_folder='footprint_folder_test')
                    if not add_footprint_lib:
                        method_success = False

                elif method_idx == 6:
                    # Add supplier category
                    categories = {
                        'Capacitors':
                        {'Super': 'Super'}
                    }
                    add_category = config_interface.add_supplier_category(categories, settings.CONFIG_DIGIKEY_CATEGORIES)
                    if not add_category:
                        method_success = False

                elif method_idx == 7:
                    # Sync InvenTree and Supplier categories
                    sync_categories = config_interface.sync_inventree_supplier_categories(inventree_config_path=settings.CONFIG_CATEGORIES,
                                                                                          supplier_config_path=settings.CONFIG_DIGIKEY_CATEGORIES)
                    if not sync_categories:
                        method_success = False

                elif method_idx == 8:
                    # Test SnapEDA API methods
                    snapeda_success = test_snapeda_api()
                    if not snapeda_success:
                        method_success = False

                elif method_idx == 9:
                    test_image_urllib = 'https://media.digikey.com/Renders/Diodes%20Renders/31;%20SOD-123;%20;%202.jpg'
                    test_image_requestslib = 'https://www.newark.com/productimages/standard/en_GB/GE2SOD12307-40.jpg'
                    # Test download image
                    if not download_image(test_image_urllib, './image1.jpg', silent=True):
                        method_success = False
                    if not download_image(test_image_requestslib, './image2.jpg', silent=True):
                        method_success = False
                    if download_image('http', '', silent=True):
                        method_success = False
                    if download_image('', '', silent=True):
                        method_success = False

                elif method_idx == 10:
                    # Test InvenTree category parameters
                    if inventree_api.get_category_parameters(1):
                        method_success = False

                elif method_idx == 11:
                    # Test manufacturer and supplier alternates using Part ID
                    part_info = {
                        "datasheet": "https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM155R71C104KA88-01.pdf",
                        "manufacturer_name": "Murata Electronics",
                        "manufacturer_part_number": "GRM155R71C104KA88D",
                        "supplier_link": "https://www.digikey.com/en/products/detail/murata-electronics/GRM155R71C104KA88D/675947",
                        "supplier_name": "Digi-Key",
                        "supplier_part_number": "490-3261-1-ND"
                    }
                    if not inventree_interface.inventree_create_alternate(part_info=part_info,
                                                                          part_id='1',
                                                                          show_progress=False, ):
                        method_success = False

                elif method_idx == 12:
                    # Test manufacturer and supplier alternates using Part IPN
                    if inventree_interface.inventree_create_alternate(part_info=part_info,
                                                                      part_ipn='CAP-000001-00',
                                                                      show_progress=False, ):
                        method_success = False

                elif method_idx == 13:
                    # Save InvenTree settings
                    if not config_interface.save_inventree_user_settings(enable=True,
                                                                         server='http://127.0.0.1:8000',
                                                                         username='admin',
                                                                         password='admin',
                                                                         user_config_path=settings.INVENTREE_CONFIG):
                        method_success = False

                elif method_idx == 14:
                    # Load configuration files with incorrect paths
                    if config_interface.load_user_config_files('', ''):
                        method_success = False

                if method_success:
                    cprint('[ PASS ]')
                else:
                    cprint('[ FAIL ]')
                    exit_code = -1
                    break
        
        if ENABLE_DELETE:
            if kicad_results or inventree_results:
                if not AUTO_DELETE:
                    input('\nPress "Enter" to delete parts...')
                else:
                    cprint('')

                # NOT YET SUPPORTED - REMOVE?
                # if ENABLE_KICAD:
                #     error = 0

                #     pretty_test_print('[MAIN]\tDeleting KiCad test parts')
                #     # Delete all KiCad test parts
                #     for number, result in kicad_results.items():
                #         try:
                #             kicad_interface.delete_part(part_number=number,
                #                                         library_path=test_library_path)
                #         except:
                #             error += 1
                #             cprint(f'[KCAD]\tWarning: "{number}" could not be deleted')

                #     if error > 0:
                #         cprint('[ FAIL ]')
                #         exit_code = -1
                #     else:
                #         cprint('[ PASS ]')

                if ENABLE_INVENTREE:
                    error = 0

                    pretty_test_print('[MAIN]\tDeleting InvenTree test parts')
                    # Delete all InvenTree test parts
                    for number, result in inventree_results.items():
                        if result[2]:
                            try:
                                if not inventree_api.delete_part(part_id=result[0]):
                                    error += 1
                            except:
                                error += 1

                    if error > 0:
                        cprint('[ FAIL ]')
                        exit_code = -1
                    else:
                        cprint('[ PASS ]')

            # Line return
            cprint('')

    sys.exit(exit_code)
