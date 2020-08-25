import config.settings as settings
from common.tools import cprint
from config import config_interface
from database import inventree_api, inventree_interface

if __name__ == '__main__':
	# Load category configuration file
	categories = config_interface.load_file(settings.CONFIG_CATEGORIES)['CATEGORIES']
	# cprint(categories)

	cprint('[MAIN]\tConnecting to Inventree server', silent=settings.SILENT)
	inventree_connect = inventree_interface.connect_to_server()
	
	if not inventree_connect:
		exit(0)

	for category in categories.keys():
		cprint(f'\n[MAIN]\tCreating {category.upper()}')
		category_pk, is_category_new = inventree_api.create_category(parent=None, name=category)
		if is_category_new:
			cprint(f'[TREE]\tSuccess: Category "{category}" was added to InvenTree', flush=True)
		else:
			cprint(f'[TREE]\tWarning: Category "{category}" already exists', flush=True)

		if categories[category]:
			cprint(f'[MAIN]\tCreating Subcategories')
			for subcategory in categories[category]:
				sub_category_pk, is_subcategory_new = inventree_api.create_category(parent=category, name=subcategory)

				if is_subcategory_new:
					cprint(f'[TREE]\tSuccess: Subcategory "{category}/{subcategory}" was added to InvenTree', flush=True)
				else:
					cprint(f'[TREE]\tWarning: Subcategory "{category}/{subcategory}" already exists', flush=True)

	# Load parameter configuration file
	parameters = config_interface.load_file(settings.CONFIG_PARAMETERS)
	# cprint(parameters)
	cprint(f'\n[MAIN]\tLoading Parameters')
	for name, unit in parameters.items():
		pk = inventree_api.create_parameter_template(name, unit)
		if pk > 0:
			cprint(f'[TREE]\tSuccess: Parameter "{name}" was added to InvenTree', flush=True)
		else:
			cprint(f'[TREE]\tWarning: Parameter "{name}" already exists', flush=True)
