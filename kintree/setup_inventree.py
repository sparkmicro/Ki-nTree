import sys

from .config import settings
from .common.tools import cprint
from .config import config_interface
from .database import inventree_api, inventree_interface


def setup_inventree():
    SETUP_CATEGORIES = True
    SETUP_PARAMETERS = True

    def create_categories(parent, name, categories):
        category_pk, is_category_new = inventree_api.create_category(parent=parent, name=name)
        if is_category_new:
            cprint(f'[TREE]\tSuccess: Category "{name}" was added to InvenTree')
        else:
            cprint(f'[TREE]\tWarning: Category "{name}" already exists')

        if categories[name]:
            for cat in categories[name]:
                create_categories(parent=name, name=cat, categories=categories[name])

    if SETUP_CATEGORIES or SETUP_PARAMETERS:
        cprint('\n[MAIN]\tStarting InvenTree setup', silent=settings.SILENT)
        # Load category configuration file
        categories = config_interface.load_file(settings.CONFIG_CATEGORIES)['CATEGORIES']

        cprint('[MAIN]\tConnecting to Inventree', silent=settings.SILENT)
        inventree_connect = inventree_interface.connect_to_server()

        if not inventree_connect:
            sys.exit(-1)

        # Setup database for test
        inventree_api.set_inventree_db_test_mode()

    if SETUP_CATEGORIES:
        for category in categories.keys():
            cprint(f'\n[MAIN]\tCreating categories in {category.upper()}')
            create_categories(parent=None, name=category, categories=categories)

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
