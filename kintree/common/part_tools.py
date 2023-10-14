import re

from ..config import settings
from ..config import config_interface
from .tools import cprint


def generate_part_number(category: str, part_pk: int, category_code='') -> str:
    ''' Generate Internal Part Number (IPN) '''
    ipn_elements = []

    # Prefix
    if settings.CONFIG_IPN.get('IPN_ENABLE_PREFIX', False):
        ipn_elements.append(settings.CONFIG_IPN.get('IPN_PREFIX', ''))
    
    # Category code
    if settings.CONFIG_IPN.get('IPN_CATEGORY_CODE', False):
        if not category_code:
            CATEGORY_CODES = config_interface.load_file(settings.CONFIG_CATEGORIES)['CODES']
            try:
                category_code = CATEGORY_CODES.get(category, '')
            except AttributeError:
                category_code = None
        if category_code:
            ipn_elements.append(category_code)

    # Unique ID (mandatory)
    try:
        unique_id = str(part_pk).zfill(int(settings.CONFIG_IPN.get('IPN_UNIQUE_ID_LENGTH', '6')))
    except:
        return None
    ipn_elements.append(unique_id)
    
    # Suffix
    if settings.CONFIG_IPN.get('IPN_ENABLE_SUFFIX', False):
        ipn_elements.append(settings.CONFIG_IPN.get('IPN_SUFFIX', ''))
    
    # Build IPN
    ipn = '-'.join(ipn_elements)

    return ipn


def compare(new_part_parameters: dict, db_part_parameters: dict, include_filters: list) -> bool:
    ''' Compare two InvenTree parts based on parameters (specs) '''
    try:
        for parameter, value in new_part_parameters.items():
            # Check for filters
            if include_filters:
                # Compare only parameters present in include_filters
                if parameter in include_filters and value != db_part_parameters[parameter]:
                    return False
            else:
                # Compare all parameters
                if value != db_part_parameters[parameter]:
                    return False
    except KeyError:
        cprint('[INFO]\tWarning: Failed to compare part with database', silent=settings.HIDE_DEBUG)
        return False

    return True


def clean_parameter_value(category: str, name: str, value: str) -> str:
    ''' Clean-up parameter value for consumption in InvenTree and KiCad '''
    category = category.lower()
    name = name.lower()

    # Parameter specific filters
    # Package
    if 'package' in name and 'size' not in name:
        space_split = value.split()

        # Return value before the space
        if len(space_split) > 1:
            value = space_split[0].replace(',', '')

    # Sizes
    if 'size' in name or \
            'height' in name or \
            'pitch' in name or \
            'outline' in name:
        # imperial = re.findall('[.0-9]*"', value)
        metric = re.findall('[.0-9]*mm', value)
        len_metric = len(metric)

        # Return only the metric dimensions
        if len_metric > 0 and len_metric <= 1:
            # One dimension
            if 'dia' in value.lower():
                # Check if diameter value
                value = '⌀' + metric[0]
            else:
                value = metric[0]
        elif len_metric > 1 and len_metric <= 2:
            # Two dimensions
            value = metric[0].replace('mm', '') + 'x' + metric[1]
        elif len_metric > 2 and len_metric <= 3:
            # Three dimensions
            value = metric[0].replace('mm', '') + 'x' + metric[1].replace('mm', '') + 'x' + metric[2]

    # Power
    if 'power' in name:
        # decimal = re.findall('[0-9]\.[0-9]*W', value)
        ratio = re.findall('[0-9]/[0-9]*W', value)

        # Return ratio
        if len(ratio) > 0:
            value = ratio[0]

    # ESR, DCR, RDS
    if 'esr' in name or \
            'dcr' in name or \
            'rds' in name:
        value = value.replace('Max', '').replace(' ', '').replace('Ohm', 'R')

    # Category specific filters
    # RESISTORS
    if 'resistor' in category:
        if 'resistance' in name:
            space_split = value.split()

            if len(space_split) > 1:
                resistance = space_split[0]
                unit = space_split[1]

                unit_filter = ['kOhms', 'MOhms', 'GOhms']
                if unit in unit_filter:
                    unit = unit.replace('Ohms', '').upper()
                else:
                    unit = unit.replace('Ohms', 'R')

                value = resistance + unit

    # General filters
    # Clean-up ranges
    separator = '~'
    if separator in value:
        space_split = value.split()
        first_value = space_split[0]
        if len(space_split) > 2:
            second_value = space_split[2]

            # Substract digits, negative sign, points from first value to get unit
            unit = first_value.replace(re.findall('[-.0-9]*', first_value)[0], '')

            if unit:
                value = first_value.replace(unit, '') + separator + second_value

    # Remove parenthesis section
    if '(' in value:
        parenthesis = re.findall('\(.*\)', value)

        if parenthesis:
            for item in parenthesis:
                value = value.replace(item, '')

            # Remove leftover spaces
            value = value.replace(' ', '')

    # Remove spaces (for specific cases)
    if '@' in value:
        value = value.replace(' ', '')

    # Escape double-quote (else causes library error in KiCad)
    if '"' in value:
        value = value.replace('"', '\\"')

    # cprint(value)
    return value
