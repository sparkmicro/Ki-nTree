import logging
import os
import time
from importlib import import_module

import requests

try:
    dk_api_client = import_module('dk_api_client')
except ModuleNotFoundError:
    dk_api_client = None

from ..config import settings, config_interface

SEARCH_HEADERS = [
    'description',
    'digi_key_part_number',
    'manufacturer',
    'manufacturer_product_number',
    'product_url',
    'datasheet_url',
    'photo_url',
]
PARAMETERS_MAP = [
    'parameters',
    'parameter_text',
    'value_text',
]

PRICING_MAP = [
    'product_variations',
    'digi_key_product_number',
    'standard_pricing',
    'break_quantity',
    'unit_price',
    'package_type'
]

TOKEN_URL = 'https://api.digikey.com/v1/oauth2/token'
_token_cache = {
    'access_token': None,
    'expires_at': 0,
}

os.environ['DIGIKEY_STORAGE_PATH'] = settings.DIGIKEY_STORAGE_PATH
# Check if storage path exists, else create it
if not os.path.exists(os.environ['DIGIKEY_STORAGE_PATH']):
    os.makedirs(os.environ['DIGIKEY_STORAGE_PATH'], exist_ok=True)


def disable_api_logger():
    # Digi-Key API logger
    logging.getLogger('dk_api_client').setLevel(logging.CRITICAL)
    # Disable DEBUG
    logging.disable(logging.DEBUG)


def _normalize_object(value):
    if value is None:
        return None

    if hasattr(value, 'to_dict'):
        try:
            return value.to_dict()
        except Exception:
            pass

    if isinstance(value, dict):
        return {k: _normalize_object(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_normalize_object(item) for item in value]

    return value


def _get_access_token() -> str:
    now = int(time.time())
    if _token_cache['access_token'] and _token_cache['expires_at'] > now + 30:
        return _token_cache['access_token']

    client_id = os.environ.get('DIGIKEY_CLIENT_ID', '').strip()
    client_secret = os.environ.get('DIGIKEY_CLIENT_SECRET', '').strip()

    if not client_id or not client_secret:
        return ''

    response = requests.post(
        TOKEN_URL,
        data={'grant_type': 'client_credentials'},
        auth=(client_id, client_secret),
        timeout=20,
    )
    response.raise_for_status()

    payload = response.json() if response.text else {}
    access_token = str(payload.get('access_token', '')).strip()
    expires_in = int(payload.get('expires_in', 0) or 0)

    if not access_token:
        return ''

    _token_cache['access_token'] = access_token
    _token_cache['expires_at'] = now + max(60, expires_in)

    return access_token


def _extract_product_from_response(response_dict: dict):
    if not isinstance(response_dict, dict):
        return None, ''

    currency = ''
    search_locale = response_dict.get('search_locale_used', {})
    if isinstance(search_locale, dict):
        currency = str(search_locale.get('currency', '') or '').strip()

    if response_dict.get('product'):
        return response_dict.get('product'), currency

    products = response_dict.get('products')
    if isinstance(products, list) and products:
        return products[0], currency

    if response_dict.get('product_details'):
        return response_dict.get('product_details'), currency

    return response_dict, currency


def _normalize_url(value):
    url = str(value or '').strip()
    if not url:
        return ''
    if url.startswith('//'):
        return f'https:{url}'
    return url


def check_environment() -> bool:
    DIGIKEY_CLIENT_ID = os.environ.get('DIGIKEY_CLIENT_ID', None)
    DIGIKEY_CLIENT_SECRET = os.environ.get('DIGIKEY_CLIENT_SECRET', None)

    if not DIGIKEY_CLIENT_ID or not DIGIKEY_CLIENT_SECRET:
        return False

    return True


def setup_environment(force=False) -> bool:
    if not check_environment() or force:
        # SETUP the Digikey authentication see https://developer.digikey.com/documentation/organization#production
        digikey_api_settings = config_interface.load_file(settings.CONFIG_DIGIKEY_API)
        os.environ['DIGIKEY_CLIENT_ID'] = digikey_api_settings['DIGIKEY_CLIENT_ID']
        os.environ['DIGIKEY_CLIENT_SECRET'] = digikey_api_settings['DIGIKEY_CLIENT_SECRET']
        os.environ['DIGIKEY_LOCAL_SITE'] = digikey_api_settings.get('DIGIKEY_LOCAL_SITE', 'US')
        os.environ['DIGIKEY_LOCAL_LANGUAGE'] = digikey_api_settings.get('DIGIKEY_LOCAL_LANGUAGE', 'en')
        os.environ['DIGIKEY_LOCAL_CURRENCY'] = digikey_api_settings.get('DIGIKEY_LOCAL_CURRENCY', 'USD')
    return check_environment()


def get_default_search_keys():
    return [
        'manufacturer_product_number',
        'product_description',
        'revision',
        'keywords',
        'digi_key_part_number',
        'manufacturer',
        'manufacturer_product_number',
        'product_url',
        'datasheet_url',
        'photo_url',
    ]


def find_categories(part_details: str):
    ''' Find categories '''
    category = part_details.get('category')
    subcategory = None
    if isinstance(category, dict):
        children = category.get('child_categories') or category.get('children') or []
        if isinstance(children, list) and children:
            first_child = children[0]
            if isinstance(first_child, dict):
                subcategory = first_child.get('name')
            else:
                subcategory = str(first_child)
        category = category.get('name')
    elif category:
        category = str(category)
    if subcategory:
        subcategory = str(subcategory)
    return category, subcategory


def fetch_part_info(part_number: str) -> dict:
    ''' Fetch part data from API '''
    from wrapt_timeout_decorator import timeout

    part_info = {}
    if not setup_environment():
        from ..common.tools import cprint
        cprint('[INFO]\tWarning: DigiKey API settings are not configured')
        return part_info

    if dk_api_client is None:
        from ..common.tools import cprint
        cprint('[INFO]\tWarning: digikey-apiv4 package is not installed')
        return part_info

    # THIS METHOD CAN SOMETIMES RETURN INCORRECT MATCH
    # Added logic to check the result in the GUI flow
    @timeout(dec_timeout=20)
    def digikey_search_timeout():
        access_token = _get_access_token()
        if not access_token:
            return None

        configuration = dk_api_client.Configuration()
        configuration.api_key['X-DIGIKEY-Client-Id'] = os.environ['DIGIKEY_CLIENT_ID']
        configuration.access_token = access_token

        api_client = dk_api_client.ApiClient(configuration)
        api_instance = dk_api_client.ProductSearchApi(api_client)

        result = api_instance.product_details(
            part_number,
            x_digikey_client_id=os.environ['DIGIKEY_CLIENT_ID'],
            x_digikey_locale_site=os.environ['DIGIKEY_LOCAL_SITE'],
            x_digikey_locale_language=os.environ['DIGIKEY_LOCAL_LANGUAGE'],
            x_digikey_locale_currency=os.environ['DIGIKEY_LOCAL_CURRENCY'],
        )
        return _normalize_object(result)

    # Method to process price breaks
    def process_price_break(product_variation):
        part_info['digi_key_part_number'] = product_variation.get(digi_number_key)
        for price_break in product_variation[pricing_key]:
            quantity = price_break[qty_key]
            price = price_break[price_key]
            part_info['pricing'][quantity] = price

    # Query part number
    try:
        part = digikey_search_timeout()
    except Exception:
        part = None

    if not part:
        return part_info

    part, currency = _extract_product_from_response(part)
    if not part:
        return part_info

    part_info['currency'] = currency or os.environ.get('DIGIKEY_LOCAL_CURRENCY', 'USD')

    category, subcategory = find_categories(part)
    try:
        part_info['category'] = category
        part_info['subcategory'] = subcategory
    except Exception:
        part_info['category'] = ''
        part_info['subcategory'] = ''

    headers = SEARCH_HEADERS

    for key in part:
        if key in headers:
            if key == 'manufacturer':
                manufacturer = part.get('manufacturer', {})
                part_info[key] = manufacturer.get('name') if isinstance(manufacturer, dict) else str(manufacturer)
            elif key == 'description':
                description = part.get('description', {})
                if isinstance(description, dict):
                    product_name = part.get('name') or description.get('name') or description.get('product_name') or ''
                    product_description = description.get('product_description') or description.get('detailed_description') or product_name
                    detailed = description.get('detailed_description') or product_description
                else:
                    product_name = str(description or '')
                    product_description = product_name
                    detailed = ''
                product_name = str(product_name or '')
                product_description = str(product_description or product_name)
                detailed = str(detailed or product_name)
                part_info['product_name'] = product_name
                part_info['product_description'] = product_description
                part_info['detailed_description'] = detailed
            else:
                value = part[key]
                if key in {'datasheet_url', 'photo_url', 'product_url'}:
                    value = _normalize_url(value)
                part_info[key] = value

    # Parameters
    part_info['parameters'] = {}
    [parameter_key, name_key, value_key] = PARAMETERS_MAP

    for parameter in part.get(parameter_key, []):
        parameter_name = parameter.get(name_key) or parameter.get('name', '')
        parameter_value = parameter.get(value_key) or parameter.get('value', '')
        # Append to parameters dictionary
        part_info['parameters'][parameter_name] = parameter_value
    # process classifications as parameters
    for classification, value in part.get('classifications', {}).items():
        part_info['parameters'][classification] = value

    # Pricing
    part_info['pricing'] = {}
    [variations_key,
     digi_number_key,
     pricing_key,
     qty_key,
     price_key,
     package_key] = PRICING_MAP

    variations = part.get(variations_key, [])
    if len(variations) == 1:
        process_price_break(variations[0])
    else:
        for variation in variations:
            # we try to get the not TR or Digi-Reel option
            package = variation.get(package_key, {})
            package_type = package.get('id') if isinstance(package, dict) else None
            if all(package_type != x for x in [1, 243]):
                process_price_break(variation)
                break
    # if no other option was found use the first one returned
    if not part_info['pricing'] and variations:
        process_price_break(variations[0])

    # Extra search fields
    if settings.CONFIG_DIGIKEY.get('EXTRA_FIELDS'):
        for extra_field in settings.CONFIG_DIGIKEY['EXTRA_FIELDS']:
            if part.get(extra_field):
                part_info['parameters'][extra_field] = part[extra_field]
            else:
                from ..common.tools import cprint
                cprint(f'[INFO]\tWarning: Extra field "{extra_field}" not found in search results', silent=False)

    return part_info


def test_api(check_content=False) -> bool:
    ''' Test method for API token '''
    test_success = True
    expected = {
        'product_description': 'RES 10K OHM 5% 1/16W 0402',
        'digi_key_part_number': 'RMCF0402JT10K0CT-ND',
        'manufacturer': 'Stackpole Electronics Inc',
        'manufacturer_product_number': 'RMCF0402JT10K0',
        'product_url': 'https://www.digikey.com/en/products/detail/stackpole-electronics-inc/RMCF0402JT10K0/1758206',
        'datasheet_url': 'https://www.seielect.com/catalog/sei-rmcf_rmcp.pdf',
        'photo_url': 'https://mm.digikey.com/Volume0/opasdata/d220001/medias/images/2597/MFG_RMC SERIES.jpg',
    }

    test_part = fetch_part_info('RMCF0402JT10K0')

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
