from ..common.tools import download

# These are the 'keys' we want to pull out response
SEARCH_HEADERS = [
    'item_code',          # name
    'primary_desc',       # description
    'revision',           # revision
    'keywords',           # keywords
    'item_code',          # suppli er_part_number
    'manufacturer_name',  # manufacturer_name
    'item_code',          # manufacturer_part_number
    'url_fullpath',       # supplier_link
    'spec_url',           # datasheet
    'image_file_name',    # image

    'insert_url',         # insert PD
    'orderable_flg',
    'prod_status',
    'price',
    'manual_url',         # not full path to html page, value is filename.html
    'unit_of_measure',
    'leadtime_cd',
    'production_time',
    'warranty',
]

PARAMETERS_MAP = [
    'tech_attributes',  # List of parameters, not list of dictionaries, changes based on product returned
]

PRICING_MAP = [
    'ordering_attributes',  # List, e.g. ['Is Cut To Length: True', 'Maximum Cut Length: 2500', 'Minimum Cut Length: 25']
    'price',                # Automation Direct only has one price, no price breaks
    'unit_of_measure',      # e.g. 'FT'
]


def get_default_search_keys():
    return [
        # Order matters
        'item_code',          # name
        'primary_desc',       # description
        'revision',           # revision
        'keywords',           # keywords
        'item_code',          # supplier_part_number
        'manufacturer_name',  # manufacturer_name
        'item_code',          # manufacturer_part_number
        'url_fullpath',       # supplier_link
        'spec_url',           # datasheet
        'image_file_name',    # image
    ]


def find_categories(part_details: str):
    ''' Find categories '''
    try:
        return part_details['parentCatalogName'], part_details['catalogName']
    except:
        return None, None


def fetch_part_info(part_number: str, silent=False) -> dict:
    ''' Fetch part data from API '''

    # Load Automation Direct settingss
    import re
    from ..common.tools import cprint
    from ..config import settings, config_interface
    automationdirect_api_settings = config_interface.load_file(settings.CONFIG_AUTOMATIONDIRECT_API)

    part_info = {}

    def search_timeout(timeout=10):
        url = automationdirect_api_settings.get('AUTOMATIONDIRECT_API_URL', '') + automationdirect_api_settings.get('AUTOMATIONDIRECT_API_SEARCH_QUERY', '') + part_number + automationdirect_api_settings.get('AUTOMATIONDIRECT_API_SEARCH_STRING', '') + part_number
        response = download(url, timeout=timeout)
        return response

    # Query part number
    try:
        part = search_timeout()
        part = part['solrResult']['response']   # extract the data for parts returned
        if part['numFound'] > 0:
            if part['numFound'] == 1:
                cprint(f'[INFO]\tFound exactly one result for "{part_number}"', silent=True)
            else:
                cprint(f'[INFO]\tFound {part["numFound"]} results for "{part_number}", selecting first result', silent=False)
            part = part['docs'][0]              # choose the first part in the returned returned list
    except Exception as e:
        cprint(f'[INFO]\tError: fetch_part_info(): {repr(e)}')
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

    headers = SEARCH_HEADERS  # keys we want to search for

    # Get all returned data we want
    for key in part:
        if key in headers:
            if key == 'image_file_name':  # JSON only returns image name, need to add path
                try:
                    part_info[key] = automationdirect_api_settings.get('AUTOMATIONDIRECT_API_IMAGE_PATH', '') + part['image_file_name']
                except IndexError:
                    pass
            elif key == 'spec_url':  # datasheet url returns partial path, need to add ROOT URL
                try:
                    part_info[key] = automationdirect_api_settings.get('AUTOMATIONDIRECT_API_ROOT_URL', '') + part['spec_url']
                except IndexError:
                    pass
            elif key == 'insert_url':  # insert url returns partial path, need to add ROOT URL
                try:
                    part_info[key] = automationdirect_api_settings.get('AUTOMATIONDIRECT_API_ROOT_URL', '') + part['insert_url']
                except IndexError:
                    pass
            elif key == 'manual_url':  # manul url returns .html file name, need to build the rest of the URL
                try:
                    part_info[key] = automationdirect_api_settings.get('AUTOMATIONDIRECT_API_ROOT_URL', '') + '/static/manuals/' + str(part['manual_url']).rsplit('.', 1)[0] + '/' + part['manual_url']
                except IndexError:
                    pass
            elif key == 'url_fullpath':  # despite being named fullpath, the URL needs the TLD as a prefix
                try:
                    part_info[key] = automationdirect_api_settings.get('AUTOMATIONDIRECT_API_ROOT_URL', '') + '/adc/shopping' + str(part['url_fullpath'])
                except IndexError:
                    pass
            elif key == 'manufacturer_name':  # taken care of in parameter list below
                pass
            else:
                part_info[key] = part[key]

    # Parameters
    part_info['parameters'] = {}
    [parameter_key] = PARAMETERS_MAP

    if part.get(parameter_key, ''):
        for attribute in part[parameter_key]:
            attribute_list = [x.strip() for x in attribute.split(':')]
            parameter_name = attribute_list[0]
            parameter_name = parameter_name.replace('/', '')
            parameter_value = attribute_list[1]
            try:
                html_li_list = re.split("</?\s*[a-z-][^>]*\s*>|(\&(?:[\w\d]+|#\d+|#x[a-f\d]+);)", parameter_value)
                cleaned_html_li_list = list(filter(None, html_li_list))
                parameter_value = ', '.join(cleaned_html_li_list)
            except Exception as e:
                print(f'{repr(e)}')
            if parameter_name == "Brand":  # Manufacturer Name returned as a parameter, pick it out of parameters list aand store it appropriately
                part_info['manufacturer_name'] = parameter_value
            # Nominal Input Voltage gives range min-max, parse it out to put in min/max params
            if parameter_name == "Nominal Input Voltage":
                if parameter_value.count('-') == 1:
                    parameter_value = re.sub('[^\d-]+', '', parameter_value)
                    values_list = parameter_value.split('-')
                    min_value = min(values_list)
                    max_value = max(values_list)
                    part_info['parameters']['Min Input Voltage'] = min_value
                    part_info['parameters']['Max Input Voltage'] = max_value
                else:
                    # more than one range, copy into set param fields
                    part_info['parameters']['Min Input Voltage'] = parameter_value
                    part_info['parameters']['Max Input Voltage'] = parameter_value
            # Nominal Output Voltage gives range min-max, parse it out to put in min/max params
            if parameter_name == "Nominal Output Voltage":
                if parameter_value.count('-') == 1:
                    parameter_value = re.sub('[^\d-]+', '', parameter_value)
                    values_list = parameter_value.split('-')
                    min_value = min(values_list)
                    max_value = max(values_list)
                    part_info['parameters']['Min Output Voltage'] = min_value
                    part_info['parameters']['Max Output Voltage'] = max_value
                else:
                    # more than one range, copy into set param fields
                    part_info['parameters']['Min Output Voltage'] = parameter_value
                    part_info['parameters']['Max Output Voltage'] = parameter_value
            else:
                # Append to parameters dictionary
                part_info['parameters'][parameter_name] = parameter_value

    # Pricing
    part_info['pricing'] = {}
    [ordering_attributes, price_key, unit_per_price] = PRICING_MAP

    # Parse out ordering attributes
    pricing_attributes = {}
    price_per_unit = part[price_key]
    try:
        for attribute in part[ordering_attributes]:
            attribute = attribute.split(':')
            attribute = [x.strip() for x in attribute]
            pricing_attributes[str(attribute[0])] = attribute[1]

        min_quantity = int(pricing_attributes['Minimum Cut Length'])
        max_quanitity = int(pricing_attributes['Maximum Cut Length'])
        
        price_per_unit = part[price_key]

        # Automation Direct doesn't have price breaks, but we can create common set quanitities for reference
        quantities = [100, 250, 500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000, 12000, 14000, 15000]
        quantities.insert(0, min_quantity)
        quantities.append(max_quanitity)
        quantities.sort()
        quantities = [qty for qty in quantities if qty <= max_quanitity]
        for i in range(len(quantities) - 1):
            part_info['pricing'][quantities[i]] = price_per_unit
    
    except KeyError as e:
        from ..common.tools import cprint
        cprint(f'[INFO]\tNo pricing attribute "{e.args[0]}" found for "{part_number}"', silent=silent)
        part_info['pricing']['1'] = price_per_unit

    part_info['currency'] = 'USD'

    # Extra search fields
    if settings.CONFIG_AUTOMATIONDIRECT.get('EXTRA_FIELDS', None):
        for extra_field in settings.CONFIG_AUTOMATIONDIRECT['EXTRA_FIELDS']:
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
        'image_file_name': 'https://cdn.automationdirect.com/images/products/medium/m_bx16nd3.jpg',
        'item_code': 'BX-16ND3',
        'manual_url': 'https://www.automationdirect.com/static/manuals/brxuserm/brxuserm.html',
        'unit_of_measure': 'EA',
        "parameters":
            {
                'Brand': 'BRX',
                'Item': 'Input module',
                'IO Module Type': 'Discrete',
                'Number of Input Points': '16',
                'Min Input Voltage': '12',
                'Max Input Voltage': '24',
                'Nominal Input Voltage': '12-24',
                'Discrete Input Type': 'Sinking/sourcing',
                'Fast Response': 'No', 'Number of Isolated Input Commons': '4',
                'Number of Points per Common': '4',
                'Requires': 'BX-RTB10, BX-RTB10-1 or BX-RTB10-2 terminal block kit or ZIPLink pre-wired cables',
                'Programming Software': 'Do-more Designer programming software v2.0 or later'
            }
    }

    test_part = fetch_part_info('BX-16ND3', silent=True)
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
