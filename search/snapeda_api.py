import json
from urllib.request import Request, urlopen

import config.settings as settings
from common.tools import cprint, download_image
# Timeout
from wrapt_timeout_decorator import timeout

API_BASE_URL = f'https://snapeda-eeintech.herokuapp.com/snapeda?q='
SNAPEDA_URL = 'https://www.snapeda.com'

@timeout(dec_timeout=20)
def fetch_snapeda_part_info(part_number: str) -> dict:
	''' Fetch SnapEDA part data from API '''

	data = {}
	api_url = API_BASE_URL + part_number
	request = Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})

	with urlopen(request) as response:
		data = json.load(response)

	return data

def test_snapeda_api_connect() -> bool:
	''' Test method for SnapEDA API '''

	test_part = fetch_snapeda_part_info('SN74LV4T125PWR')
	if test_part:
		return True

	return False

def parse_snapeda_response(response: dict) -> dict:
	''' Return only relevant information from SnapEDA API response '''

	data = {}

	# data = {
	# 	'part_number': None,
	# 	'has_symbol': False,
	# 	'has_footprint': False,
	# 	'symbol_image': None,
	# 	'footprint_image': None,
	# 	'package': None,
	# 	'part_url': 'https://www.snapeda.com',
	# }

	number_results = int(response.get('hits', 0))

	# Check for single result
	if number_results != 1:
		pass
	else:
		try:
			data['part_number'] = response['results'][0].get('part_number', None)
			data['has_symbol'] = response['results'][0].get('has_symbol', False)
			data['has_footprint'] = response['results'][0].get('has_footprint', False)
			data['symbol_image'] = response['results'][0]['models'][0]['symbol_medium'].get('url', None)
			data['footprint_image'] = response['results'][0]['models'][0]['package_medium'].get('url', None)
			data['package'] = response['results'][0]['package'].get('name', None)
			data['part_url'] = SNAPEDA_URL + response['results'][0]['_links']['self'].get('href', '')
		except KeyError:
			pass

	return data

def download_snapeda_images(snapeda_data: dict) -> dict:
	''' Download symbol and footprint images from SnapEDA's server '''

	images = {
		'symbol': None,
		'footprint': None,
	}

	# Form path
	image_name = f'{snapeda_data["part_number"].lower()}_symbol.png'
	image_location = settings.search_images + image_name

	# Download symbol image
	symbol = download_image(snapeda_data['symbol_image'], image_location)
	if symbol:
		images['symbol'] = image_location

	# Form path
	image_name = f'{snapeda_data["part_number"].lower()}_footprint.png'
	image_location = settings.search_images + image_name

	# Download symbol image
	footprint = download_image(snapeda_data['footprint_image'], image_location)
	if footprint:
		images['footprint'] = image_location

	return images
