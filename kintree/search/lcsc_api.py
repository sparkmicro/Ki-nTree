import requests


def find_categories(part_details: str):
    ''' Find categories '''
    try:
        part_details['parentCatalogName']
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

    header = [
        'productDescEn',
        'productIntroEn',
        'productCode',
        'brandNameEn',
        'productModel',
        'pdfUrl',
        'productImages',
    ]

    for key in part:
        if key in header:
            if key == 'productImages':
                try:
                    part_info[key] = part['productImages'][0]
                except IndexError:
                    pass
            else:
                part_info[key] = part[key]

    # Parameters
    part_info['parameters'] = {}
    for parameter in range(len(part['paramVOList'])):
        parameter_name = part['paramVOList'][parameter]['paramNameEn']
        parameter_value = part['paramVOList'][parameter]['paramValueEn']
        # Append to parameters dictionary
        part_info['parameters'][parameter_name] = parameter_value
    # print(part_info['parameters'])

    return part_info