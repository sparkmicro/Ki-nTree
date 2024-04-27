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

PRICING_MAP = [
    'PriceBreaks',
    'Quantity',
    'Price',
    'Currency',
]


def get_default_search_keys():
    return [
        'ManufacturerPartNumber',
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
        try:
            os.environ['MOUSER_PART_API_KEY'] = mouser_api_settings['MOUSER_PART_API_KEY']
        except TypeError:
            pass


def find_categories(part_details: str):
    ''' Find categories '''

    try:
        return part_details['Category'], None
    except:
        return None, None


def fetch_part_info(part_number: str) -> dict:
    ''' Fetch part data from API '''

    from wrapt_timeout_decorator import timeout

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

    # Pricing
    part_info['pricing'] = {}
    [pricing_key, qty_key, price_key, currency_key] = PRICING_MAP

    for price_break in part[pricing_key]:
        quantity = price_break[qty_key]
        price = price_break[price_key]
        part_info['pricing'][quantity] = price

    if part[pricing_key]:
        part_info['currency'] = part[pricing_key][0][currency_key]
    else:
        part_info['currency'] = 'USD'

    # Extra search fields
    if settings.CONFIG_MOUSER.get('EXTRA_FIELDS', None):
        for extra_field in settings.CONFIG_MOUSER['EXTRA_FIELDS']:
            if part.get(extra_field, None):
                part_info['parameters'][extra_field] = part[extra_field]
            else:
                from ..common.tools import cprint
                cprint(f'[INFO]\tWarning: Extra field "{extra_field}" not found in search results', silent=False)

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
