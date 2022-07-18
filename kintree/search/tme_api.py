import os

from ..database import inventree_api
from ..database import inventree_interface

from .tme.tmeapi import Client
from ..config import settings, config_interface
from ..common.tools import download_request


def create_category_recursive(category, parent_pk, category_counter):
    pk = inventree_api.create_category_force(parent_pk, category['Name'])
    category_counter = category_counter + 1
    if not category['SubTree'] is None:
        for sub_tree in category['SubTree']:
            create_category_recursive(category, pk, category_counter)


def createAllCategories() -> int:
    inventree_connect = inventree_interface.connect_to_server()

    if not inventree_connect:
        return 0

    category_counter = 0
    tme_api_settings = config_interface.load_file(settings.CONFIG_TME_API)
    tme_client = Client(tme_api_settings['TME_API_TOKEN'], tme_api_settings['TME_API_SECRET'])
    params = {
        'Country': tme_api_settings['TME_API_COUNTRY'],
        'Language': tme_api_settings['TME_API_LANGUAGE'],
        'Tree': True
    }

    response = download_request(tme_client.request('/Products/GetCategories', params))
    if response is None or response['Status'] != 'OK':
        return 0

    for category in response['Data']['CategoryTree']['SubTree']:
        create_category_recursive(category, None, category_counter)
    return category_counter


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
        os.environ['TME_API_TOKEN'] = tme_api_settings['TME_API_TOKEN']
        os.environ['TME_API_SECRET'] = tme_api_settings['TME_API_SECRET']

    return check_environment()


def fetch_part_info(part_number: str) -> dict:
    tme_api_settings = config_interface.load_file(settings.CONFIG_TME_API)
    tme_client = Client(tme_api_settings['TME_API_TOKEN'], tme_api_settings['TME_API_SECRET'])
    get_params_params = get_prod_params = get_files_params = {
        'Country': tme_api_settings['TME_API_COUNTRY'],
        'Language': tme_api_settings['TME_API_LANGUAGE'],
        'SymbolList[0]': part_number,
    }

    response = download_request(tme_client.request('/Products/GetProducts', get_prod_params))
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
    response = download_request(tme_client.request('/Products/GetParameters', get_params_params))
    # check if accidentally no data returned
    if response is None or response['Status'] != 'OK':
        return part_info

    found = False
    index = 0
    for product in response['Data']['ProductList']:
        if product['Symbol'] == part_number:
            found = True
            break
        index = index + 1

    if not found:
        return part_info

    part_info['parameters'] = {}
    for param in response['Data']['ProductList'][index]["ParameterList"]:
        part_info['parameters'][param['ParameterName']] = param['ParameterValue']

    # Query the files associated to the product
    response = download_request(tme_client.request('/Products/GetProductsFiles', get_files_params))
    # check if accidentally no products returned
    if response is None or response['Status'] != 'OK':
        return part_info

    found = False
    index = 0
    for product in response['Data']['ProductList']:
        if product['Symbol'] == part_number:
            found = True
            break
        index = index + 1

    if not found:
        return part_info

    for doc in response['Data']['ProductList'][index]['Files']['DocumentList']:
        if doc['DocumentType'] == 'DTE':
            part_info['Datasheet'] = 'http:' + doc['DocumentUrl']
            break
    '''

    # Parameters
    tmePart['parameters'] = {}
    [parameter_key, name_key, value_key] = PARAMETERS_MAP

    try:
        for parameter in range(len(part[parameter_key])):
            parameter_name = part[parameter_key][parameter][name_key]
            parameter_value = part[parameter_key][parameter][value_key]
            # Append to parameters dictionary
            part_info['parameters'][parameter_name] = parameter_value
    except TypeError:
        # Parameter list is empty
        pass'''
    return part_info


def get_lang_list(token, secret) -> list:
    tme_client = Client(token, secret)
    response = download_request(tme_client.request('/Utils/GetLanguages', {}))
    if response['Status'] == "OK":
        return response['Data']['LanguageList']
    return []


def get_country_list(token, secret) -> []:
    tme_client = Client(token, secret)
    response = download_request(tme_client.request('/Utils/GetCountries', {'Language': 'EN'}))
    if response['Status'] == "OK":
        ret = []
        for country in response['Data']['CountryList']:
            ret.append(country['CountryId'])
        return ret
    return []


def test_api() -> bool:
    ''' Test method for API '''
    setup_environment()
    tme_client = Client(os.environ['TME_API_TOKEN'], os.environ['TME_API_SECRET'])
    jsonResponse = download_request(tme_client.request('/Utils/Ping', {}))
    return jsonResponse['Status'] == "OK"
