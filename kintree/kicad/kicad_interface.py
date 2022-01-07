from . import kicad_symbol


def inventree_to_kicad(part_data: dict, library_path: str, template_path=None, show_progress=True) -> bool:
    ''' Create KiCad symbol from InvenTree part data '''
    klib = kicad_symbol.ComponentLibManager(library_path)
    return klib.add_symbol_to_library_from_inventree(symbol_data=part_data,
                                                     template_path=template_path,
                                                     show_progress=show_progress)

# NOT YET SUPPORTED - REMOVE?
# def delete_part(part_number: str, library_path: str) -> bool:
#     ''' Delete KiCad symbol from library '''
#     pass
