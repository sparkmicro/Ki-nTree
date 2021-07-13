''' DISCLAIMER
SchLib classes and methods were directly imported from: https://github.com/KiCad/kicad-library-utils
Class 'Component' init method was slightly modified to handle double-quote in part parameters:
https://github.com/KiCad/kicad-library-utils/pull/324
'''
# -*- coding: utf-8 -*-

import hashlib
import os.path
import shlex
import sys
from collections import OrderedDict


class Documentation(object):
    """
    A class to parse documentation files (dcm) of Schematic Libraries Files Format of the KiCad
    """
    line_keys = {
        'header': 'EESchema-DOCLIB',
        'start': '$CMP ',
        'description': 'D ',
        'keywords': 'K ',
        'datasheet': 'F ',
        'end': '$ENDCMP',
    }

    def __init__(self, filename, create=False):
        self.filename = filename
        self.components = OrderedDict()
        self.validFile = False
        self.header = None

        self.checksum = ""

        if create:
            if os.path.lexists(self.filename):
                sys.stderr.write("File already exists!\n")
                return
            else:
                self.validFile = True
                self.header = ["EESchema-DOCLIB  Version 2.0\n"]  # used for new dcm files

        else:
            if not os.path.isfile(self.filename):
                sys.stderr.write("DCM file '{filename}' does not exist\n".format(filename=self.filename))
                return
            else:
                self.validFile = True
                self.__parse()

    def __parse(self):
        f = open(self.filename, 'r')
        self.header = [f.readline()]

        if self.header and not self.line_keys['header'] in self.header[0]:
            self.header = None
            sys.stderr.write("'{fn}' is not a KiCad Documentation Library File\n".format(fn=self.filename))
            return False

        name = None
        f.seek(0)

        checksum_data = ''

        for line in f.readlines():
            checksum_data += line.strip()
            line = line.replace('\n', '')
            if line.startswith(Documentation.line_keys['start']):
                name = line[5:].strip()
                keywords = None
                description = None
                datasheet = None
            elif line.startswith(Documentation.line_keys['description']):
                description = line[2:]
            elif line.startswith(Documentation.line_keys['keywords']):
                keywords = line[2:]
            elif line.startswith(Documentation.line_keys['datasheet']):
                datasheet = line[2:]
            elif line.startswith(Documentation.line_keys['end']):
                self.components[name] = OrderedDict([('description', description), ('keywords', keywords), ('datasheet', datasheet)])
            # FIXME: we do not handle comments except separators around components
        f.close()

        try:
            md5 = hashlib.md5(checksum_data.encode('utf-8'))
        except UnicodeDecodeError:
            md5 = hashlib.md5(checksum_data)

        self.checksum = md5.hexdigest()

        return True

    def save(self, filename=None):
        if not self.validFile:
            return False

        if not filename:
            filename = self.filename

        to_write = self.header

        # Ensure that items are written in alphabetical order
        items = sorted(self.components.items(), key=lambda item: item[0])

        for name, doc in items:
            to_write.append('#\n')  # just spacer (no even in dcm format specification, but used everywhere)
            to_write.append(self.line_keys['start'] + name + '\n')
            for key in doc.keys():
                if(doc[key] is not None):
                    to_write.append(self.line_keys[key] + doc[key] + '\n')
            to_write.append(self.line_keys['end'] + '\n')
        to_write.append("#\n")  # again, spacer^^
        to_write.append("#End Doc Library\n")

        f = open(filename, 'w', newline='\n')
        f.writelines(to_write)
        f.close()

    def remove(self, name):
        if name in self.components.keys():  # delete only if it exists
            del self.components[name]

    def add(self, name, doc):
        if doc:  # do not create empty records
            self.components[name] = doc


class Component(object):
    """
    A class to parse components of Schematic Libraries Files Format of the KiCad
    """

    _DEF_KEYS = ['name', 'reference', 'unused', 'text_offset', 'draw_pinnumber', 'draw_pinname', 'unit_count', 'units_locked', 'option_flag']
    _F0_KEYS = ['reference', 'posx', 'posy', 'text_size', 'text_orient', 'visibility', 'htext_justify', 'vtext_justify']
    _FN_KEYS = ['name', 'posx', 'posy', 'text_size', 'text_orient', 'visibility', 'htext_justify', 'vtext_justify', 'fieldname']
    _ARC_KEYS = ['posx', 'posy', 'radius', 'start_angle', 'end_angle', 'unit', 'convert', 'thickness', 'fill', 'startx', 'starty', 'endx', 'endy']
    _CIRCLE_KEYS = ['posx', 'posy', 'radius', 'unit', 'convert', 'thickness', 'fill']
    _POLY_KEYS = ['point_count', 'unit', 'convert', 'thickness', 'points', 'fill']
    _RECT_KEYS = ['startx', 'starty', 'endx', 'endy', 'unit', 'convert', 'thickness', 'fill']
    _TEXT_KEYS = ['direction', 'posx', 'posy', 'text_size', 'text_type', 'unit', 'convert', 'text', 'italic', 'bold', 'hjustify', 'vjustify']
    _PIN_KEYS = ['name', 'num', 'posx', 'posy', 'length', 'direction', 'num_text_size', 'name_text_size', 'unit', 'convert', 'electrical_type', 'pin_type']

    _DRAW_KEYS = {'A': _ARC_KEYS, 'C': _CIRCLE_KEYS, 'P': _POLY_KEYS, 'S': _RECT_KEYS, 'T': _TEXT_KEYS, 'X': _PIN_KEYS}
    # _DRAW_ELEMS = {'arcs':'A', 'circles':'C', 'polylines':'P', 'rectangles':'S', 'texts':'T', 'pins':'X'}

    _KEYS = {'DEF': _DEF_KEYS, 'F0': _F0_KEYS, 'F': _FN_KEYS,
             'A': _ARC_KEYS, 'C': _CIRCLE_KEYS, 'P': _POLY_KEYS, 'S': _RECT_KEYS, 'T': _TEXT_KEYS, 'X': _PIN_KEYS}

    def __init__(self, data, comments, filename, documentation):
        self.comments = comments
        self.fplist = []
        self.aliases = OrderedDict()
        self.lib_filename = filename
        self.dcm_filename = documentation.filename
        building_fplist = False
        building_draw = False
        building_fields = False

        checksum_data = ''

        self.resetDraw()

        for line in data:
            checksum_data += line.strip()
            line = line.replace('\n', '')
            if '\\"' in line:
                import re
                line = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', line)
                # print(line)
            else:
                s = shlex.shlex(line)  # , posix=True)
                s.whitespace_split = True
                s.commenters = ''
                s.quotes = '"'
                line = list(s)

            if len(line) == 0:
                continue

            if line[0] in self._KEYS:
                key_list = self._KEYS[line[0]]
                values = line[1:] + ['' for n in range(len(key_list) - len(line[1:]))]

            if line[0] == 'DEF':
                building_fields = True
                self.definition = dict(zip(self._DEF_KEYS, values))

            elif line[0] == 'ALIAS':
                for alias in line[1:]:
                    self.aliases[alias] = self.getDocumentation(documentation, alias)

            elif line[0] == '$FPLIST':
                building_fields = False
                building_fplist = True
                self.fplist = []

            elif line[0] == '$ENDFPLIST':
                building_fplist = False

            elif line[0] == 'DRAW':
                building_draw = True
                self.resetDraw()
                self.drawOrdered = []  # list of draw elements references, needed to preserve line ordering

            elif line[0] == 'ENDDRAW':
                building_draw = False

            else:
                if building_fplist:
                    self.fplist.append(line[0])

                elif building_draw:
                    if line[0] == 'A':
                        self.draw['arcs'].append(dict(zip(self._ARC_KEYS, values)))
                        self.drawOrdered.append(['A', self.draw['arcs'][-1]])
                    if line[0] == 'C':
                        self.draw['circles'].append(dict(zip(self._CIRCLE_KEYS, values)))
                        self.drawOrdered.append(['C', self.draw['circles'][-1]])
                    if line[0] == 'P':  # mixing X an Y points into 1 list in not handy
                        n_points = int(line[1])
                        points = line[5:5 + (2 * n_points)]
                        values = line[1:5] + [points]
                        if len(line) > (5 + len(points)):
                            values += [line[-1]]
                        else:
                            values += ['']
                        self.draw['polylines'].append(dict(zip(self._POLY_KEYS, values)))
                        self.drawOrdered.append(['P', self.draw['polylines'][-1]])
                    if line[0] == 'S':
                        self.draw['rectangles'].append(dict(zip(self._RECT_KEYS, values)))
                        self.drawOrdered.append(['S', self.draw['rectangles'][-1]])
                    if line[0] == 'T':
                        self.draw['texts'].append(dict(zip(self._TEXT_KEYS, values)))
                        self.drawOrdered.append(['T', self.draw['texts'][-1]])
                    if line[0] == 'X':
                        self.draw['pins'].append(dict(zip(self._PIN_KEYS, values)))
                        self.drawOrdered.append(['X', self.draw['pins'][-1]])

                elif building_fields:
                    if line[0] == 'F0':
                        self.fields = []
                        self.fields.append(dict(zip(self._F0_KEYS, values)))

                    elif line[0][0] == 'F':
                        values = line[1:] + ['' for n in range(len(self._FN_KEYS) - len(line[1:]))]
                        self.fields.append(dict(zip(self._FN_KEYS, values)))

        # perform checksum calculation
        try:
            md5 = hashlib.md5(checksum_data.encode('utf-8'))
        except UnicodeDecodeError:
            md5 = hashlib.md5(checksum_data)
        self.checksum = md5.hexdigest()

        # define some shortcuts
        self.name = self.definition['name']
        self.reference = self.definition['reference']
        self.pins = self.draw['pins']

        # get documentation
        self.documentation = self.getDocumentation(documentation, self.name)

    def resetDraw(self):
        self.draw = {
            'arcs': [],
            'circles': [],
            'polylines': [],
            'rectangles': [],
            'texts': [],
            'pins': []
        }

    def getDocumentation(self, documentation, name):
        try:
            if name.startswith('~'):
                return documentation.components[name[1:(len(name))]]
            else:
                return documentation.components[name]
        except KeyError:
            return {}

    def getPinsByName(self, name):
        pins = []
        for pin in self.pins:
            if pin['name'] == name:
                pins.append(pin)

        return pins

    def getPinByNumber(self, num):
        for pin in self.draw['pins']:
            if pin['num'] == str(num):
                return pin

        return None

    def filterPins(self, name=None, direction=None, electrical_type=None):
        pins = []

        for pin in self.pins:
            if ((name and pin['name'] == name) or (direction and pin['direction'] == direction) or (electrical_type and pin['electrical_type'] == electrical_type)):
                pins.append(pin)

        return pins

    def isNonBOMSymbol(self):
        return self.reference.startswith('#')

    def isPowerSymbol(self):
        return self.definition['option_flag'] == 'P'

    def isPossiblyPowerSymbol(self):
        return (self.reference == '#PWR')

    def isGraphicSymbol(self):
        return self.isNonBOMSymbol() and len(self.pins) == 0

    # heuristics, which tries to determine whether this is a "small" component (resistor, capacitor, LED, diode, transistor, ...)
    def isSmallComponentHeuristics(self):
        if len(self.pins) <= 2:
            return True

        # If there is only a single filled rectangle, we assume that it is the
        # main symbol outline.
        drawing = self.draw
        filled_rects = [rect for rect in drawing['rectangles']
                        if rect['fill'] == 'f']

        # if there is no filled rectangle as symbol outline and we have 3 or 4 pins, we assume this
        # is a small symbol
        if len(self.pins) >= 3 and len(self.pins) <= 4 and len(filled_rects) == 0:
            return True

        return False


class SchLib(object):
    """
    A class to parse Schematic Libraries Files Format of the KiCad
    """

    line_keys = {
        'header': 'EESchema-LIBRARY',
    }

    def __init__(self, filename, create=False):
        self.filename = filename
        self.header = None
        self.components = []
        self.validFile = False

        self.checksum = ""

        self.documentation = Documentation(self.libToDcmFilename(self.filename), create)

        if create:
            if os.path.lexists(self.filename):
                sys.stderr.write("File already exists!\n")
                return
            else:
                self.validFile = True
                self.header = ['EESchema-LIBRARY Version 2.3\n', '#encoding utf-8\n']

        else:
            if not os.path.isfile(self.filename):
                sys.stderr.write("Library file '{filename}' does not exist\n".format(filename=self.filename))
                return
            else:
                self.validFile = True
                self.__parse()

    def libToDcmFilename(self, filename):
        dir_path = os.path.dirname(os.path.realpath(filename))
        filename = os.path.splitext(os.path.basename(filename))
        return os.path.join(dir_path, filename[0] + '.dcm')

    def __parse(self):
        f = open(self.filename, 'r')

        checksum_data = ""

        self.header = [f.readline()]

        checksum_data += self.header[0]

        if self.header and not SchLib.line_keys['header'] in self.header[0]:
            sys.stderr.write("'{fn}' is not a KiCad Schematic Library File\n".format(fn=self.filename))
            return False

        self.header.append(f.readline())
        building_component = False

        comments = []
        for line in f.readlines():

            checksum_data += line.strip()

            if line.startswith('#'):
                comments.append(line)

            elif line.startswith('DEF'):
                building_component = True
                component_data = []
                component_data.append(line)

            elif building_component:
                component_data.append(line)
                if line.startswith('ENDDEF'):
                    building_component = False
                    self.components.append(Component(component_data, comments, self.filename, self.documentation))
                    comments = []
        f.close()

        # perform checksum calculation
        try:
            md5 = hashlib.md5(checksum_data.encode('utf-8'))
        except UnicodeDecodeError:
            md5 = hashlib.md5(checksum_data)
        self.checksum = md5.hexdigest()

        return True

    def validChecksum(self):
        if len(self.checksum) == 0:
            return False
        if len(self.documentation.checksum) == 0:
            return False

        return True

    def compareChecksum(self, otherlib):

        if not self.validChecksum() or not otherlib.validChecksum():
            return False

        return self.checksum == otherlib.checksum and self.documentation.checksum == otherlib.documentation.checksum

    def getComponentByName(self, name):
        for component in self.components:
            if component.definition['name'] == name:
                return component

        return None

    def getComponentCount(self, unique=False):
        count = 0

        for cmp in self.components:
            count += 1

            if unique:
                continue

            count += len(cmp.aliases)

        return count

    def removeComponent(self, name):
        component = self.getComponentByName(name)
        for alias in component.aliases.keys():
            self.documentation.remove(alias)
        self.documentation.remove(name)
        self.components.remove(component)
        return component

    def addComponent(self, component):
        if component not in self.components:
            self.components.append(component)
            self.documentation.add(component.name, component.documentation)
            for alias in component.aliases.keys():
                self.documentation.add(alias, component.aliases[alias])

    def save(self, filename=None):
        if not self.validFile:
            return False

        if not filename:
            filename = self.filename

        self.documentation.save(self.libToDcmFilename(filename))

        # insert the header
        to_write = self.header

        # Ensure that the components are sorted by name!
        components = sorted(self.components, key=lambda cmp: cmp.name)

        # insert the components
        for component in components:
            # append the component comments
            to_write += component.comments

            # DEF
            line = 'DEF '
            for key in Component._DEF_KEYS:
                line += component.definition[key] + ' '

            line = line.rstrip() + '\n'
            to_write.append(line)

            # FIELDS
            line = 'F'
            for i, f in enumerate(component.fields):
                line = "F{n} ".format(n=i)

                if i == 0:
                    keys_list = Component._F0_KEYS
                else:
                    keys_list = Component._FN_KEYS

                for k, key in enumerate(keys_list):
                    key_val = component.fields[i][key]

                    if k == 0 and not key_val.startswith('"'):
                        key_val = '"' + key_val + '"'

                    line += key_val + ' '

                line = line.rstrip() + '\n'
                to_write.append(line)

            # ALIAS
            if len(component.aliases) > 0:
                line = 'ALIAS '
                for alias in component.aliases.keys():
                    line += alias + ' '

                line = line.rstrip() + '\n'
                to_write.append(line)

            # $FPLIST
            if len(component.fplist) > 0:
                to_write.append('$FPLIST\n')
                for fp in component.fplist:
                    to_write.append(' ' + fp + '\n')

            # $ENDFPLIST
                to_write.append('$ENDFPLIST\n')

            # DRAW
            to_write.append('DRAW\n')
            for elem in component.drawOrdered:
                item = elem[1]
                keys_list = Component._DRAW_KEYS[elem[0]]  # 'A' -> keys of all properties of arc
                line = elem[0] + ' '  # 'arcs' -> 'A'
                for k in keys_list:
                    if k == 'points':
                        for i in item['points']:
                            line += '{0} '.format(i)
                    else:
                        line += item[k] + ' '

                line = line.rstrip() + '\n'
                to_write.append(line)

            # ENDDRAW
            to_write.append('ENDDRAW\n')

            # ENDDEF
            to_write.append('ENDDEF\n')

        # insert the footer
        to_write.append('#\n')
        to_write.append('#End Library\n')

        f = open(filename, 'w', newline='\n')
        f.writelines(to_write)
        f.close()
