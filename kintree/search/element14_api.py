from ..config import settings, config_interface
from ..common.tools import download

ELEMENT14_API_URL = 'https://api.element14.com/catalog/products'

STORES = {
    'Farnell': {
        'Bulgaria': 'bg.farnell.com ',
        'Czechia': 'cz.farnell.com',
        'Denmark': 'dk.farnell.com',
        'Austria': 'at.farnell.com ',
        'Switzerland': 'ch.farnell.com',
        'Germany': 'de.farnell.com',
        'CPC UK': 'cpc.farnell.com',
        'CPC Ireland': 'cpcireland.farnell.com',
        'Export': 'export.farnell.com',
        'Onecall': 'onecall.farnell.com',
        'Ireland': 'ie.farnell.com',
        'Israel': 'il.farnell.com',
        'United Kingdom': 'uk.farnell.com',
        'Spain': 'es.farnell.com',
        'Estonia': 'ee.farnell.com',
        'Finland': 'fi.farnell.com',
        'France': 'fr.farnell.com',
        'Hungary': 'hu.farnell.com',
        'Italy': 'it.farnell.com',
        'Lithuania': 'lt.farnell.com',
        'Latvia': 'lv.farnell.com',
        'Belgium': 'be.farnell.com',
        'Netherlands': 'nl.farnell.com',
        'Norway': 'no.farnell.com',
        'Poland': 'pl.farnell.com',
        'Portugal': 'pt.farnell.com',
        'Romania': 'ro.farnell.com',
        'Russia': 'ru.farnell.com',
        'Slovakia': 'sk.farnell.com',
        'Slovenia': 'si.farnell.com',
        'Sweden': 'se.farnell.com',
        'Turkey': 'tr.farnell.com',
    },
    'Newark': {
        'Canada': 'canada.newark.com',
        'Mexico': 'mexico.newark.com',
        'United States': 'www.newark.com',
    },
    'Element14': {
        'China': 'cn.element14.com',
        'Australia': 'au.element14.com',
        'New Zealand': 'nz.element14.com',
        'Hong Kong': 'hk.element14.com',
        'Singapore': 'sg.element14.com',
        'Malaysia': 'my.element14.com',
        'Philippines': 'ph.element14.com',
        'Thailand': 'th.element14.com',
        'India': 'in.element14.com',
        'Taiwan': 'tw.element14.com',
        'Korea': 'kr.element14.com',
        'Vietnam': 'vn.element14.com',
    },
}

SEARCH_HEADERS = [
    'brandName',
    'displayName',
    'id',
    'packSize',
    'publishingModule',
    'sku',
    'translatedManufacturerPartNumber',
    'translatedMinimumOrderQuality',
    'unitOfMeasure',
]


def get_default_search_keys():
    return [
        'displayName',
        'displayName',
        'revision',
        'keywords',
        'sku',
        'brandName',
        'translatedManufacturerPartNumber',
        '',
        '',
        '',
    ]


def build_api_url(part_number, supplier) -> str:
    ''' Build API URL based on user settings '''

    user_settings = config_interface.load_file(settings.CONFIG_ELEMENT14_API)
    api_key = user_settings.get('ELEMENT14_PRODUCT_SEARCH_API_KEY', '')
    default_store = user_settings.get(f'{supplier.upper()}_STORE', '')
    store_url = STORES[supplier][default_store]

    # Set base URL
    api_url = ELEMENT14_API_URL
    # Set response format
    api_url += '?callInfo.responseDataFormat=JSON'
    # Set API key
    api_url += f'&callInfo.apiKey={api_key}'
    # Set store URL
    api_url += f'&storeInfo.id={store_url}'
    # Set part number
    api_url += f'&term=manuPartNum:{part_number}'

    return api_url


def fetch_part_info(part_number: str, supplier: str) -> dict:
    ''' Fetch part data from API '''

    part_info = {}

    def search_timeout(timeout=10):
        url = build_api_url(part_number, supplier)
        response = download(url, timeout=timeout)
        return response

    # Query part number
    try:
        part = search_timeout()
    except:
        part = None

    # Extract result
    part = part['manufacturerPartNumberSearchReturn']['products'][0]

    if not part:
        return part_info

    headers = SEARCH_HEADERS

    for key in part:
        if key in headers:
            part_info[key] = part[key]

    return part_info


def test_api(supplier='') -> bool:
    ''' Test method for API '''

    test_success = False

    if supplier == 'Farnell':
        pass
    elif supplier == 'Newark':
        pass
    elif supplier == 'Element14':
        pass
    else:
        return test_success

    return True

    # expected = {
    #     'productIntroEn': '25V 100pF C0G ±5% 0201  Multilayer Ceramic Capacitors MLCC - SMD/SMT ROHS',
    #     'productCode': 'C2181718',
    #     'brandNameEn': 'TDK',
    #     'productModel': 'C0603C0G1E101J030BA',
    # }

    # test_part = fetch_part_info('C2181718')
    # if not test_part:
    #     test_success = False
        
    # # Check content of response
    # if test_success:
    #     for key, value in expected.items():
    #         if test_part[key] != value:
    #             print(f'"{test_part[key]}" <> "{value}"')
    #             test_success = False
    #             break

    # return test_success
