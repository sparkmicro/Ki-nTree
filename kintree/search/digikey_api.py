import logging
import os
import time

from ..config import settings
import digikey
from ..config import config_interface

os.environ['DIGIKEY_STORAGE_PATH'] = settings.DIGIKEY_STORAGE_PATH
# Check if storage path exists, else create it
if not os.path.exists(os.environ['DIGIKEY_STORAGE_PATH']):
    os.makedirs(os.environ['DIGIKEY_STORAGE_PATH'], exist_ok=True)


def disable_digikey_api_logger():
    # Digi-Key API logger
    logging.getLogger('digikey.v3.api').setLevel(logging.WARNING)
    # Disable DEBUG
    logging.disable(logging.DEBUG)


def check_environment() -> bool:
    DIGIKEY_CLIENT_ID = os.environ.get('DIGIKEY_CLIENT_ID', None)
    DIGIKEY_CLIENT_SECRET = os.environ.get('DIGIKEY_CLIENT_SECRET', None)

    if not DIGIKEY_CLIENT_ID or not DIGIKEY_CLIENT_SECRET:
        return False

    return True


def setup_environment() -> bool:
    if not check_environment():
        # SETUP the Digikey authentication see https://developer.digikey.com/documentation/organization#production
        digikey_api_settings = config_interface.load_file(settings.CONFIG_DIGIKEY_API)
        os.environ['DIGIKEY_CLIENT_ID'] = digikey_api_settings['DIGIKEY_CLIENT_ID']
        os.environ['DIGIKEY_CLIENT_SECRET'] = digikey_api_settings['DIGIKEY_CLIENT_SECRET']

    return check_environment()


def find_categories(part_details: str):
    ''' Find Digi-Key categories '''
    try:
        # print(part_details['limited_taxonomy']['children'][0]['value'])
        return part_details['limited_taxonomy']['children'][0]['value'], part_details['limited_taxonomy']['children'][0]['children'][0]['value']
    except:
        return None, None


def fetch_digikey_part_info(part_number: str) -> dict:
    ''' Fetch Digi-Key part data from API '''
    from wrapt_timeout_decorator import timeout

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

    header = [
        'product_description',
        'detailed_description',
        'digi_key_part_number',
        'manufacturer',
        'manufacturer_part_number',
        'product_url',
        'primary_datasheet',
        'primary_photo',
    ]

    for key in part:
        if key in header:
            if key == 'manufacturer':
                part_info[key] = part['manufacturer']['value']
            else:
                part_info[key] = part[key]

    # Parameters
    part_info['parameters'] = {}
    for parameter in range(len(part['parameters'])):
        parameter_name = part['parameters'][parameter]['parameter']
        parameter_value = part['parameters'][parameter]['value']
        # Append to parameters dictionary
        part_info['parameters'][parameter_name] = parameter_value
    # print(part_info['parameters'])

    return part_info


def test_digikey_api_connect() -> bool:
    ''' Test method for Digi-Key API token '''
    setup_environment()

    test_part = fetch_digikey_part_info('RMCF0402JT10K0')
    if test_part:
        return True

    return False


def load_from_file(search_file, test_mode=False) -> dict:
    ''' Fetch Digi-Key part data from file '''
    cache_valid = settings.CACHE_VALID_DAYS * 24 * 3600

    # Load data from file if cache enabled
    if settings.CACHE_ENABLED:
        try:
            part_data = config_interface.load_file(search_file)
        except FileNotFoundError:
            return None

        # Check cache validity
        try:
            # Get timestamp
            timestamp = int(time.time() - part_data['search_timestamp'])
        except (KeyError, TypeError):
            timestamp = int(time.time())

        if timestamp < cache_valid or test_mode:
            return part_data

    return None


def save_to_file(part_info, search_file):
    ''' Save Digi-Key part data to file '''

    # Check if search/results directory needs to be created
    if not os.path.exists(os.path.dirname(search_file)):
        os.mkdir(os.path.dirname(search_file))

    # Add timestamp
    part_info['search_timestamp'] = int(time.time())

    # Save data if cache enabled
    if settings.CACHE_ENABLED:
        try:
            config_interface.dump_file(part_info, search_file)
        except:
            raise Exception('Error saving Digi-key search data')
