import config.settings as settings
from common.tools import cprint
from config import config_interface
from database import inventree_api, inventree_interface
from kicad import kicad_interface
from search.digikey_api import disable_digikey_api_logger

### SETTINGS
# Enable test mode
settings.enable_test_mode()
# Create user configuration files
settings.create_user_config_files()
# Disable API logging
disable_digikey_api_logger()
# Enable KiCad tests
ENABLE_KICAD = True
# Enable test samples deletion
ENABLE_DELETE = True
# Set test symbol library name
TEST_LIBRARY = 'TEST_NEW'
# Set path to test symbol library
TEST_LIBRARY_PATH = settings.KICAD_SYMBOLS_PATH + TEST_LIBRARY + '.lib'
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

# Load test samples
samples = config_interface.load_file(os.abspath(os.path.join('tests','test_samples.yaml')))
PART_TEST_SAMPLES = {}
for category in PART_CATEGORIES:
	PART_TEST_SAMPLES.update({category:samples[category]})

# Store primary keys and part numbers to delete afterwards
pk_log = []
ipn_log = {}

if __name__ == '__main__':
	if settings.ENABLE_TEST:
		cprint('\n[MAIN]\tConnecting to Inventree server', silent=settings.SILENT)
		inventree_connect = inventree_interface.connect_to_server()

		for category in PART_TEST_SAMPLES.keys():
			cprint(f'\n[MAIN]\tTesting {category.upper()}')
			for number, status in PART_TEST_SAMPLES[category].items():
				# InvenTree
				test_message = f'[INFO]\tInvenTree test for "{number}" ({status})'.ljust(65)
				cprint(test_message, end='')

				# Adding part information to InvenTree
				categories = [None, None]
				new_part = False
				part_pk = 0
				part_data = {}
				
				# Fetch supplier data
				part_info = inventree_interface.digikey_search(number)

				# Get categories
				if part_info:
					categories = inventree_interface.get_categories(part_info)

				# Create part in InvenTree
				if categories[0] and categories[1]:
					new_part, part_pk, part_data = inventree_interface.inventree_create(part_info=part_info,
																						categories=categories,
																						symbol=TEST_LIBRARY )

				# Create pk list for deletion
				if part_pk > 0 and part_pk not in pk_log:
					pk_log.append(part_pk)

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

				# Display
				if success:
					cprint(f'[ PASS ]')
				else:
					cprint(f'[ FAIL ]')
					part_url = settings.PART_URL_ROOT + str(part_pk) + '/'
					cprint(f'[DBUG]\tnew_part = {new_part}')
					cprint(f'[DBUG]\tpart_pk = {part_pk}')
					cprint(f'[DBUG]\tpart_url = {part_url}')
					# cprint(f'[DBUG]\tpart_info =')
					# cprint(part_data)

				# KiCad
				if ENABLE_KICAD:
					if part_pk:
						ipn = part_data['IPN']
						kicad_success, kicad_new_part = kicad_interface.inventree_to_kicad(	part_data=part_data,
																							library_path=TEST_LIBRARY_PATH )
						if kicad_success and ipn not in ipn_log:
							ipn_log[ipn] = category

		cprint(f'\npk_log = {pk_log}', silent=not(settings.ENABLE_TEST))
		cprint(f'ipn_log = {ipn_log}', silent=not(settings.ENABLE_TEST))

		if ENABLE_DELETE:
			if pk_log or ipn_log:
				input('\nPress "Enter" to delete parts...')
				cprint(f'\n[MAIN]\tDeleting test parts:')

				# Delete all InvenTree test parts
				for pk in pk_log:
					cprint(f'[{pk}]\tAPI Result:\t', end='', silent=not(ENABLE_DELETE))
					try:
						inventree_api.delete_part(part_id=pk)
					except:
						pass

				if ENABLE_KICAD:
					# Delete all KiCad test parts
					for ipn, category in ipn_log.items():	
						try:
							kicad_interface.delete_part(part_number=ipn,
														category= None,
														library_path=TEST_LIBRARY_PATH )
						except:
							cprint(f'\n[KCAD]\tWarning: {ipn} could not be deleted')
