import sys

from .config import settings
from .common.tools import cprint
from .config import config_interface
from .database import inventree_api, inventree_interface


def setup_inventree():
    SETUP_CATEGORIES = True
    SETUP_PARAMETERS = True

    if SETUP_CATEGORIES or SETUP_PARAMETERS:
        cprint('\n[MAIN]\tStarting InvenTree setup', silent=settings.SILENT)
        # Load category configuration file
        categories = config_interface.load_file(settings.CONFIG_CATEGORIES)['CATEGORIES']
        # cprint(categories)

        cprint('[MAIN]\tConnecting to Inventree', silent=settings.SILENT)
        inventree_connect = inventree_interface.connect_to_server()

        if not inventree_connect:
            sys.exit(-1)

    if SETUP_CATEGORIES:
        for category in categories.keys():
            cprint(f'\n[MAIN]\tCreating {category.upper()}')
            category_pk, is_category_new = inventree_api.create_category(parent=None, name=category)
            if is_category_new:
                cprint(f'[TREE]\tSuccess: Category "{category}" was added to InvenTree')
            else:
                cprint(f'[TREE]\tWarning: Category "{category}" already exists')

            if categories[category]:
                cprint('[MAIN]\tCreating Subcategories')
                for subcategory in categories[category]:
                    sub_category_pk, is_subcategory_new = inventree_api.create_category(parent=category, name=subcategory)

                    if is_subcategory_new:
                        cprint(f'[TREE]\tSuccess: Subcategory "{category}/{subcategory}" was added to InvenTree')
                    else:
                        cprint(f'[TREE]\tWarning: Subcategory "{category}/{subcategory}" already exists')

    if SETUP_PARAMETERS:
        # Load parameter configuration file
        parameters = config_interface.load_file(settings.CONFIG_PARAMETERS)
        # cprint(parameters)
        cprint('\n[MAIN]\tLoading Parameters')
        for name, unit in parameters.items():
            pk = inventree_api.create_parameter_template(name, unit)
            if pk > 0:
                cprint(f'[TREE]\tSuccess: Parameter "{name}" was added to InvenTree')
            else:
                cprint(f'[TREE]\tWarning: Parameter "{name}" already exists')


if __name__ == '__main__':
    setup_inventree()
