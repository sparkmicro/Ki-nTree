"""Class to manage KiCad schematics

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    19.02.2022 - created

Documentation taken from:
    https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List
from os import path

from kiutils.items.common import PageSettings, TitleBlock
from kiutils.items.schitems import *
from kiutils.symbol import Symbol
from kiutils.utils import sexpr
from kiutils.misc.config import KIUTILS_CREATE_NEW_GENERATOR_STR, KIUTILS_CREATE_NEW_VERSION_STR

@dataclass
class Schematic():
    """The ``schematic`` token represents a KiCad schematic as defined by the schematic file format

    Documenatation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/
    """

    version: str = "20211123"
    """The ``version`` token attribute defines the schematic version using the YYYYMMDD date format"""

    generator: str = "kicad-python-tools"
    """The ``generator`` token attribute defines the program used to write the file"""

    uuid: Optional[str] = None
    """The ``uuid`` defines the universally unique identifier"""

    paper: PageSettings = field(default_factory=lambda: PageSettings())
    """The ``paper`` token defines the drawing page size and orientation"""

    titleBlock: Optional[TitleBlock] = None
    """The ``titleBlock`` token defines author, date, revision, company and comments of the schematic"""

    libSymbols: List[Symbol] = field(default_factory=list)
    """The ``libSymbols`` token defines a list of symbols that are used in the schematic"""

    schematicSymbols: List[SchematicSymbol] = field(default_factory=list)
    """The ``schematicSymbols`` token defines a list of instances of symbols used in the schematic"""

    junctions: List[Junction] = field(default_factory=list)
    """The ``junctions`` token defines a list of junctions used in the schematic"""

    noConnects: List[NoConnect] = field(default_factory=list)
    """The ``noConnect`` token defines a list of no_connect markers used in the schematic"""

    busEntries: List[BusEntry] = field(default_factory=list)
    """The ``busEntries`` token defines a list of bus_entry used in the schematic"""

    graphicalItems: List = field(default_factory=list)
    """The ``graphicalItems`` token defines a list of ``bus``, ``wire`` or ``polyline`` elements used in
    the schematic"""

    images: List[Image] = field(default_factory=list)
    """The ``images`` token defines a list of images used in the schematic"""

    texts: List[Text] = field(default_factory=list)
    """The ``text`` token defines a list of texts used in the schematic"""

    labels: List[LocalLabel] = field(default_factory=list)
    """The ``labels`` token defines a list of local labels used in the schematic"""

    globalLabels: List[GlobalLabel] = field(default_factory=list)
    """The ``globalLabels`` token defines a list of global labels used in the schematic"""

    hierarchicalLabels: List[HierarchicalLabel] = field(default_factory=list)
    """The ``herarchicalLabels`` token defines a list of hierarchical labels used in the schematic"""

    sheets: List[HierarchicalSheet] = field(default_factory=list)
    """The ``sheets`` token defines a list of hierarchical sheets used in the schematic"""

    sheetInstances: List[HierarchicalSheetInstance] = field(default_factory=list)
    """The ``sheetInstances`` token defines a list of instances of hierarchical sheets used in
    the schematic"""

    symbolInstances: List[SymbolInstance] = field(default_factory=list)
    """The ``symbolInstances`` token defines a list of instances of symbols from ``libSymbols`` token
    used in the schematic"""

    filePath: Optional[str] = None
    """The ``filePath`` token defines the path-like string to the schematic file. Automatically set when
    ``self.from_file()`` is used. Allows the use of ``self.to_file()`` without parameters."""

    @classmethod
    def from_sexpr(cls, exp: list) -> Schematic:
        """Convert the given S-Expresstion into a Schematic object

        Args:
            - exp (list): Part of parsed S-Expression ``(kicad_sch ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not kicad_sch

        Returns:
            - Schematic: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'kicad_sch':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'version': object.version = item[1]
            if item[0] == 'generator': object.generator = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'paper': object.paper = PageSettings().from_sexpr(item)
            if item[0] == 'title_block': object.titleBlock = TitleBlock().from_sexpr(item)
            if item[0] == 'lib_symbols':
                for symbol in item[1:]:
                    object.libSymbols.append(Symbol().from_sexpr(symbol))
            if item[0] == 'junction': object.junctions.append(Junction().from_sexpr(item))
            if item[0] == 'no_connect': object.noConnects.append(NoConnect().from_sexpr(item))
            if item[0] == 'bus_entry': object.busEntries.append(BusEntry().from_sexpr(item))
            if item[0] == 'wire': object.graphicalItems.append(Connection().from_sexpr(item))
            if item[0] == 'bus': object.graphicalItems.append(Connection().from_sexpr(item))
            if item[0] == 'polyline': object.graphicalItems.append(PolyLine().from_sexpr(item))
            if item[0] == 'image': object.images.append(Image().from_sexpr(item))
            if item[0] == 'text': object.texts.append(Text().from_sexpr(item))
            if item[0] == 'label': object.labels.append(LocalLabel().from_sexpr(item))
            if item[0] == 'global_label': object.globalLabels.append(GlobalLabel().from_sexpr(item))
            if item[0] == 'hierarchical_label': object.hierarchicalLabels.append(HierarchicalLabel().from_sexpr(item))
            if item[0] == 'symbol': object.schematicSymbols.append(SchematicSymbol().from_sexpr(item))
            if item[0] == 'sheet': object.sheets.append(HierarchicalSheet().from_sexpr(item))
            if item[0] == 'sheet_instances':
                for instance in item[1:]:
                    object.sheetInstances.append(HierarchicalSheetInstance().from_sexpr(instance))
            if item[0] == 'symbol_instances':
                for instance in item[1:]:
                    object.symbolInstances.append(SymbolInstance().from_sexpr(instance))
        return object

    @classmethod
    def from_file(cls, filepath: str, encoding: Optional[str] = None) -> Schematic:
        """Load a schematic directly from a KiCad schematic file (`.kicad_sch`) and sets the
        ``self.filePath`` attribute to the given file path.

        Args:
            - filepath (str): Path or path-like object that points to the file
            - encoding (str, optional): Encoding of the input file. Defaults to None (platform 
                                        dependent encoding).

        Raises:
            - Exception: If the given path is not a file

        Returns:
            - Schematic: Object of the Schematic class initialized with the given KiCad schematic
        """
        if not path.isfile(filepath):
            raise Exception("Given path is not a file!")

        with open(filepath, 'r', encoding=encoding) as infile:
            item = cls.from_sexpr(sexpr.parse_sexp(infile.read()))
            item.filePath = filepath
            return item

    @classmethod
    def create_new(cls) -> Schematic:
        """Creates a new empty schematic page with its attributes set as KiCad would create it

        Returns:
            - Schematic: Empty schematic
        """
        schematic = cls(
            version = KIUTILS_CREATE_NEW_VERSION_STR,
            generator = KIUTILS_CREATE_NEW_GENERATOR_STR
        )
        schematic.sheetInstances.append(HierarchicalSheetInstance(instancePath='/', page='1'))
        return schematic

    def to_file(self, filepath = None, encoding: Optional[str] = None):
        """Save the object to a file in S-Expression format

        Args:
            - filepath (str, optional): Path-like string to the file. Defaults to None. If not set, 
                                        the attribute ``self.filePath`` will be used instead.
            - encoding (str, optional): Encoding of the output file. Defaults to None (platform 
                                        dependent encoding).

        Raises:
            - Exception: If no file path is given via the argument or via `self.filePath`
        """
        if filepath is None:
            if self.filePath is None:
                raise Exception("File path not set")
            filepath = self.filePath

        with open(filepath, 'w', encoding=encoding) as outfile:
            outfile.write(self.to_sexpr())

    def to_sexpr(self, indent=0, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        expression =  f'{indents}(kicad_sch (version {self.version}) (generator {self.generator})\n'
        if self.uuid is not None:
            expression += f'\n{indents}  (uuid {self.uuid})\n\n'
        expression += f'{self.paper.to_sexpr(indent+2)}'
        if self.titleBlock is not None:
            expression += f'\n{self.titleBlock.to_sexpr(indent+2)}'

        if self.libSymbols:
            expression += f'\n{indents}  (lib_symbols'
            for item in self.libSymbols:
                expression += '\n'
                expression += item.to_sexpr(indent+4)
            expression += f'{indents}  )\n'
        else:
            expression += f'{indents}  (lib_symbols)\n'

        if self.junctions:
            expression += '\n'
            for item in self.junctions:
                expression += item.to_sexpr(indent+2)

        if self.noConnects:
            expression += '\n'
            for item in self.noConnects:
                expression += item.to_sexpr(indent+2)

        if self.busEntries:
            expression += '\n'
            for item in self.busEntries:
                expression += item.to_sexpr(indent+2)

        if self.graphicalItems:
            expression += '\n'
            for item in self.graphicalItems:
                expression += item.to_sexpr(indent+2)

        if self.images:
            expression += '\n'
            for item in self.images:
                expression += item.to_sexpr(indent+2)

        if self.texts:
            expression += '\n'
            for item in self.texts:
                expression += item.to_sexpr(indent+2)

        if self.labels:
            expression += '\n'
            for item in self.labels:
                expression += item.to_sexpr(indent+2)

        if self.globalLabels:
            expression += '\n'
            for item in self.globalLabels:
                expression += item.to_sexpr(indent+2)

        if self.hierarchicalLabels:
            expression += '\n'
            for item in self.hierarchicalLabels:
                expression += item.to_sexpr(indent+2)

        if self.schematicSymbols:
            for item in self.schematicSymbols:
                expression += '\n'
                expression += item.to_sexpr(indent+2)

        if self.sheets:
            for item in self.sheets:
                expression += '\n'
                expression += item.to_sexpr(indent+2)

        if self.sheetInstances:
            expression += '\n'
            expression += '  (sheet_instances\n'
            for item in self.sheetInstances:
                expression += item.to_sexpr(indent+4)
            expression += '  )\n'

        if self.symbolInstances:
            expression += '\n'
            expression += '  (symbol_instances\n'
            for item in self.symbolInstances:
                expression += item.to_sexpr(indent+4)
            expression += '  )\n'

        expression += f'{indents}){endline}'
        return expression
