import base64
import collections
import hashlib
import hmac
import os
import urllib.parse
import urllib.request

from ..common.tools import download
from ..config import config_interface, settings

PRICING_MAP = [
    'PriceList',
    'Amount',
    'PriceValue',
    'Currency',
]


def get_default_search_keys():
    return [
        'Symbol',
        'Description',
        '',  # Revision
        'Category',
        'Symbol',
        'Producer',
        'OriginalSymbol',
        'ProductInformationPage',
        'Datasheet',
        'Photo',
    ]


def check_environment() -> bool:
    TME_API_TOKEN = os.environ.get('TME_API_TOKEN', None)
    TME_API_SECRET = os.environ.get('TME_API_SECRET', None)

    if not TME_API_TOKEN or not TME_API_SECRET:
        return False

    return True


def setup_environment(force=False) -> bool:
    if not check_environment() or force:
        tme_api_settings = config_interface.load_file(settings.CONFIG_TME_API)
        os.environ['TME_API_TOKEN'] = tme_api_settings.get('TME_API_TOKEN', None)
        os.environ['TME_API_SECRET'] = tme_api_settings.get('TME_API_SECRET', None)

    return check_environment()


# Based on TME API snippets mentioned in API documentation: https://developers.tme.eu/documentation/download
# https://github.com/tme-dev/TME-API/blob/master/Python/call.py
def tme_api_request(endpoint, tme_api_settings, part_number, api_host='https://api.tme.eu', format='json', **kwargs):
    TME_API_TOKEN = tme_api_settings.get('TME_API_TOKEN', None)
    TME_API_SECRET = tme_api_settings.get('TME_API_SECRET', None)

    params = collections.OrderedDict()
    params['Country'] = tme_api_settings.get('TME_API_COUNTRY', 'US')
    params['Language'] = tme_api_settings.get('TME_API_LANGUAGE', 'EN')
    params['SymbolList[0]'] = part_number
    if kwargs.get('currency', None):
        params['Currency'] = kwargs.get('currency')
    if not TME_API_TOKEN and not TME_API_SECRET:
        TME_API_TOKEN = os.environ.get('TME_API_TOKEN', None)
        TME_API_SECRET = os.environ.get('TME_API_SECRET', None)
    if not TME_API_TOKEN and not TME_API_SECRET:
        return None
    params['Token'] = TME_API_TOKEN

    url = api_host + endpoint + '.' + format
    encoded_params = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    signature_base = 'POST' + '&' + urllib.parse.quote(url, '') + '&' + urllib.parse.quote(encoded_params, '')
    hmac_value = hmac.new(
        TME_API_SECRET.encode(),
        signature_base.encode(),
        hashlib.sha1
    ).digest()
    api_signature = base64.encodebytes(hmac_value).rstrip()
    params['ApiSignature'] = api_signature

    data = urllib.parse.urlencode(params).encode()
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
    }
    return urllib.request.Request(url, data, headers)


def fetch_part_info(part_number: str) -> dict:

    def search_product(response):
        found = False
        index = 0
        for product in response['Data']['ProductList']:
            if product['Symbol'] == part_number:
                found = True
                break
            index = index + 1
        return found, index

    tme_api_settings = config_interface.load_file(settings.CONFIG_TME_API)
    response = download(tme_api_request('/Products/GetProducts', tme_api_settings, part_number))
    if response is None or response['Status'] != 'OK':
        return {}
    # in the case if multiple parts returned
    # (for e.g. if we looking for NE555A we could have NE555A and NE555AB in the results)
    found = False
    index = 0
    for product in response['Data']['ProductList']:
        if product['Symbol'] == part_number:
            found = True
            break
        index = index + 1

    if not found:
        return {}
    part_info = response['Data']['ProductList'][index]
    part_info['Photo'] = "http:" + part_info['Photo']
    part_info['ProductInformationPage'] = "http:" + part_info['ProductInformationPage']
    part_info['category'] = part_info['Category']
    part_info['subcategory'] = None

    # query the parameters
    response = download(tme_api_request('/Products/GetParameters', tme_api_settings, part_number))
    # check if accidentally no data returned
    if response is None or response['Status'] != 'OK':
        return part_info

    found, index = search_product(response)

    if not found:
        return part_info

    part_info['parameters'] = {}
    for param in response['Data']['ProductList'][index]["ParameterList"]:
        part_info['parameters'][param['ParameterName']] = param['ParameterValue']

    # query the prices
    response = download(tme_api_request('/Products/GetPrices', tme_api_settings, part_number, currency='USD'))
    # check if accidentally no data returned
    if response is None or response['Status'] != 'OK':
        return part_info

    found, index = search_product(response)

    if not found:
        part_info['currency'] = 'USD'
        return part_info

    part_info['pricing'] = {}
    [pricing_key, qty_key, price_key, currency_key] = PRICING_MAP

    for price_break in response['Data']['ProductList'][index][pricing_key]:
        quantity = price_break[qty_key]
        price = price_break[price_key]
        part_info['pricing'][quantity] = price

    part_info['currency'] = response['Data'][currency_key]

    # Query the files associated to the product
    response = download(tme_api_request('/Products/GetProductsFiles', tme_api_settings, part_number))
    # check if accidentally no products returned
    if response is None or response['Status'] != 'OK':
        return part_info

    found, index = search_product(response)

    if not found:
        return part_info

    for doc in response['Data']['ProductList'][index]['Files']['DocumentList']:
        if doc['DocumentType'] == 'DTE':
            part_info['Datasheet'] = 'http:' + doc['DocumentUrl']
            break
    return part_info


def test_api(check_content=False) -> bool:
    ''' Test method for API '''
    setup_environment()

    test_success = True
    expected = {
        'Description': 'Capacitor: ceramic; MLCC; 33pF; 50V; C0G; ±5%; SMD; 0402',
        'Symbol': 'CL05C330JB5NNNC',
        'Producer': 'SAMSUNG',
        'OriginalSymbol': 'CL05C330JB5NNNC',
        'ProductInformationPage': 'http://www.tme.eu/en/details/cl05c330jb5nnnc/mlcc-smd-capacitors/samsung/',
        'Datasheet': 'http://www.tme.eu/Document/7da762c1dbaf553c64ad9c40d3603826/mlcc_samsung.pdf',
        'Photo': 'http://ce8dc832c.cloudimg.io/v7/_cdn_/8D/4E/00/00/0/58584_1.jpg?width=640&height=480&wat=1&wat_url=_tme-wrk_%2Ftme_new.png&wat_scale=100p&ci_sign=be42abccf5ef8119c2a0d945a27afde3acbeb699',
    }

    test_part = fetch_part_info('CL05C330JB5NNNC')

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
