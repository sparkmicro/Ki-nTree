import logging
import os
import digikey

from ..config import settings, config_interface

SEARCH_HEADERS = [
    'product_description',
    'detailed_description',
    'digi_key_part_number',
    'manufacturer',
    'manufacturer_part_number',
    'product_url',
    'primary_datasheet',
    'primary_photo',
]
PARAMETERS_MAP = [
    'parameters',
    'parameter',
    'value',
]


os.environ['DIGIKEY_STORAGE_PATH'] = settings.DIGIKEY_STORAGE_PATH
# Check if storage path exists, else create it
if not os.path.exists(os.environ['DIGIKEY_STORAGE_PATH']):
    os.makedirs(os.environ['DIGIKEY_STORAGE_PATH'], exist_ok=True)


def disable_api_logger():
    # Digi-Key API logger
    logging.getLogger('digikey.v3.api').setLevel(logging.CRITICAL)
    # Disable DEBUG
    logging.disable(logging.DEBUG)


def check_environment() -> bool:
    DIGIKEY_CLIENT_ID = os.environ.get('DIGIKEY_CLIENT_ID', None)
    DIGIKEY_CLIENT_SECRET = os.environ.get('DIGIKEY_CLIENT_SECRET', None)

    if not DIGIKEY_CLIENT_ID or not DIGIKEY_CLIENT_SECRET:
        return False

    return True


def setup_environment(force=False) -> bool:
    if not check_environment() or force:
        # SETUP the Digikey authentication see https://developer.digikey.com/documentation/organization#production
        digikey_api_settings = config_interface.load_file(settings.CONFIG_DIGIKEY_API)
        os.environ['DIGIKEY_CLIENT_ID'] = digikey_api_settings['DIGIKEY_CLIENT_ID']
        os.environ['DIGIKEY_CLIENT_SECRET'] = digikey_api_settings['DIGIKEY_CLIENT_SECRET']

    return check_environment()


def get_default_search_keys():
    return [
        'product_description',
        'product_description',
        'revision',
        'keywords',
        'digi_key_part_number',
        'manufacturer',
        'manufacturer_part_number',
        'product_url',
        'primary_datasheet',
        'primary_photo',
    ]


def find_categories(part_details: str):
    ''' Find categories '''
    try:
        return part_details['limited_taxonomy'].get('value'), part_details['limited_taxonomy']['children'][0].get('value')
    except:
        return None, None


def fetch_part_info(part_number: str) -> dict:
    ''' Fetch part data from API '''
    from ..wrapt_timeout_decorator import timeout

    part_info = {}
    if not setup_environment():
        return part_info

    @timeout(dec_timeout=20)
    def digikey_search_timeout():
        return digikey.product_details(part_number).to_dict()

    # Query part number
    try:
        part = digikey_search_timeout()
    except:
        part = None

    if not part:
        return part_info

    category, subcategory = find_categories(part)
    try:
        part_info['category'] = category
        part_info['subcategory'] = subcategory
    except:
        part_info['category'] = ''
        part_info['subcategory'] = ''

    headers = SEARCH_HEADERS

    for key in part:
        if key in headers:
            if key == 'manufacturer':
                part_info[key] = part['manufacturer']['value']
            else:
                part_info[key] = part[key]

    # Parameters
    part_info['parameters'] = {}
    [parameter_key, name_key, value_key] = PARAMETERS_MAP

    for parameter in range(len(part[parameter_key])):
        parameter_name = part[parameter_key][parameter][name_key]
        parameter_value = part[parameter_key][parameter][value_key]
        # Append to parameters dictionary
        part_info['parameters'][parameter_name] = parameter_value

    return part_info


def test_api_connect(check_content=False) -> bool:
    ''' Test method for API token '''
    setup_environment()

    test_success = True
    expected = {
        'product_description': 'RES 10K OHM 5% 1/16W 0402',
        'digi_key_part_number': 'RMCF0402JT10K0CT-ND',
        'manufacturer': 'Stackpole Electronics Inc',
        'manufacturer_part_number': 'RMCF0402JT10K0',
        'product_url': 'https://www.digikey.com/en/products/detail/stackpole-electronics-inc/RMCF0402JT10K0/1758206',
        'primary_datasheet': 'https://www.seielect.com/catalog/sei-rmcf_rmcp.pdf',
        'primary_photo': 'https://media.digikey.com/photos/Stackpole%20Photos/MFG_RMC%20SERIES.jpg',
    }

    test_part = fetch_part_info('RMCF0402JT10K0')

    # Check for response
    if not test_part:
        test_success = False
    
    if not check_content:
        return test_success
        
    # Check content of response
    if test_success:
        for key, value in expected.items():
            if test_part[key] != value:
                print(f'{test_part[key]} != {value}')
                test_success = False
                break

    return test_success
