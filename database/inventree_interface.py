import copy
import os

import config.settings as settings
from common import part_tools
from common.tools import cprint
from config import config_interface
from database import inventree_api
from fuzzywuzzy import fuzz
from search import digikey_api


def connect_to_server() -> bool:
	''' Connect to InvenTree server using user settings '''
	connect = False
	settings.load_inventree_settings()

	connect = inventree_api.connect(	server=settings.SERVER_ADDRESS,
										username=settings.USERNAME,
										password=settings.PASSWORD )

	if not connect:
		if not settings.SERVER_ADDRESS:
			cprint(f'[TREE]\tError connecting to InvenTree server: missing server address')
			return connect
		if not settings.USERNAME:
			cprint(f'[TREE]\tError connecting to InvenTree server: missing username')
			return connect
		if not settings.PASSWORD:
			cprint(f'[TREE]\tError connecting to InvenTree server: missing password')
			return connect
		cprint(f'[TREE]\tError connecting to InvenTree server: invalid address, username or password')
	else:
		cprint(f'[TREE]\tSuccessfully connected to InvenTree server', silent=settings.SILENT)

	return connect

def build_part_keywords(inventree_part: dict) -> str:
	''' Build part keywords to be used in InvenTree and KiCad '''
	return inventree_part['description']

def get_categories(part_info: dict, supplier_only=False) -> list:
	''' Find categories from part supplier data, use "somewhat automatic" matching '''
	categories = [None, None]
	supplier_category = str(part_info['category'])
	supplier_subcategory = str(part_info['subcategory'])

	# Return supplier category, if match not needed
	if supplier_only:
		categories[0] = supplier_category
		categories[1] = supplier_subcategory
		return categories

	function_filter = False
	# TODO: Make 'filter_parameter' user defined?
	filter_parameter = 'Function Type'

	### Check existing matches
	# Load inversed category map
	category_map = config_interface.load_supplier_categories_inversed(supplier_config_path=settings.CONFIG_DIGIKEY_CATEGORIES)

	try:
		for inventree_category in category_map.keys():
			for key, inventree_subcategory in category_map[inventree_category].items():
				if supplier_subcategory == key:
					categories[0] = inventree_category
					# Check if filtering by function
					if inventree_subcategory.startswith('__'):
						function_filter = True

					# Save subcategory if not function filtered
					if not function_filter:
						categories[1] = inventree_subcategory
					
					break
	except:
		pass

	### Function Filter
	if not categories[1] and function_filter:
		cprint(f'[INFO]\tSubcategory is filtered using "{filter_parameter}" parameter', silent=settings.SILENT, end='')
		# Load parameter map
		parameter_map = config_interface.load_category_parameters(categories[0], settings.CONFIG_DIGIKEY_PARAMETERS)
		# Build compare list
		compare = []
		for supplier_parameter, inventree_parameter in parameter_map.items():
			if (supplier_parameter in part_info['parameters'].keys() and \
			inventree_parameter == filter_parameter):
				compare.append(part_info['parameters'][supplier_parameter])

		# Load subcategory map
		category_map = config_interface.load_supplier_categories(supplier_config_path=settings.CONFIG_DIGIKEY_CATEGORIES)[categories[0]]
		for inventree_subcategory in category_map.keys():
			for item in compare:
				fuzzy_match = fuzz.partial_ratio(inventree_subcategory, item)
				display_result = f'"{inventree_subcategory}" ?= "{item}"'.ljust(50)
				cprint(f'{display_result} => {fuzzy_match}', silent=settings.HIDE_DEBUG)
				if fuzzy_match >= settings.CATEGORY_MATCH_RATIO_LIMIT:
					categories[1] = inventree_subcategory.replace('__','')
					break

			if categories[1]:
				cprint(f'\t[ PASS ]', silent=settings.SILENT)
				break

	if not categories[1] and function_filter:
		cprint(f'\t[ FAILED ]', silent=settings.SILENT)

	### Automatic Match
	if not (categories[0] and categories[1]):
		# Load category map
		category_map = config_interface.load_supplier_categories(supplier_config_path=settings.CONFIG_DIGIKEY_CATEGORIES)

		def find_supplier_category_match(supplier_category: str):
			# Check for match with Inventree categories
			category_match = None
			subcategory_match = None

			# try:
			for inventree_category in category_map.keys():
				fuzzy_match = fuzz.partial_ratio(supplier_category, inventree_category)
				display_result = f'"{supplier_category}" ?= "{inventree_category}"'.ljust(50)
				cprint(f'{display_result} => {fuzzy_match}', silent=settings.HIDE_DEBUG)
				
				if 	fuzzy_match < settings.CATEGORY_MATCH_RATIO_LIMIT and \
					category_map[inventree_category]:
					# Compare to subcategories
					for inventree_subcategory in category_map[inventree_category]:
						fuzzy_match = fuzz.partial_ratio(supplier_category, inventree_subcategory)
						display_result = f'"{supplier_category}" ?= "{inventree_subcategory}"'.ljust(50)
						cprint(f'{display_result} => {fuzzy_match}', silent=settings.HIDE_DEBUG)

						if fuzzy_match >= settings.CATEGORY_MATCH_RATIO_LIMIT:
							subcategory_match = inventree_subcategory
							break

				if fuzzy_match >= settings.CATEGORY_MATCH_RATIO_LIMIT:
					category_match = inventree_category
					break

			# except:
			# 	pass

			return category_match, subcategory_match

		# Find category and subcategories match
		category, subcategory = find_supplier_category_match(supplier_category)
		if category:
			categories[0] = category
		if subcategory:
			categories[1] = subcategory

		# Run match with supplier subcategory
		if not categories[0] or not categories[1]:
			category, subcategory = find_supplier_category_match(supplier_subcategory)

		if category and not categories[0]:
			categories[0] = category
		if subcategory and not categories[1]:
			categories[1] = subcategory

	# Final checks
	if not categories[0]:
		cprint(f'[INFO]\tWarning: "{part_info["category"]}" did not match any supplier category ', silent=settings.SILENT)
	else:
		cprint(f'[TREE]\tCategory: "{categories[0]}"', silent=settings.SILENT)
	if not categories[1]:
		cprint(f'[INFO]\tWarning: "{part_info["subcategory"]}" did not match any supplier subcategory ', silent=settings.SILENT)
	else:
		cprint(f'[TREE]\tSubcategory: "{categories[1]}"', silent=settings.SILENT)
	
	return categories

def translate_digikey_to_inventree(part_info: dict, categories: list) -> dict:
	''' Using supplier part data and categories, fill-in InvenTree part dictionary '''
	# Copy template
	inventree_part = copy.deepcopy(settings.inventree_part_template)
	# Insert data
	inventree_part["category"][0] = categories[0]
	inventree_part["category"][1] = categories[1]
	inventree_part['name'] = part_info['product_description']
	inventree_part['description'] = part_info['product_description']
	# Keywords (need to be after description)
	inventree_part['keywords'] = build_part_keywords(inventree_part)
	inventree_part['image'] = part_info['primary_photo']
	inventree_part['supplier'] = {'Digi-Key': [part_info['digi_key_part_number']],}
	inventree_part['manufacturer'] = {part_info['manufacturer']: [part_info['manufacturer_part_number']],}
	# Replace whitespaces in URL
	inventree_part['datasheet'] = part_info['primary_datasheet'].replace(' ','%20')

	# Load parameters map
	parameter_map = config_interface.load_category_parameters(	category=inventree_part["category"][0],
																		supplier_config_path=settings.CONFIG_DIGIKEY_PARAMETERS, )
	# Add Parameters	
	if parameter_map:
		for supplier_param, inventree_param in parameter_map.items():
			# Some parameters may not be mapped
			if inventree_param not in inventree_part['parameters'].keys():
				if supplier_param != 'Manufacturer Part Number':
					try:
						parameter_value = part_tools.clean_parameter_value(	category=categories[0],
																			name=supplier_param,
																			value=part_info['parameters'][supplier_param] )
						inventree_part['parameters'][inventree_param] = parameter_value
					except:
						cprint(f'[INFO]\tWarning: Parameter "{supplier_param}" not found in supplier data', silent=settings.SILENT)
				else:
					inventree_part['parameters'][inventree_param] = part_info['manufacturer_part_number']
		
		# Check for missing parameters and fill value with dash
		for inventree_param in parameter_map.values():
			if inventree_param not in inventree_part['parameters'].keys():
				inventree_part['parameters'][inventree_param] = '-'
	else:
		cprint(f'[INFO]\tWarning: Parameter map for "{categories[0]}" does not exist or is empty', silent=settings.SILENT)

	return inventree_part

def digikey_search(part_number: str) -> dict:
	''' Wrapper for Digi-Key search, allow use of cached data (limited daily API calls) '''
	part_info = {}
	# Check part number exist
	if not part_number:
		cprint(f'\n[MAIN]\tError: Missing Part Number', silent=settings.SILENT)
		return part_info

	# Load from file if cache is enabled
	search_filename = settings.search_results['directory'] + part_number + settings.search_results['extension']
	if settings.CACHE_ENABLED:
		# TODO: Cache should be automatically disabled if data is too old
		try:
			part_info = digikey_api.load_from_file(search_filename)
			if part_info:
				cprint(f'\n[MAIN]\tUsing Digi-Key cached data for {part_number}', silent=settings.SILENT)
		except:
			pass

	if not part_info:
		cprint(f'\n[MAIN]\tDigi-Key search for {part_number}', silent=settings.SILENT)
		part_info = digikey_api.fetch_digikey_part_info(part_number)

	# Check Digi-Key data exist
	if not part_info:
		cprint(f'[INFO]\tError: Failed to fetch data for "{part_number}"', silent=settings.SILENT)
	
	# Save search results
	if part_info and settings.CACHE_ENABLED:
		# Check if search/results directory needs to be created
		if not os.path.exists(os.path.dirname(search_filename)):
			os.mkdir(os.path.dirname(search_filename))
		digikey_api.save_to_file(part_info, search_filename)

	return part_info

def inventree_create(part_info: dict, categories: list, symbol=None, footprint=None):
	''' Create InvenTree part from supplier part data and categories '''
	# TODO: Make 'supplier' a variable for use with other APIs (eg. Octopart)
	supplier = 'Digi-Key'
	part_pk = 0
	new_part = False

	# Translate to InvenTree part format
	if supplier == 'Digi-Key':
		inventree_part = translate_digikey_to_inventree(part_info, categories)

	if not inventree_part:
		cprint(f'\n[MAIN]\tError: Failed to process {supplier} data', silent=settings.SILENT)

	# Fetch category info from InvenTree part
	category_name = inventree_part['category'][0]
	subcategory_name = inventree_part['category'][1]
	category_pk = inventree_api.get_inventree_category_id(category_name)
	
	if subcategory_name:
		# Fetch subcategory id
		subcategory_pk = inventree_api.get_inventree_category_id(	category_name=subcategory_name,
																	parent_category_id=category_pk )
		if subcategory_pk > 0:
			# Check if part already exists
			part_pk = inventree_api.is_new_part_specs(subcategory_pk, inventree_part)

			### Part exists
			if part_pk > 0:
				cprint(f'[INFO]\tPart already exists, skipping.', silent=settings.SILENT)
				ipn = inventree_api.get_part_number(part_pk)
				# Update InvenTree part number
				inventree_part['IPN'] = ipn
				# Update InvenTree URL
				inventree_part['inventree_url'] = settings.PART_URL_ROOT + str(part_pk) + '/'
			### Part is new
			else:
				new_part = True
				# Create a new Part
				# Use the pk (primary-key) of the category
				part_pk = inventree_api.create_part(description=inventree_part['description'],
													category_id=subcategory_pk,
													image=inventree_part['image'],
													keywords=inventree_part['keywords'])

				# Generate Internal Part Number
				cprint(f'\n[MAIN]\tGenerating Internal Part Number', silent=settings.SILENT)
				ipn = part_tools.generate_part_number(category_name, part_pk)
				cprint(f'[INFO]\tInternal Part Number = {ipn}', silent=settings.SILENT)
				# Update InvenTree part number
				ipn_update = inventree_api.set_part_number(part_pk, ipn)
				if not ipn_update:
					cprint(f'\n[INFO]\tError updating IPN', silent=settings.SILENT)
				inventree_part['IPN'] = ipn
				# Update InvenTree part revision
				inventree_part['revision'] = 'A'
				# Update InvenTree URL
				inventree_part['inventree_url'] = settings.PART_URL_ROOT + str(part_pk) + '/'
		else:
			cprint(f'\n[TREE]\tError: Subcategory "{subcategory_name}" does not exist', silent=settings.SILENT)
	
	if part_pk > 0:
		if new_part:
			cprint('[INFO]\tSuccess: Added new part to InvenTree', silent=settings.SILENT)
			# Add image
			image_result = inventree_api.upload_part_image(inventree_part['image'], part_pk)
			if not image_result:
				cprint(f'[TREE]\tWarning: Failed to upload part image', silent=settings.SILENT)

		# Create mandatory parameters (symbol & footprint)
		if symbol:
			kicad_symbol = symbol + ':' + ipn # symbol.split('.')[0] + ':' + ipn
		else:
			try:
				kicad_symbol = settings.symbol_libraries_paths[category_name].split(os.sep)[-1].split('.')[0] + ':' + ipn
			except:
				kicad_symbol = category_name.replace(' ','_') + ':TBD'
		if footprint:
			kicad_footprint = footprint
		else:
			try:
				supplier_package = inventree_part['parameters']['Package Type']
				kicad_footprint = settings.footprint_lookup_table[category_name][supplier_package]
			except:
				kicad_footprint = category_name.replace(' ','_') + ':TBD'

		# Add symbol & footprint to InvenTree part
		inventree_part['parameters']['Symbol'] = kicad_symbol
		inventree_part['parameters']['Footprint'] = kicad_footprint

		# Create parameters
		if len(inventree_part['parameters']) > 0:
			cprint('\n[MAIN]\tCreating parameters', silent=settings.SILENT)
			parameters_lists = [
				[], # Store new parameters
				[], # Store existings paremeters
			]
			for name, value in inventree_part['parameters'].items():
					parameter, is_new_parameter = inventree_api.create_parameter(part_id=part_pk, template_name=name, value=value)

					if is_new_parameter:
						parameters_lists[0].append(name)
					else:
						parameters_lists[1].append(name)

			if parameters_lists[0]:
				cprint(f'[INFO]\tSuccess: The following parameters were created:', silent=settings.SILENT)
				for item in parameters_lists[0]:
					cprint(f'--->\t{item}', silent=settings.SILENT)
			if parameters_lists[1]:
				cprint(f'[TREE]\tWarning: The following parameters were skipped:', silent=settings.SILENT)
				for item in parameters_lists[1]:
					cprint(f'--->\t{item}', silent=settings.SILENT)

		# Create company part
		cprint('\n[MAIN]\tCreating supplier part', silent=settings.SILENT)
		is_new_supplier_part = inventree_api.is_new_supplier_part(	supplier_name=supplier, 
																	supplier_sku=inventree_part['supplier'][supplier][0] )

		if not is_new_supplier_part:
			cprint(f'[INFO]\tSupplier part already exists, skipping.', silent=settings.SILENT)
		else:
			# Extract manufacturer name and number
			for key, values in inventree_part['manufacturer'].items():
				manufacturer_name = key
				manufacturer_number = values[0]
			# Create a new supplier part
			is_supplier_part_created = inventree_api.create_supplier_part(	part_id=part_pk,
																			supplier_name=supplier,
																			supplier_sku=inventree_part['supplier'][supplier],
																			description=inventree_part['description'],
																			manufacturer_name=manufacturer_name,
																			manufacturer_pn=manufacturer_number,
																			datasheet=inventree_part['datasheet'] )
			
			if is_supplier_part_created:
				cprint('[INFO]\tSuccess: Added new supplier part', silent=settings.SILENT)

	return new_part, part_pk, inventree_part
