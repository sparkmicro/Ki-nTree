from ..common.tools import download

SEARCH_HEADERS = [
    'productDescEn',
    'productIntroEn',
    'productCode',
    'brandNameEn',
    'productModel',
    'pdfUrl',
    'productImages',
]
PARAMETERS_MAP = [
    'paramVOList',
    'paramNameEn',
    'paramValueEn',
]

PRICING_MAP = [
    'productPriceList',
    'ladder',
    'usdPrice',
]


def get_default_search_keys():
    return [
        'productIntroEn',
        'productIntroEn',
        'revision',
        'keywords',
        'productCode',
        'brandNameEn',
        'productModel',
        'part_url',
        'pdfUrl',
        'productImages',
    ]


def find_categories(part_details: str):
    ''' Find categories '''
    try:
        return part_details['parentCatalogName'], part_details['catalogName']
    except:
        return None, None


def fetch_part_info(part_number: str) -> dict:
    ''' Fetch part data from API '''

    # Load LCSC settings
    from ..config import settings, config_interface
    lcsc_api_settings = config_interface.load_file(settings.CONFIG_LCSC_API)

    part_info = {}

    def search_timeout(timeout=10):
        url = lcsc_api_settings.get('LCSC_API_URL', '') + part_number
        response = download(url, timeout=timeout)
        return response

    # Query part number
    try:
        part = search_timeout()
        # Extract result
        part = part.get('result', None)
    except:
        part = {}

    if not part:
        return part_info

    product_code = part.get('productCode')
    if product_code:
        part_info['part_url'] = f'https://www.lcsc.com/product-detail/{product_code}.html'

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
            if key == 'productImages':
                try:
                    part_info[key] = part['productImages'][0]
                except IndexError:
                    pass
            else:
                part_info[key] = part[key]

    # Parameters
    part_info['parameters'] = {}
    [parameter_key, name_key, value_key] = PARAMETERS_MAP

    if part.get(parameter_key, ''):
        for parameter in range(len(part[parameter_key])):
            parameter_name = part[parameter_key][parameter][name_key]
            parameter_value = part[parameter_key][parameter][value_key]
            # Append to parameters dictionary
            part_info['parameters'][parameter_name] = parameter_value

    # Pricing
    part_info['pricing'] = {}
    [pricing_key, qty_key, price_key] = PRICING_MAP

    for price_break in part[pricing_key]:
        quantity = price_break[qty_key]
        price = price_break[price_key]
        part_info['pricing'][quantity] = price

    part_info['currency'] = 'USD'

    # Extra search fields
    if settings.CONFIG_LCSC.get('EXTRA_FIELDS', None):
        for extra_field in settings.CONFIG_LCSC['EXTRA_FIELDS']:
            if part.get(extra_field, None):
                part_info['parameters'][extra_field] = part[extra_field]
            else:
                from ..common.tools import cprint
                cprint(f'[INFO]\tWarning: Extra field "{extra_field}" not found in search results', silent=False)

    return part_info


def test_api() -> bool:
    ''' Test method for API '''

    test_success = True
    # Exact-match only on stable identity fields. The free-text 'productIntroEn'
    # description is edited by LCSC from time to time, so it is checked loosely below.
    expected = {
        'productCode': 'C2181718',
        'brandNameEn': 'TDK',
        'productModel': 'C0603C0G1E101J030BA',
    }

    test_part = fetch_part_info('C2181718')
    if not test_part:
        test_success = False

    # Check content of response
    if test_success:
        for key, value in expected.items():
            actual = test_part.get(key)
            if actual != value:
                print(f'"{actual}" <> "{value}"')
                test_success = False
                break

    # Loose check on the free-text description (resilient to LCSC rewording)
    if test_success and '100pF' not in test_part.get('productIntroEn', ''):
        print(f'"100pF" not found in "{test_part.get("productIntroEn", "")}"')
        test_success = False

    return test_success
