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
    
]

PARAMETERS_MAP = [
    
]


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
