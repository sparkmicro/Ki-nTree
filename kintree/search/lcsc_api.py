import requests

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


def get_default_search_keys():
    return [
        'productIntroEn',
        'productIntroEn',
        'revision',
        'keywords',
        'productCode',
        'brandNameEn',
        'productModel',
        '',
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
    from ..wrapt_timeout_decorator import timeout

    part_info = {}

    @timeout(dec_timeout=20)
    def search_timeout():
        url = 'https://wwwapi.lcsc.com/v1/products/detail?product_code=' + part_number
        response = requests.get(url)
        return response.json()

    # Query part number
    try:
        part = search_timeout()
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

    try:
        for parameter in range(len(part[parameter_key])):
            parameter_name = part[parameter_key][parameter][name_key]
            parameter_value = part[parameter_key][parameter][value_key]
            # Append to parameters dictionary
            part_info['parameters'][parameter_name] = parameter_value
    except TypeError:
        # Parameter list is empty
        pass

    return part_info


def test_api() -> bool:
    ''' Test method for API '''

    test_success = True
    expected = {
        'productIntroEn': '25V 100pF C0G ±5% 0201 Multilayer Ceramic Capacitors MLCC - SMD/SMT ROHS',
        'productCode': 'C2181718',
        'brandNameEn': 'TDK',
        'productModel': 'C0603C0G1E101J030BA',
    }

    test_part = fetch_part_info('C2181718')
        
    # Check content of response
    if test_success:
        for key, value in expected.items():
            if test_part[key] != value:
                print(f'"{test_part[key]}" <> "{value}"')
                test_success = False
                break

    return test_success
