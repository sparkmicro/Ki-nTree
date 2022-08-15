import re

from ..config import settings
from ..config import config_interface
from .tools import cprint


def generate_part_number(category: str, part_pk: int) -> str:
    ''' Generate Internal Part Number (IPN) '''
    try:
        ipn = str(part_pk).zfill(settings.IPN_UNIQUE_ID_LENGTH)
    except:
        return None

    if settings.IPN_USE_FIXED_PREFIX:
        prefix_id = settings.IPN_PREFIX
    else:
        CATEGORY_CODES = config_interface.load_file(settings.CONFIG_CATEGORIES)['CODES']

        for key in CATEGORY_CODES.keys():
            if key in category:
                break
        try:
            prefix_id = CATEGORY_CODES[key]
        except:
            return None

    if prefix_id:
        ipn = '-'.join([prefix_id, ipn])

    if settings.IPN_USE_VARIANT_SUFFIX:
        ipn = '-'.join([ipn, settings.IPN_VARIANT_SUFFIX])

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
        split_space = value.split()
        first_value = split_space[0]
        second_value = split_space[2]

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
