import os

from ..config import settings
from ..common import progress
from ..common.tools import cprint
from lib_utils import kicad_sym


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
            # Main data
            if property.value in symbol_data.keys():
                property.value = symbol_data[property.value]
                continue

            # Parameters
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

        # Add symbol to library
        self.kicad_lib.symbols.append(new_symbol)
        # Update generator version
        self.kicad_lib.version = '20211014'
        # Write library
        self.kicad_lib.write()

        cprint(f'[KCAD]\tSuccess: Component added to library {self.library_name}', silent=settings.SILENT)
        part_in_lib = True
        new_part = True

        # Progress Update
        if show_progress and not progress.update_progress_bar_window():
            pass

        return part_in_lib, new_part

    # NOT YET SUPPORTED - REMOVE?
    # def delete_symbol_from_lib(self, part_number):
    #     ''' Remove symbol from KiCad library '''
    #     pass
