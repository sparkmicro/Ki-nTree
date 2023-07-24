import os

from ..config import settings
from ..common import progress
from ..common.tools import cprint
from kiutils.symbol import SymbolLib


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
        self.kicad_lib = SymbolLib.from_file(library_path)
        self.library_name = library_path.split(os.sep)[-1]
        cprint('[KCAD]\tNumber of parts in library ' + self.library_name + ': ' + str(len(self.kicad_lib.symbols)), silent=settings.SILENT)

    def is_symbol_in_library(self, symbol_id):
        ''' Check if symbol already exists in library '''
        for symbol in self.kicad_lib.symbols:
            cprint(f'[DBUG]\t{symbol.libId} ?= {symbol_id}', silent=settings.HIDE_DEBUG)
            if symbol.libId == symbol_id:
                cprint(f'[KCAD]\tWarning: Component {symbol_id} already in library', silent=settings.SILENT)
                return True

        return False

    def add_symbol_to_library_from_inventree(self, symbol_data, template_path=None, show_progress=True):
        ''' Create symbol in KiCad library '''
        part_in_lib = False
        new_part = False
        part_name = ''
        parameters = symbol_data.get('parameters', {})
        parameters = {**symbol_data, **parameters}
        key_list = list(parameters.keys())
        key_list.sort(key=len, reverse=True)

        def replace_wildcards(field):
            for key in key_list:
                if key in field:
                    field = field.replace(key, parameters[key])
            return field

        symbol_id = symbol_data.get('Symbol', '').split(':')
        if not symbol_id:
            cprint('[KCAD] Error: Adding a new symbol to a KiCad library requires the \'Symbol\' key with the following format: {lib}:{symbol_id}')
            return part_in_lib, new_part, part_name

        if not template_path:
            category = symbol_data['Template'][0]
            subcategory = symbol_data['Template'][1]

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
            return part_in_lib, new_part, part_name

        # Load template
        templatelib = SymbolLib.from_file(template_path)
        # Load new symbol
        if len(templatelib.symbols) == 1:
            for symbol in templatelib.symbols:
                new_symbol = symbol
        else:
            cprint('[KCAD]\tError: Found more than 1 symbol template in template file, aborting', silent=settings.SILENT)
            return part_in_lib, new_part, part_name

        # Update name/ID
        part_name = replace_wildcards(new_symbol.libId)
        new_symbol.libId = part_name

        # Check if part already in library
        try:
            is_symbol_in_library = self.is_symbol_in_library(part_name)
            part_in_lib = True
        except:
            is_symbol_in_library = False
        if is_symbol_in_library:
            return part_in_lib, new_part, part_name

        # Progress Update
        if not progress.update_progress_bar(show_progress):
            return part_in_lib, new_part, part_name

        # Update properties
        for property in new_symbol.properties:
            property.value = replace_wildcards(property.value)

        # Add symbol to library
        self.kicad_lib.symbols.append(new_symbol)
        # Write library
        self.kicad_lib.to_file()

        cprint(f'[KCAD]\tSuccess: Component added to library {self.library_name}', silent=settings.SILENT)
        part_in_lib = True
        new_part = True

        # Progress Update
        if not progress.update_progress_bar(show_progress):
            pass

        return part_in_lib, new_part, part_name
