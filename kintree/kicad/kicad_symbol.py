import os

from ..config import settings
from ..common import progress
from ..common.tools import cprint
from kintree.kicad.common import kicad_sym


# KiCad Component Library Manager
class ComponentLibManager(object):
    def __init__(self, library_path):
        # Load library and template paths
        cprint(f'[KCAD]\tlibrary_path: {library_path}', silent=settings.SILENT)

        # Check files exist
        if not os.path.isfile(library_path):
            cprint(f'[KCAD]\tError loading library file ({library_path})', silent=settings.SILENT)
            return None

        # Load library
        self.kicad_lib = kicad_sym.KicadLibrary.from_file(library_path)
        self.library_name = library_path.split(os.sep)[-1]
        cprint('[KCAD]\tNumber of parts in library ' + self.library_name + ': ' + str(len(self.kicad_lib.symbols)), silent=settings.SILENT)

    def is_symbol_in_library(self, symbol_part_number):
        ''' Check if symbol already exists in library '''
        for symbol in self.kicad_lib.symbols:
            cprint(f'[DBUG]\t{symbol.name} ?= {symbol_part_number}', silent=settings.HIDE_DEBUG)
            if symbol.name == symbol_part_number:
                cprint(f'[KCAD]\tWarning: Component {symbol_part_number} already in library', silent=settings.SILENT)
                return True

        return False

    def add_symbol_to_library_from_inventree(self, symbol_data, template_path=None, show_progress=True):
        ''' Create symbol in KiCad library '''
        part_in_lib = False
        new_part = False
        category = symbol_data['category'][0]
        subcategory = symbol_data['category'][1]

        if not template_path:
            # Fetch template path
            try:
                template_path = settings.symbol_templates_paths[category][subcategory]
            except:
                template_path = settings.symbol_templates_paths[category]['Default']

        # Check files exist
        if not self.kicad_lib:
            return part_in_lib, new_part
        if not os.path.isfile(template_path):
            cprint(f'[KCAD]\tError loading template file ({template_path})', silent=settings.SILENT)
            return part_in_lib, new_part

        # Check if part already in library
        try:
            is_symbol_in_library = self.is_symbol_in_library(symbol_data['IPN'])
            part_in_lib = True
        except:
            is_symbol_in_library = False
        if is_symbol_in_library:
            return part_in_lib, new_part

        # Progress Update
        if show_progress and not progress.update_progress_bar_window():
            return part_in_lib, new_part

        # Load template
        templatelib = kicad_sym.KicadLibrary.from_file(template_path)
        # Load new symbol
        if len(templatelib.symbols) == 1:
            for symbol in templatelib.symbols:
                new_symbol = symbol
        else:
            cprint('[KCAD]\tError: Found more than 1 symbol template in template file, aborting', silent=settings.SILENT)
            return part_in_lib, new_part

        # Update name
        new_symbol.name = symbol_data['IPN']

        # Update properties
        for property in new_symbol.properties:
            # Match part data
            if property.value in symbol_data.keys():
                property.value = symbol_data[property.value]
                continue

            # Match parameters
            if property.value in symbol_data['parameters'].keys():
                property.value = symbol_data['parameters'][property.value]
                continue

            # Special properties
            if property.name in ['Value', 'Manufacturer', 'Manufacturer Part Number']:
                if property.name == 'Value':
                    property.value = symbol_data['IPN']
                elif property.name == 'Manufacturer':
                    property.value = list(symbol_data['manufacturer'].keys())[0]
                elif property.name == 'Manufacturer Part Number':
                    property.value = list(symbol_data['manufacturer'].values())[0][0]
                continue

        # Update fields
        # manufacturer_name = ''
        # for field_idx in range(len(new_symbol.fields)):
        #     if 'name' in new_symbol.fields[field_idx]:
        #         symbol_field = str(new_symbol.fields[field_idx]['name']).replace('"', '')
        #         if symbol_field in symbol_data['parameters'].keys():
        #             new_symbol.fields[field_idx]['name'] = symbol_data['parameters'][symbol_field]
        #         elif symbol_field == 'IPN':
        #             new_symbol.fields[field_idx]['name'] = symbol_data['IPN']
        #         elif symbol_field == 'Manufacturer':
        #             for manufacturer in symbol_data['manufacturer'].keys():
        #                 manufacturer_name = manufacturer
        #                 new_symbol.fields[field_idx]['name'] = manufacturer_name
        #                 break
        #         elif symbol_field == 'MPN':
        #             new_symbol.fields[field_idx]['name'] = symbol_data['manufacturer'][manufacturer_name][0]

        # Add symbol to library
        self.kicad_lib.symbols.append(new_symbol)
        # Update generator version
        self.kicad_lib.version = '20211014'
        self.kicad_lib.write()
        cprint(f'[KCAD]\tSuccess: Component added to library {self.library_name}', silent=settings.SILENT)
        part_in_lib = True
        new_part = True

        # Progress Update
        if show_progress and not progress.update_progress_bar_window():
            pass

        return part_in_lib, new_part

    # NOT SUPPORTED YET - REMOVE?
    # def delete_symbol_from_lib(self, part_number):
    #     ''' Remove symbol from KiCad library '''
    #     pass


if __name__ == '__main__':

    test_part = {
        "IPN": "",
        "category": [
            "Capacitors",
            "Ceramic"
        ],
        "datasheet": "https://www.passivecomponent.com/wp-content/uploads/2018/10/MLCC.pdf",
        "description": "CAP CER 0.1UF 16V X7R 0402",
        "image": "https://media.digikey.com/Renders/Walsin%20Tech/Walsin-0402-(1005-Metric)-,5.jpg",
        "inventree_url": "http://127.0.0.1:8000/part/CAP-000030-00/",
        "keywords": "CAP CER 0.1UF 16V X7R 0402",
        "manufacturer": {
            "Walsin Technology Corporation": [
                "0402B104K160CT"
            ]
        },
        "name": "CAP CER 0.1UF 16V X7R 0402",
        "parameters": {
            "ESR": "-",
            "Footprint": "Capacitors:C0603",
            "Package Height": "-",
            "Package Size": "1.00x0.50mm",
            "Package Type": "0402",
            "Rated Voltage": "16V",
            "Symbol": "Capacitors:CAP-000030-00",
            "Temperature Grade": "X7R",
            "Temperature Range": "-55~125\u00b0C",
            "Tolerance": "\u00b110%",
            "Value": "0.1 \u00b5F"
        },
        "revision": "A",
        "supplier": {
            "Digi-Key": [
                "1292-1630-1-ND"
            ]
        },
        "supplier_link": "https://www.digikey.com/en/products/detail/walsin-technology-corporation/0402B104K160CT/6707534"
    }

    import sys
    if len(sys.argv) >= 2:
        kicad_lib = ComponentLibManager(sys.argv[1])
        test_part['IPN'] = sys.argv[2]

        # if not kicad_lib.is_symbol_in_library(mpn):
        #     print("Component not in library")

        kicad_lib.add_symbol_to_library_from_inventree(symbol_data=test_part,
                                                       template_path='/home/francois/Desktop/kicad/Ki-nTree/kintree/kicad/templates/capacitor.kicad_sym',
                                                       show_progress=False)