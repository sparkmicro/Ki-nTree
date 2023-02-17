"""Class to manage KiCad boards

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    20.02.2022 - created

Documentation taken from:
    https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from os import path

from kiutils.items.common import Group, Net, PageSettings, TitleBlock
from kiutils.items.zones import Zone
from kiutils.items.brditems import *
from kiutils.items.gritems import *
from kiutils.items.dimensions import Dimension
from kiutils.utils.strings import dequote
from kiutils.utils import sexpr
from kiutils.footprint import Footprint
from kiutils.misc.config import KIUTILS_CREATE_NEW_VERSION_STR, KIUTILS_CREATE_NEW_GENERATOR_STR

@dataclass
class Board():
    """The ``board`` token defines a KiCad layout according to the board file format used in
    ``.kicad_pcb`` files.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/
    """
    version: str = ""
    """The ``version`` token defines the board version using the YYYYMMDD date format"""

    generator: str = ""
    """The ``generator`` token defines the program used to write the file"""

    general: GeneralSettings = field(default_factory=lambda: GeneralSettings())
    """The ``general`` token defines general information about the board"""

    paper: PageSettings = field(default_factory=lambda: PageSettings())
    """The ``paper`` token defines informations about the page itself"""

    titleBlock: Optional[TitleBlock] = None
    """The ``titleBlock`` token defines author, date, revision, company and comments of the board"""

    layers: List[LayerToken] = field(default_factory=list)
    """The ``layers`` token defines all of the layers used by the board"""

    setup: SetupData = field(default_factory=lambda: SetupData())
    """The ``setup`` token is used to store the current settings used by the board"""

    properties: Dict[str, str] = field(default_factory=dict)
    """The ``properties`` token holds a list of key-value properties of the board as a dictionary"""

    nets: List[Net] = field(default_factory=list)
    """The ``nets`` token defines a list of nets used in the layout"""

    footprints: List[Footprint] = field(default_factory=list)
    """The ``footprints`` token defines a list of footprints used in the layout"""

    graphicalItems: List = field(default_factory=list) # as in gritems.py
    """The ``graphicalItems`` token defines a list of graphical items (as listed in `gritems.py`) used
    in the layout"""

    traceItems: List = field(default_factory=list)
    """The ``traceItems`` token defines a list of segments, arcs and vias used in the layout"""

    zones: List[Zone] = field(default_factory=list)
    """The ``zones`` token defines a list of zones used in the layout"""

    dimensions: List[Dimension] = field(default_factory=list)
    """The ``dimensions`` token defines a list of dimensions on the PCB"""

    targets: List[Target] = field(default_factory=list)
    """The ``targets`` token defines a list of target markers on the PCB"""

    groups: List[Group] = field(default_factory=list)
    """The ``groups`` token defines a list of groups used in the layout"""

    filePath: Optional[str] = None
    """The ``filePath`` token defines the path-like string to the board file. Automatically set when
    ``self.from_file()`` is used. Allows the use of ``self.to_file()`` without parameters."""

    @classmethod
    def from_sexpr(cls, exp: list) -> Board:
        """Convert the given S-Expresstion into a Board object

        Args:
            - exp (list): Part of parsed S-Expression ``(kicad_pcb ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not kicad_pcb

        Returns:
            - Board: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'kicad_pcb':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'version': object.version = item[1]
            if item[0] == 'generator': object.generator = item[1]
            if item[0] == 'general': object.general = GeneralSettings().from_sexpr(item)
            if item[0] == 'paper': object.paper = PageSettings().from_sexpr(item)
            if item[0] == 'title_block': object.titleBlock = TitleBlock().from_sexpr(item)
            if item[0] == 'layers':
                for layer in item[1:]:
                    object.layers.append(LayerToken().from_sexpr(layer))
            if item[0] == 'setup': object.setup = SetupData().from_sexpr(item)
            if item[0] == 'property': object.properties.update({item[1]: item[2]})
            if item[0] == 'net': object.nets.append(Net().from_sexpr(item))
            if item[0] == 'footprint': object.footprints.append(Footprint().from_sexpr(item))
            if item[0] == 'gr_text': object.graphicalItems.append(GrText().from_sexpr(item))
            if item[0] == 'gr_text_box': object.graphicalItems.append(GrTextBox().from_sexpr(item))
            if item[0] == 'gr_line': object.graphicalItems.append(GrLine().from_sexpr(item))
            if item[0] == 'gr_rect': object.graphicalItems.append(GrRect().from_sexpr(item))
            if item[0] == 'gr_circle': object.graphicalItems.append(GrCircle().from_sexpr(item))
            if item[0] == 'gr_arc': object.graphicalItems.append(GrArc().from_sexpr(item))
            if item[0] == 'gr_poly': object.graphicalItems.append(GrPoly().from_sexpr(item))
            if item[0] == 'gr_curve': object.graphicalItems.append(GrCurve().from_sexpr(item))
            if item[0] == 'dimension': object.dimensions.append(Dimension().from_sexpr(item))
            if item[0] == 'target': object.targets.append(Target().from_sexpr(item))
            if item[0] == 'segment': object.traceItems.append(Segment().from_sexpr(item))
            if item[0] == 'arc': object.traceItems.append(Arc().from_sexpr(item))
            if item[0] == 'via': object.traceItems.append(Via().from_sexpr(item))
            if item[0] == 'zone': object.zones.append(Zone().from_sexpr(item))
            if item[0] == 'group': object.groups.append(Group().from_sexpr(item))

        return object

    @classmethod
    def from_file(cls, filepath: str, encoding: Optional[str] = None) -> Board:
        """Load a board directly from a KiCad board file (`.kicad_pcb`) and sets the
        ``self.filePath`` attribute to the given file path.

        Args:
            - filepath (str): Path or path-like object that points to the file
            - encoding (str, optional): Encoding of the input file. Defaults to None (platform 
                                        dependent encoding).

        Raises:
            - Exception: If the given path is not a file

        Returns:
            - Footprint: Object of the Schematic class initialized with the given KiCad schematic
        """
        if not path.isfile(filepath):
            raise Exception("Given path is not a file!")

        with open(filepath, 'r', encoding=encoding) as infile:
            item = cls.from_sexpr(sexpr.parse_sexp(infile.read()))
            item.filePath = filepath
            return item

    @classmethod
    def create_new(cls) -> Board:
        """Creates a new empty board with its attributes set as KiCad would create it

        Returns:
            - Board: Empty board
        """
        board = cls(
            version = KIUTILS_CREATE_NEW_VERSION_STR,
            generator = KIUTILS_CREATE_NEW_GENERATOR_STR
        )

        # Add all standard layers to board
        board.layers.extend([
            LayerToken(ordinal=0, name='F.Cu', type='signal'), 
            LayerToken(ordinal=31, name='B.Cu', type='signal'), 
            LayerToken(ordinal=32, name='B.Adhes', type='user', userName="B.Adhesive"),
            LayerToken(ordinal=33, name='F.Adhes', type='user', userName="F.Adhesive"),
            LayerToken(ordinal=34, name='B.Paste', type='user'),
            LayerToken(ordinal=35, name='F.Paste', type='user'),
            LayerToken(ordinal=36, name='B.SilkS', type='user', userName="B.Silkscreen"),
            LayerToken(ordinal=37, name='F.SilkS', type='user', userName="F.Silkscreen"),
            LayerToken(ordinal=38, name='B.Mask', type='user'),
            LayerToken(ordinal=39, name='F.Mask', type='user'),
            LayerToken(ordinal=40, name='Dwgs.User', type='user', userName="User.Drawings"),
            LayerToken(ordinal=41, name='Cmts.User', type='user', userName="User.Comments"),
            LayerToken(ordinal=42, name='Eco1.User', type='user', userName="User.Eco1"),
            LayerToken(ordinal=43, name='Eco2.User', type='user', userName="User.Eco2"),
            LayerToken(ordinal=44, name='Edge.Cuts', type='user'),
            LayerToken(ordinal=45, name='Margin', type='user'),
            LayerToken(ordinal=46, name='B.CrtYd', type='user', userName="B.Courtyard"),
            LayerToken(ordinal=47, name='F.CrtYd', type='user', userName="F.Courtyard"),
            LayerToken(ordinal=48, name='B.Fab', type='user'),
            LayerToken(ordinal=49, name='F.Fab', type='user'),
            LayerToken(ordinal=50, name='User.1', type='user'),
            LayerToken(ordinal=51, name='User.2', type='user'),
            LayerToken(ordinal=52, name='User.3', type='user'),
            LayerToken(ordinal=53, name='User.4', type='user'),
            LayerToken(ordinal=54, name='User.5', type='user'),
            LayerToken(ordinal=55, name='User.6', type='user'),
            LayerToken(ordinal=56, name='User.7', type='user'),
            LayerToken(ordinal=57, name='User.8', type='user'),
            LayerToken(ordinal=58, name='User.9', type='user')
        ])

        # Append net0 to netlist
        board.nets.append(Net())

        return board

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

        addNewLine = False

        expression =  f'{indents}(kicad_pcb (version {self.version}) (generator {self.generator})\n\n'
        expression += self.general.to_sexpr(indent+2) + '\n'
        expression += self.paper.to_sexpr(indent+2)
        if self.titleBlock is not None:
            expression += self.titleBlock.to_sexpr(indent+2) + '\n'
        expression += f'{indents}  (layers\n'
        for layer in self.layers:
            expression += layer.to_sexpr(indent+4)
        expression += f'{indents}  )\n\n'
        expression += self.setup.to_sexpr(indent+2) + '\n'
        # Properties, if any
        if len(self.properties) > 0:
            for key, value in self.properties.items():
                expression += f'  (property "{dequote(key)}" "{dequote(value)}")\n'
            expression += '\n'

        # Nets
        if len(self.nets) > 0:
            for net in self.nets:
                expression += net.to_sexpr(indent=indent+2, newline=True)
            expression += '\n'

        # Footprints
        for footprint in self.footprints:
            expression += footprint.to_sexpr(indent+2, layerInFirstLine=True) + '\n'

        # Lines, Texts, Arcs and other graphical items
        if len(self.graphicalItems) > 0:
            addNewLine = True
            for item in self.graphicalItems:
                if isinstance(item, GrPoly):
                    expression += item.to_sexpr(indent+2, pts_newline=True)
                else:
                    expression += item.to_sexpr(indent+2)

        # Dimensions
        if len(self.dimensions) > 0:
            addNewLine = True
            for dimension in self.dimensions:
                expression += dimension.to_sexpr(indent+2)

        # Target markers:
        if len(self.targets) > 0:
            addNewLine = True
            for target in self.targets:
                expression += target.to_sexpr(indent+2)

        if addNewLine:
            expression += '\n'

        # Segments, vias and arcs
        if len(self.traceItems) > 0:
            for item in self.traceItems:
                expression += item.to_sexpr(indent+2)
            expression += '\n'

        # Zones
        for zone in self.zones:
            expression += zone.to_sexpr(indent+2)

        # Groups
        for group in self.groups:
            expression += group.to_sexpr(indent+2)

        expression += f'{indents}){endline}'
        return expression
