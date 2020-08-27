import logging
import os
import pickle

import config.settings as settings
import digikey
from config import config_interface

os.environ['DIGIKEY_STORAGE_PATH'] = settings.DIGIKEY_STORAGE_PATH

def disable_digikey_api_logger():
	# Digi-Key API logger
	logging.getLogger('digikey.v3.api').setLevel(logging.WARNING)
	# Disable DEBUG
	logging.disable(logging.DEBUG)

def check_environment() -> bool:
	DIGIKEY_CLIENT_ID = os.environ.get('DIGIKEY_CLIENT_ID', None)
	DIGIKEY_CLIENT_SECRET = os.environ.get('DIGIKEY_CLIENT_SECRET', None)

	if not DIGIKEY_CLIENT_ID or not DIGIKEY_CLIENT_SECRET:
		return False

	return True

def setup_environment() -> bool:
	if not check_environment():
		# SETUP the Digikey authentication see https://developer.digikey.com/documentation/organization#production
		digikey_api_settings = config_interface.load_file(settings.CONFIG_DIGIKEY_API)
		os.environ['DIGIKEY_CLIENT_ID'] = digikey_api_settings['DIGIKEY_CLIENT_ID']
		os.environ['DIGIKEY_CLIENT_SECRET'] = digikey_api_settings['DIGIKEY_CLIENT_SECRET']

	return check_environment()

def find_categories(part_details: str):
	''' Find Digi-Key categories '''
	try:
		# print(part_details['limited_taxonomy']['children'][0]['value'])
		return part_details['limited_taxonomy']['children'][0]['value'], part_details['limited_taxonomy']['children'][0]['children'][0]['value']
	except:
		return None, None

def fetch_digikey_part_info(part_number: str) -> dict:
	''' Fetch Digi-Key part data from API '''
	part_info = {}
	if not setup_environment():
		return part_info

	# Query part number
	try:
		part = digikey.product_details(part_number).to_dict()
	except:
		return part_info
	# print(json.dumps(part, indent = 4, sort_keys = True))
	
	category, subcategory = find_categories(part)
	try:
		part_info['category'] = category
		part_info['subcategory'] = subcategory
	except:
		part_info['category'] = ''
		part_info['subcategory'] = ''

	header = ['product_description', 'digi_key_part_number', 'manufacturer', 'manufacturer_part_number', 'primary_datasheet', 'primary_photo']
	
	for key in part:
		if key in header:
			if key == 'manufacturer':
				part_info[key] = part['manufacturer']['value']
			else:
				part_info[key] = part[key]

	# Parameters
	part_info['parameters'] = {}
	for parameter in range(len(part['parameters'])):
		parameter_name = part['parameters'][parameter]['parameter']
		parameter_value = part['parameters'][parameter]['value']
		# Append to parameters dictionary
		part_info['parameters'][parameter_name] = parameter_value
	# print(part_info['parameters'])

	return part_info

def test_digikey_api_connect() -> bool:
	setup_environment()

	test_part = fetch_digikey_part_info('RMCF0402JT10K0')
	if test_part:
		return True

	return False
	
def load_from_file(search_file) -> dict:
	''' Fetch Digi-Key part data from file '''
	try:
		file = open(search_file, 'rb')
		part_info = pickle.load(file)
		file.close()
		return part_info
	except:
		return None

def save_to_file(part_info, search_file):
	try:
		''' Save Digi-Key part data to file '''
		file = open(search_file, 'wb')
		pickle.dump(part_info, file)
		file.close()
	except:
		raise Exception('Error saving Digi-key search data')
