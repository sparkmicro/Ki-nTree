from . import kicad_symbol

def inventree_to_kicad(part_data: dict, library_path: str, template_path=None, show_progress=True) -> bool:
    ''' Create KiCad symbol from InvenTree part data '''
    klib = kicad_symbol.ComponentLibManager(library_path)
    if klib:
        return klib.add_component_to_library_from_inventree(component_data=part_data,
                                                            template_path=template_path,
                                                            show_progress=show_progress)
    else:
        return False, False

# NOT SUPPORTED YET
# def delete_part(part_number: str, library_path: str) -> bool:
#     ''' Delete KiCad symbol from library '''
#     return klib.delete_component_from_lib(part_number=part_number,
#                                           library_path=library_path)
