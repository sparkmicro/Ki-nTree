from ..config import settings
from ..common.tools import download, download_image

API_BASE_URL = 'https://snapeda.eeinte.ch/?'
SNAPEDA_URL = 'https://www.snapeda.com'


def fetch_snapeda_part_info(part_number: str) -> dict:
    ''' Fetch SnapEDA part data from API '''

    api_url = API_BASE_URL + part_number.replace(' ', '%20')
    data = download(api_url, timeout=10)
    return data if data else {}


def parse_snapeda_response(response: dict) -> dict:
    ''' Return only relevant information from SnapEDA API response '''

    data = {
        'part_number': None,
        'has_symbol': False,
        'has_footprint': False,
        'symbol_image': None,
        'footprint_image': None,
        'package': None,
        'part_url': None,
        'has_single_result': False,
    }

    number_results = int(response.get('hits', 0))

    # Check for single result
    if number_results == 1:
        try:
            data['part_number'] = response['results'][0].get('part_number', None)
            data['has_symbol'] = response['results'][0].get('has_symbol', False)
            data['has_footprint'] = response['results'][0].get('has_footprint', False)
            data['package'] = response['results'][0]['package'].get('name', None)
            data['part_url'] = SNAPEDA_URL + response['results'][0]['_links']['self'].get('href', '')
            data['part_url'] += '?ref=kintree'
            data['has_single_result'] = True
        except KeyError:
            pass

        # Separate as the 'models' key does not always exist
        try:
            data['symbol_image'] = response['results'][0]['models'][0]['symbol_medium'].get('url', None)
        except KeyError:
            pass
        try:
            data['footprint_image'] = response['results'][0]['models'][0]['package_medium'].get('url', None)
        except KeyError:
            pass
    elif number_results > 1:
        try:
            data['part_url'] = SNAPEDA_URL + '/search/' + response['pages'][0].get('link', None).split('&')[0] + '&ref=kintree'
        except:
            pass
    else:
        pass

    return data


def download_snapeda_images(snapeda_data: dict) -> dict:
    ''' Download symbol and footprint images from SnapEDA's server '''

    images = {
        'symbol': None,
        'footprint': None,
    }

    try:
        part_number = snapeda_data["part_number"].replace('/', '').lower()
    except:
        part_number = None

    if part_number:
        try:
            if snapeda_data['symbol_image']:
                # Form path
                image_name = f'{part_number}_symbol.png'
                image_location = settings.search_images + image_name

                # Download symbol image
                symbol = download_image(snapeda_data['symbol_image'], image_location)
                if symbol:
                    images['symbol'] = image_location
        except KeyError:
            pass

        try:
            if snapeda_data['footprint_image']:
                # Form path
                image_name = f'{part_number}_footprint.png'
                image_location = settings.search_images + image_name

                # Download symbol image
                footprint = download_image(snapeda_data['footprint_image'], image_location)
                if footprint:
                    images['footprint'] = image_location
        except KeyError:
            pass

    return images


def test_snapeda_api() -> bool:
    ''' Test method for SnapEDA API '''

    result = False

    # Test single result
    response = fetch_snapeda_part_info('SN74LV4T125PWR')
    data = parse_snapeda_response(response)
    images = download_snapeda_images(data)

    if data['part_number'] and data['has_symbol'] and images['symbol']:
        result = True

    # Test multiple results
    if result:
        response = fetch_snapeda_part_info('1N4148W-7-F')
        data = parse_snapeda_response(response)
        if data['has_single_result']:
            result = False

    return result
