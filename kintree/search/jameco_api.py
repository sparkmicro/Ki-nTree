import re
from ..common.tools import download

SEARCH_HEADERS = [
    'name',
    'prod_id',
    'brandNameEn',
    'productModel',
    'pdfUrl',
    'imageUrl',
    'price',
    'manufacturer_part_number',
    'url',
    'ss_attr_manufacturer',

]
PARAMETERS_MAP = [
    'product_type_unigram', #e.g. to92
]


def get_default_search_keys():
    return [
        'name',
        'prod_id',
        'brandNameEn',
        'productModel',
        'pdfUrl',
        'imageUrl',
        'price',
        'manufacturer_part_number',
        'url',
        'ss_attr_manufacturer',
    ]


def find_categories(part_details: str):
    ''' Find categories '''
    try:
        return part_details['parentCatalogName'], part_details['catalogName']
    except:
        return None, None


def fetch_part_info(part_number: str) -> dict:
    ''' Fetch part data from API '''

    # Load Jameco settings
    from ..config import settings, config_interface
    jameco_api_settings = config_interface.load_file(settings.CONFIG_JAMECO_API)

    part_info = {}

    def search_timeout(timeout=10):
        url = jameco_api_settings.get('JAMECO_API_URL', '') + part_number
        response = download(url, timeout=timeout)
        return response

    # Query part number
    try:
        part = search_timeout()
    except:
        part = None

    # Extract results, select first in returned search List
    part = part.get('results', None)
    part = part[0]

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
            if key == 'imageUrl':
                try:
                    part_info[key] = part['imageUrl'][0]
                except IndexError:
                    pass
            else:
                part_info[key] = part[key]

    # Parameters
    part_info['parameters'] = {}
    [parameter_key] = PARAMETERS_MAP

    if part.get(parameter_key, ''):
        for parameter in range(len(part[parameter_key])):
            parameter_name = parameter_key
            parameter_value = str(part[parameter_key]).upper()
            # Append to parameters dictionary
            part_info['parameters'][parameter_name] = parameter_value

    # Pricing
    part_info['pricing'] = {}

    # Jameco returns price breaks as a string of HTML text
    # Convert pricing string pattern to List, then  dictionary for Ki-nTree
    price_break_str = part['secondary_prices']
    price_break_str = re.sub('(\&lt;br\s\/&*gt)','', price_break_str)
    price_break_str = re.sub(';', ':', price_break_str)
    price_break_str = re.sub('(\:\s+\$)|\;', ':', price_break_str)
    price_break_list = price_break_str.split(':')
    price_break_list.pop() # remove last empty element in List

    for i in range(0, len(price_break_list), 2):
        quantity = price_break_list[i]
        price = price_break_list[i+1]
        part_info['pricing'][quantity] = price

    part_info['currency'] = 'USD'

    # Extra search fields
    if settings.CONFIG_JAMECO.get('EXTRA_FIELDS', None):
        for extra_field in settings.CONFIG_JAMECO['EXTRA_FIELDS']:
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
        'manufacturer_part_number':'PN2222ABU',
        'name': 'Transistor PN2222A NPN Silicon General Purpose TO-92',
        'prod_id': '178511',
    }

    test_part = fetch_part_info('178511')
    if not test_part:
        test_success = False
        
    # Check content of response
    if test_success:
        for key, value in expected.items():
            if test_part[key] != value:
                print(f'"{test_part[key]}" <> "{value}"')
                test_success = False
                break

    return test_success
