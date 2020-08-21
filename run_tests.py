import os

import config.settings as settings
from common.tools import cprint, create_library
from config import config_interface
from database import inventree_api, inventree_interface
from kicad import kicad_interface
from search.digikey_api import disable_digikey_api_logger

# SETTINGS
# Enable InvenTree tests
ENABLE_INVENTREE = False
# Enable KiCad tests
ENABLE_KICAD = True
# Enable test samples deletion
ENABLE_DELETE = True
# Set categories to test
PART_CATEGORIES = [
	'Capacitors',
	'Circuit Protections',
	'Connectors',
	'Crystals and Oscillators',
	'Diodes',
	'Inductors',
	'Integrated Circuits',
	'Mechanicals',
	'Power Management',
	'Resistors',
	'RF',
	'Transistors',
]
###

# Enable test mode
settings.enable_test_mode()
# Create user configuration files
settings.create_user_config_files()
# Set path to test symbol library
test_library_path = os.path.join(
	settings.PROJECT_DIR, 'tests', 'TEST.lib')
# Disable API logging
disable_digikey_api_logger()

# Check result
def check_result(status: str, new_part: bool) -> bool:
	# Build result
	success = False
	if (status == 'original') or (status == 'fake_alternate'):
		if new_part:
			success = True
	elif status == 'alternate_mpn':
		if not new_part:
			success = True
	else:
		pass

	return success

# Load test samples
samples = config_interface.load_file(os.path.abspath(
	os.path.join('tests', 'test_samples.yaml')))
PART_TEST_SAMPLES = {}
for category in PART_CATEGORIES:
	PART_TEST_SAMPLES.update({category: samples[category]})

# Store results
kicad_results = {}
inventree_results = {}

if __name__ == '__main__':
	if settings.ENABLE_TEST:
		for category in PART_TEST_SAMPLES.keys():
			cprint(f'\n[MAIN]\tTesting {category.upper()}')
			for number, status in PART_TEST_SAMPLES[category].items():
				# Fetch supplier data
				part_info = inventree_interface.digikey_search(number)

				if ENABLE_KICAD:
					test_message = f'[INFO]\tKiCad test for "{number}" ({status})'.ljust(65)
					cprint(test_message, end='')
					# Translate supplier data to inventree/kicad data
					part_data = inventree_interface.translate_digikey_to_inventree(part_info, [category, None])

					if part_data:
						part_data['IPN'] = number
						part_data['inventree_url'] = part_data['datasheet']

						if settings.AUTO_GENERATE_LIB:
							create_library(os.path.dirname(test_library_path), 'TEST', settings.symbol_template_lib)

						kicad_success, kicad_new_part = kicad_interface.inventree_to_kicad(part_data=part_data,
																					 	   library_path=test_library_path)
						
						# Get and print result
						if kicad_success:
							cprint(f'[ PASS ]')
							result = True
						else:
							cprint(f'[ FAIL ]')
							result = False

						# Log result
						if number not in kicad_results.keys():
							kicad_results.update({number: result})

				if ENABLE_INVENTREE:
					cprint('\n[MAIN]\tConnecting to Inventree server',
						   silent=settings.SILENT)
					inventree_connect = inventree_interface.connect_to_server()

					# InvenTree
					test_message = f'[INFO]\tInvenTree test for "{number}" ({status})'.ljust(65)
					cprint(test_message, end='')

					# Adding part information to InvenTree
					categories = [None, None]
					new_part = False
					part_pk = 0
					part_data = {}

					# Get categories
					if part_info:
						categories = inventree_interface.get_categories(part_info)

					# Create part in InvenTree
					if categories[0] and categories[1]:
						symbol = os.path.basename(test_library_path).split['.'][0]
						new_part, part_pk, part_data = inventree_interface.inventree_create(part_info=part_info,
																							categories=categories,
																							symbol=symbol)

					success = check_result(status, new_part)

					# Display
					if success:
						# Build results
						inventree_results.update({number: [part_pk, success]})
						cprint(f'[ PASS ]')
					else:
						cprint(f'[ FAIL ]')
						part_url = settings.PART_URL_ROOT + str(part_pk) + '/'
						cprint(f'[DBUG]\tnew_part = {new_part}')
						cprint(f'[DBUG]\tpart_pk = {part_pk}')
						cprint(f'[DBUG]\tpart_url = {part_url}')
						# cprint(f'[DBUG]\tpart_info =')
						# cprint(part_data)

		if ENABLE_KICAD:
			cprint(f'\nKiCad Results\n-----', silent=not(settings.ENABLE_TEST))
			cprint(kicad_results, silent=not(settings.ENABLE_TEST))
		if ENABLE_INVENTREE:
			cprint(f'\nInvenTree Results\n-----', silent=not(settings.ENABLE_TEST))
			cprint(inventree_results, silent=not(settings.ENABLE_TEST))

		if ENABLE_DELETE:
			if kicad_results or inventree_results:
				input('\nPress "Enter" to delete parts...')

				if ENABLE_KICAD:
					cprint(f'[MAIN]\tDeleting KiCad test parts')
					# Delete all KiCad test parts
					for number, result in kicad_results.items():
						try:
							kicad_interface.delete_part(part_number=number,
														category=None,
														library_path=test_library_path)
							cprint(f'[KCAD]\tSuccess: "{number}" was deleted')
						except:
							cprint(f'[KCAD]\tWarning: "{number}" could not be deleted')

				if ENABLE_INVENTREE:
					cprint(f'[MAIN]\tDeleting InvenTree test parts')
					# Delete all InvenTree test parts
					for number, result in inventree_results.items():
						cprint(f'[{number}]\tAPI Result:\t', end='', silent=not(ENABLE_DELETE))
						try:
							inventree_api.delete_part(part_id=result[0])
						except:
							pass
