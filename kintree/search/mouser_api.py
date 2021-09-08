import os

from ..config import settings, config_interface
from mouser.api import MouserPartSearchRequest

SEARCH_HEADERS = [
    'Description',
    'productCode',
    'MouserPartNumber',
    'Manufacturer',
    'ManufacturerPartNumber',
    'DataSheetUrl',
    'ProductDetailUrl',
    'ImagePath',
]
PARAMETERS_MAP = [
    'ProductAttributes',
    'AttributeName',
    'AttributeValue',
]


def get_default_search_keys():
    return [
        'Description',
        'Description',
        'revision',
        'keywords',
        'MouserPartNumber',
        'Manufacturer',
        'ManufacturerPartNumber',
        'ProductDetailUrl',
        'DataSheetUrl',
        'ImagePath',
    ]


def setup_environment(force=False):
    ''' Setup environmental variables '''

    api_key = os.environ.get('MOUSER_PART_API_KEY', None)
    if not api_key or force:
        mouser_api_settings = config_interface.load_file(settings.CONFIG_MOUSER_API)
        os.environ['MOUSER_PART_API_KEY'] = mouser_api_settings['MOUSER_PART_API_KEY']


def find_categories(part_details: str):
    ''' Find categories '''

    try:
        return part_details['Category'], None
    except:
        return None, None


def fetch_part_info(part_number: str) -> dict:
    ''' Fetch part data from API '''

    from ..wrapt_timeout_decorator import timeout

    setup_environment()
    part_info = {}

    @timeout(dec_timeout=20)
    def search_timeout():
        request = MouserPartSearchRequest('partnumber')
        request.part_search(part_number)
        return request.get_clean_response()

    # Query part number
    try:
        part = search_timeout()
    except:
        part = None

    if not part:
        return part_info

    # Check for empty response
    empty = True
    for key, value in part.items():
        if value:
            empty = False
            break
    if empty:
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


def test_api() -> bool:
    ''' Test method for API '''

    test_success = True
    expected = {
        'Description': 'MOSFET P-channel 1.25W',
        'MouserPartNumber': '621-DMP2066LSN-7',
        'Manufacturer': 'Diodes Incorporated',
        'ManufacturerPartNumber': 'DMP2066LSN-7',
    }

    test_part = fetch_part_info('DMP2066LSN-7')
        
    if not test_part:
        # Unsucessful search
        test_success = False
    else:
        # Check content of response
        for key, value in expected.items():
            if test_part[key] != value:
                print(f'"{test_part[key]}" <> "{value}"')
                test_success = False
                break

    return test_success
