import os
import time

from ..config import settings, config_interface


def load_from_file(search_file, test_mode=False) -> dict:
    ''' Fetch part data from file '''
    cache_valid = settings.CACHE_VALID_DAYS * 24 * 3600

    # Load data from file if cache enabled
    if settings.CACHE_ENABLED:
        try:
            part_data = config_interface.load_file(search_file)
        except FileNotFoundError:
            return None

        # Check cache validity
        try:
            # Get timestamp
            timestamp = int(time.time() - part_data['search_timestamp'])
        except (KeyError, TypeError):
            timestamp = int(time.time())

        if timestamp < cache_valid or test_mode:
            return part_data

    return None


def save_to_file(part_info, search_file):
    ''' Save part data to file '''

    # Check if search/results directory needs to be created
    if not os.path.exists(os.path.dirname(search_file)):
        os.mkdir(os.path.dirname(search_file))

    # Add timestamp
    part_info['search_timestamp'] = int(time.time())

    # Save data if cache enabled
    if settings.CACHE_ENABLED:
        config_interface.dump_file(part_info, search_file)
