import logging
import os
import digikey

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

os.environ['DIGIKEY_STORAGE_PATH'] = settings.DIGIKEY_STORAGE_PATH
# Check if storage path exists, else create it
if not os.path.exists(os.environ['DIGIKEY_STORAGE_PATH']):
    os.makedirs(os.environ['DIGIKEY_STORAGE_PATH'], exist_ok=True)


def disable_api_logger():
    # Digi-Key API logger
    logging.getLogger('digikey.v3.api').setLevel(logging.CRITICAL)
    # Disable DEBUG
    logging.disable(logging.DEBUG)


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
        'product_description',
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
    if category:
        subcategory = category.get('child_categories')[0]
        category = category.get('name')
    if subcategory:
        subcategory = subcategory.get('name')
    return category, subcategory


def fetch_part_info(part_number: str) -> dict:
    ''' Fetch part data from API '''
    from wrapt_timeout_decorator import timeout

    part_info = {}
    if not setup_environment():
        from ..common.tools import cprint
        cprint('[INFO]\tWarning: DigiKey API settings are not configured')
        return part_info

    # THIS METHOD CAN SOMETIMES RETURN INCORRECT MATCH
    # Added logic to check the result in the GUI flow
    @timeout(dec_timeout=20)
    def digikey_search_timeout():
        return digikey.product_details(
            part_number,
            x_digikey_locale_site=os.environ['DIGIKEY_LOCAL_SITE'],
            x_digikey_locale_language=os.environ['DIGIKEY_LOCAL_LANGUAGE'],
            x_digikey_locale_currency=os.environ['DIGIKEY_LOCAL_CURRENCY'],
        ).to_dict()

    # THIS METHOD WILL NOT WORK WITH DIGI-KEY PART NUMBERS...
    # @timeout(dec_timeout=20)
    # def digikey_search_timeout():
    #     from digikey.v3.productinformation.models.manufacturer_product_details_request import ManufacturerProductDetailsRequest
    #     # Set parametric filter for Cut Tape
    #     parametric_filters = {
    #         "ParameterId": 7,
    #         "ValueId": "2",
    #     }
    #     # Create search request body
    #     # TODO: record_count and filters parameter do not seem to work as intended
    #     search_request = ManufacturerProductDetailsRequest(manufacturer_product=part_number, record_count=1, filters=parametric_filters)
    #     # Run search
    #     manufacturer_product_details = digikey.manufacturer_product_details(body=search_request).to_dict()
    #     from ..common.tools import cprint
    #     print(f'length of response = {len(manufacturer_product_details.get("product_details", None))}')
    #     if type(manufacturer_product_details.get('product_details', None)) == list:
    #         # Return the first item only
    #         return manufacturer_product_details.get('product_details', None)[0]
    #     else:
    #         return {}
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
    except:
        part = None

    if not part:
        return part_info
    if 'product' not in part or not part['product']:
        return part_info

    part_info['currency'] = part['search_locale_used']['currency']
    part = part['product']

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
            if key == 'manufacturer':
                part_info[key] = part['manufacturer'].get('name')
            elif key == 'description':
                part_info['product_description'] = part['description'].get('product_description')
                part_info['detailed_description'] = part['description'].get('detailed_description')
            else:
                part_info[key] = part[key]

    # Parameters
    part_info['parameters'] = {}
    [parameter_key, name_key, value_key] = PARAMETERS_MAP

    for parameter in part[parameter_key]:
        parameter_name = parameter.get(name_key, '')
        parameter_value = parameter.get(value_key, '')
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

    variations = part[variations_key]
    if len(variations) == 1:
        process_price_break(variations[0])
    else:
        for variation in variations:
            # we try to get the not TR or Digi-Reel option
            package_type = variation.get(package_key).get('id')
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
    setup_environment()

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
