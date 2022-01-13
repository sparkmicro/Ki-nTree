from ..config import settings
import validators
from ..common import part_tools
from ..common.tools import cprint, download_image
from ..config import config_interface

# Required to use local CA certificates on Linux
# For more details, refer to https://github.com/sparkmicro/Ki-nTree/pull/45
import platform
if platform.system() == 'Linux':
    import os
    cert_path = '/etc/ssl/certs/ca-certificates.crt'
    if os.path.isfile(cert_path):
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path

# InvenTree
from inventree.api import InvenTreeAPI
from inventree.base import Parameter, ParameterTemplate
from inventree.company import Company, ManufacturerPart, SupplierPart
from inventree.part import Part, PartCategory


def connect(server: str, username: str, password: str, connect_timeout=5, silent=False) -> bool:
    ''' Connect to InvenTree server and create API object '''
    from ..wrapt_timeout_decorator import timeout
    global inventree_api

    @timeout(dec_timeout=connect_timeout)
    def get_inventree_api_timeout():
        return InvenTreeAPI(server, username=username, password=password)

    try:
        inventree_api = get_inventree_api_timeout()
    except:
        return False

    if inventree_api.token:
        return True
    return False


def get_inventree_category_id(category_name: str, parent_category_id=None) -> int:
    ''' Get InvenTree category ID from name, specificy parent if subcategory '''
    global inventree_api

    # Fetch all categories
    part_categories = PartCategory.list(inventree_api)

    for item in part_categories:
        if category_name == item.name:
            # Check parent id match (if passed as argument)
            match = True
            if parent_category_id:
                cprint(f'[TREE]\t{item.getParentCategory().pk} ?= {parent_category_id}', silent=settings.HIDE_DEBUG)
                if item.getParentCategory().pk != parent_category_id:
                    match = False
            if match:
                cprint(f'[TREE]\t{item.name} ?= {category_name} => True', silent=settings.HIDE_DEBUG)
                return item.pk
        else:
            cprint(f'[TREE]\t{item.name} ?= {category_name} => False', silent=settings.HIDE_DEBUG)

    return -1


def get_category_parameters(category_id: int) -> list:
    ''' Get all default parameter templates for category '''
    global inventree_api

    parameter_templates = []

    category = PartCategory(inventree_api, category_id)

    try:
        category_templates = category.get_category_parameter_templates(fetch_parent=True)
    except AttributeError:
        category_templates = None

    if category_templates:
        for template in category_templates:

            default_value = template.default_value
            if not default_value:
                default_value = '-'

            parameter_templates.append([template.parameter_template['name'], default_value])

    return parameter_templates


def get_part_number(part_id: int) -> str:
    ''' Get InvenTree part number from specified Part ID '''
    global inventree_api

    part = Part(inventree_api, part_id)
    return part.IPN


def set_part_number(part_id: int, ipn: str) -> bool:
    ''' Set InvenTree part number for specified Part ID '''
    global inventree_api

    part = Part(inventree_api, part_id)
    part._data['IPN'] = ipn
    part.save()

    if Part(inventree_api, part_id).IPN == ipn:
        return True
    else:
        return False


def is_new_part(category_id: int, part_info: dict) -> int:
    ''' Check if part exists based on parameters (or description) '''
    global inventree_api

    # Get category object
    part_category = PartCategory(inventree_api, category_id)

    # Fetch all parts from category and subcategories
    part_list = []
    part_list.extend(part_category.getParts())
    for subcategory in part_category.getChildCategories():
        part_list.extend(subcategory.getParts())

    # Extract parameter from part info
    # Verify parameters values are not empty
    new_part_parameters = part_info['parameters'] if list(set(part_info['parameters'].values())) != ['-'] else None

    template_list = ParameterTemplate.list(inventree_api)

    def fetch_template_name(template_id):
        for item in template_list:
            if item.pk == template_id:
                return item.name

    # Retrieve parent category name for parameters compare
    try:
        category_name = part_category.getParentCategory().name
    except AttributeError:
        category_name = part_category.name
    filters = config_interface.load_category_parameters_filters(category=category_name,
                                                                supplier_config_path=settings.CONFIG_PARAMETERS_FILTERS)
    # cprint(filters)

    for part in part_list:
        # Get part parameters
        db_part_parameters = part.getParameters()
        part_parameters = {}
        for parameter in db_part_parameters:
            parameter_name = fetch_template_name(parameter.template)
            parameter_value = parameter.data
            part_parameters[parameter_name] = parameter_value

        if new_part_parameters and part_parameters:
            # Compare database part with new part
            compare = part_tools.compare(new_part_parameters=new_part_parameters,
                                         db_part_parameters=part_parameters,
                                         include_filters=filters)
        else:
            # Compare with name and description
            compare = part_info['name'] == part.name and \
                part_info['description'] == part.description and \
                part_info['revision'] == part.revision
            
            # Check if new manufacturer part
            if not compare:
                manufacturer = list(part_info['manufacturer'].keys())[0]
                mpn = list(part_info['manufacturer'].values())[0][0]
                compare = not is_new_manufacturer_part(manufacturer, mpn)

        if compare:
            cprint(f'\n[TREE]\tFound part match in database (pk = {part.pk})', silent=settings.HIDE_DEBUG)
            return part.pk

    cprint('\n[TREE]\tNo match found in database', silent=settings.HIDE_DEBUG)
    return 0


def create_category(parent: str, name: str):
    ''' Create InvenTree category, use parent for subcategories '''
    global inventree_api

    parent_id = 0
    is_new_category = False

    # Check if category already exists
    category_list = PartCategory.list(inventree_api)
    for category in category_list:
        if name == category.name:
            try:
                # Check if parents are the same
                if category.getParentCategory().name == parent:
                    # Return category ID
                    return category.pk, is_new_category
            except:
                return category.pk, is_new_category
        elif parent == category.name:
            # Get Parent ID
            parent_id = category.pk
        else:
            pass

    if parent:
        if parent_id > 0:
            category = PartCategory.create(inventree_api, {
                'name': name,
                'parent': parent_id,
            })

            is_new_category = True
        else:
            cprint(f'[TREE]\tError: Check parent category name ({parent})', silent=settings.SILENT)
            return -1, is_new_category
    else:
        # No parent
        category = PartCategory.create(inventree_api, {
            'name': name,
            'parent': None,
        })
        is_new_category = True

    return category.pk, is_new_category


def upload_part_image(image_url: str, part_id: int) -> bool:
    ''' Upload InvenTree part thumbnail'''
    global inventree_api

    # Get image full path
    image_name = f'{str(part_id)}_thumbnail.jpeg'
    image_location = settings.search_images + image_name

    # Download image (multiple attempts)
    if not download_image(image_url, image_location):
        return False

    # Upload image to InvenTree
    part = Part(inventree_api, part_id)
    if part:
        return part.uploadImage(image=image_location)
    else:
        return False


def create_part(category_id: int, name: str, description: str, revision: str, image: str, keywords=None) -> int:
    ''' Create InvenTree part '''
    global inventree_api

    part = Part.create(inventree_api, {
        'name': name,
        'description': description,
        'category': category_id,
        'keywords': keywords,
        'revision': revision,
        'active': True,
        'virtual': False,
        'component': True,
        'purchaseable': True,
    })

    if part:
        return part.pk
    else:
        return 0


def delete_part(part_id: int) -> bool:
    ''' Delete InvenTree part (only used for testing) '''
    global inventree_api

    part = Part(inventree_api, part_id)
    if part.pk:
        part._data['active'] = False
        # Remove image url (API rejects it as it is not a file)
        try:
            del part._data['image']
        except:
            pass
        part.save()
        return part.delete()
    else:
        return True


def create_company(company_name: str, manufacturer=False, supplier=False) -> bool:
    ''' Create InvenTree company '''
    global inventree_api

    if not manufacturer and not supplier:
        return None

    company = Company.create(inventree_api, {
        'name': company_name,
        'description': company_name,
        'is_customer': False,
        'is_supplier': supplier,
        'is_manufacturer': manufacturer,
    })

    return company


def get_company_id(company_name: str) -> int:
    ''' Get company (supplier/manufacturer) primary key (ID) '''
    global inventree_api

    company_list = Company.list(inventree_api)
    companies = {}
    for company in company_list:
        companies[company.name] = company.pk
    try:
        return companies[company_name]
    except:
        return 0


def is_new_manufacturer_part(manufacturer_name: str, manufacturer_mpn: str) -> bool:
    ''' Check if InvenTree manufacturer part exists to avoid duplicates '''
    global inventree_api

    # Fetch all companies
    cprint('[TREE]\tFetching manufacturers', silent=settings.HIDE_DEBUG)
    company_list = Company.list(inventree_api, is_manufacturer=True, is_customer=False)
    companies = {}
    for company in company_list:
        companies[company.name] = company

    try:
        # Get all parts
        part_list = companies[manufacturer_name].getManufacturedParts()
    except:
        part_list = None

    if part_list is None:
        # Create
        cprint(f'[TREE]\tCreating new manufacturer "{manufacturer_name}"', silent=settings.SILENT)
        create_company(
            company_name=manufacturer_name,
            manufacturer=True,
        )
        # Get all parts
        part_list = []

    for item in part_list:
        try:
            if manufacturer_mpn in item.MPN:
                cprint(f'[TREE]\t{item.MPN} ?= {manufacturer_mpn} => True', silent=settings.HIDE_DEBUG)
                return False
            else:
                cprint(f'[TREE]\t{item.MPN} ?= {manufacturer_mpn} => False', silent=settings.HIDE_DEBUG)
        except TypeError:
            cprint(f'[TREE]\t{item.MPN} ?= {manufacturer_mpn} => *** SKIPPED ***', silent=settings.HIDE_DEBUG)

    return True


def is_new_supplier_part(supplier_name: str, supplier_sku: str) -> bool:
    ''' Check if InvenTree supplier part exists to avoid duplicates '''
    global inventree_api

    # Fetch all companies
    cprint('[TREE]\tFetching suppliers', silent=settings.HIDE_DEBUG)
    company_list = Company.list(inventree_api, is_supplier=True, is_customer=False)
    companies = {}
    for company in company_list:
        companies[company.name] = company

    try:
        # Get all parts
        part_list = companies[supplier_name].getSuppliedParts()
    except:
        part_list = None

    if part_list is None:
        # Create
        cprint(f'[TREE]\tCreating new supplier "{supplier_name}"', silent=settings.SILENT)
        create_company(
            company_name=supplier_name,
            supplier=True,
        )
        # Get all parts
        part_list = []

    for item in part_list:
        if supplier_sku in item.SKU:
            cprint(f'[TREE]\t{item.SKU} ?= {supplier_sku} => True', silent=settings.HIDE_DEBUG)
            return False
        else:
            cprint(f'[TREE]\t{item.SKU} ?= {supplier_sku} => False', silent=settings.HIDE_DEBUG)

    return True


def create_manufacturer_part(part_id: int, manufacturer_name: str, manufacturer_mpn: str, description: str, datasheet: str) -> bool:
    ''' Create InvenTree manufacturer part

        part_id: Part the manufacturer data is linked to
        manufacturer: Company that manufactures the SupplierPart (leave blank if it is the sample as the Supplier!)
        MPN: Manufacture part number
        datasheet: Datasheet link
        description: Descriptive notes field
    '''
    global inventree_api

    # Get Manufacturer ID
    manufacturer_id = get_company_id(manufacturer_name)

    if manufacturer_id:
        # Validate datasheet link
        if not validators.url(datasheet):
            datasheet = ''

        manufacturer_part = ManufacturerPart.create(inventree_api, {
            'part': part_id,
            'manufacturer': manufacturer_id,
            'MPN': manufacturer_mpn,
            'link': datasheet,
            'description': description,
        })

        if manufacturer_part:
            return True
    else:
        cprint(f'[TREE]\tError: Manufacturer "{manufacturer_name}" not found (failed to create manufacturer part)',
               silent=settings.SILENT)

    return False


def create_supplier_part(part_id: int, manufacturer_name: str, manufacturer_mpn: str, supplier_name: str, supplier_sku: str, description: str, link: str) -> bool:
    ''' Create InvenTree supplier part

        part_id: Part the supplier data is linked to
        manufacturer_name: Manufacturer the supplier data is linked to
        manufacturer_mpn: MPN the supplier data is linked to
        supplier: Company that supplies this SupplierPart object
        SKU: Stock keeping unit (supplier part number)
        manufacturer: Company that manufactures the SupplierPart (leave blank if it is the sample as the Supplier!)
        MPN: Manufacture part number
        link: Link to part detail page on supplier's website
        description: Descriptive notes field
    '''
    global inventree_api

    # Get Supplier ID
    supplier_id = get_company_id(supplier_name)

    if not manufacturer_name or not manufacturer_mpn:
        # Unset manufacturer data
        manufacturer_name = None
        manufacturer_mpn = None

    if supplier_id:
        # Validate supplier link
        if not validators.url(link):
            link = ''

        supplier_part = SupplierPart.create(inventree_api, {
            'part': part_id,
            'manufacturer': manufacturer_name,
            'MPN': manufacturer_mpn,
            'supplier': supplier_id,
            'SKU': supplier_sku,
            'link': link,
            'description': description,
        })

        if supplier_part:
            return True
    else:
        cprint(f'[TREE]\tError: Supplier "{supplier_name}" not found (failed to create supplier part)',
               silent=settings.SILENT)

    return False


def create_parameter_template(name: str, units: str) -> int:
    ''' Create InvenTree parameter template '''
    global inventree_api

    parameter_templates = ParameterTemplate.list(inventree_api)
    for item in parameter_templates:
        if name == item.name:
            return 0

    parameter_template = ParameterTemplate.create(inventree_api, {
        'name': name,
        'units': units,
    })

    if parameter_template:
        return parameter_template.pk
    else:
        return 0


def create_parameter(part_id: int, template_name: int, value: str):
    ''' Create InvenTree part parameter based on template '''
    global inventree_api

    parameter_template_list = ParameterTemplate.list(inventree_api)

    template_id = 0
    for item in parameter_template_list:
        if template_name == item.name:
            template_id = item.pk
            break

    # Check if template_id already exists for this part
    part = Part(inventree_api, part_id)
    part_parameters = part.getParameters()
    is_new_part_parameters_template_id = True
    for item in part_parameters:
        # cprint(f'[TREE]\t{parameter.template} ?= {template_id}', silent=SILENT)
        if item.template == template_id:
            is_new_part_parameters_template_id = False
            break
    # cprint(part_parameters, silent=SILENT)

    '''
        Create parameter only if:
        - template exists
        - parameter does not exist for this part
    '''
    parameter = None
    if template_id > 0 and is_new_part_parameters_template_id:
        parameter = Parameter.create(inventree_api, {
            'part': part_id,
            'template': template_id,
            'data': value,
        })

    if parameter:
        return parameter.pk, is_new_part_parameters_template_id
    else:
        if template_id == 0:
            cprint(f'[TREE]\tError: Parameter template "{template_name}" does not exist', silent=settings.SILENT)
        return 0, False
