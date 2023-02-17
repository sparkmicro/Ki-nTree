"""Classes to manage KiCad footprints

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    02.02.2022 - created

Documentation taken from:
    https://dev-docs.kicad.org/en/file-formats/sexpr-footprint/
"""

from __future__ import annotations

import calendar
import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from os import path

from kiutils.items.zones import Zone
from kiutils.items.common import Position, Coordinate, Net, Group, Font
from kiutils.items.fpitems import *
from kiutils.items.gritems import *
from kiutils.utils import sexpr
from kiutils.utils.strings import dequote, remove_prefix
from kiutils.misc.config import KIUTILS_CREATE_NEW_VERSION_STR

@dataclass
class Attributes():
    """The ``attr`` token defines the list of attributes of a footprint.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_attributes
    """

    type: Optional[str] = None
    """The optional ``type`` token defines the type of footprint. Valid footprint types are ``smd`` and
    ``through_hole``. May be none when no attributes are set."""

    boardOnly: bool = False
    """The optional ``boardOnly`` token indicates that the footprint is only defined in the board
    and has no reference to any schematic symbol"""

    excludeFromPosFiles: bool = False
    """The optional ``excludeFromPosFiles`` token indicates that the footprint position information
    should not be included when creating position files"""

    excludeFromBom: bool = False
    """The optional ``excludeFromBom`` token indicates that the footprint should be excluded when
    creating bill of materials (BOM) files"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Attributes:
        """Convert the given S-Expresstion into a Attributes object

        Args:
            - exp (list): Part of parsed S-Expression ``(attr ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not attr

        Returns:
            - Attributes: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'attr':
            raise Exception("Expression does not have the correct type")

        object = cls()
        if len(exp) > 1:
            # Attributes token may be set with no other items (empty attributes)
            # Test case for this: test_fp_empty_attr.kicad_mod
            if exp[1] == 'through_hole' or exp[1] == 'smd':
                object.type = exp[1]

        for item in exp:
            if item == 'board_only': object.boardOnly = True
            if item == 'exclude_from_pos_files': object.excludeFromPosFiles = True
            if item == 'exclude_from_bom': object.excludeFromBom = True
        return object

    def to_sexpr(self, indent=0, newline=False) -> str:
        """Generate the S-Expression representing this object. Will return an empty string, if the
        following attributes are selected:
        - ``type``: None
        - ``boardOnly``: False
        - ``excludeFromBom``: False
        - ``excludeFromPosFiles``: False

        KiCad won't add the ``(attr ..)`` token to a footprint when this combination is selected.

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        if (self.type == None
            and self.boardOnly == False
            and self.excludeFromBom == False
            and self.excludeFromPosFiles == False):
            return ''

        indents = ' '*indent
        endline = '\n' if newline else ''
        type = f' {self.type}' if self.type is not None else ''

        expression = f'{indents}(attr{type}'
        if self.boardOnly is not None:
            if self.boardOnly:
                expression += ' board_only'
        if self.excludeFromPosFiles is not None:
            if self.excludeFromPosFiles:
                expression += ' exclude_from_pos_files'
        if self.excludeFromBom is not None:
            if self.excludeFromBom:
                expression += ' exclude_from_bom'
        expression += f'){endline}'
        return expression

@dataclass
class Model():
    """The ``model`` token defines the 3D model associated with a footprint.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_3d_model
    """

    path: str = ""
    """The ``path`` attribute is the path and file name of the 3D model"""

    pos: Coordinate = field(default_factory=lambda: Coordinate(0.0, 0.0, 0.0))
    """The ``pos`` token specifies the 3D position coordinates of the model relative to the footprint"""

    scale: Coordinate = field(default_factory=lambda: Coordinate(1.0, 1.0, 1.0))
    """The ``scale`` token specifies the model scale factor for each 3D axis"""

    rotate: Coordinate = field(default_factory=lambda: Coordinate(0.0, 0.0, 0.0))
    """The ``rotate`` token specifies the model rotation for each 3D axis relative to the footprint"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Model:
        """Convert the given S-Expresstion into a Model object

        Args:
            - exp (list): Part of parsed S-Expression ``(model ...)``

        Raises:
            - Exception: When given parameter's type is not a list or the list is not 5 long
            - Exception: When the first item of the list is not model

        Returns:
            - Model: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list) or len(exp) != 5:
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'model':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.path = exp[1]
        object.pos = Coordinate.from_sexpr(exp[2][1])
        object.scale = Coordinate.from_sexpr(exp[3][1])
        object.rotate = Coordinate.from_sexpr(exp[4][1])
        return object

    def to_sexpr(self, indent=2, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        expression =  f'{indents}(model "{dequote(self.path)}"\n'
        expression += f'{indents}  (offset {self.pos.to_sexpr()})\n'
        expression += f'{indents}  (scale {self.scale.to_sexpr()})\n'
        expression += f'{indents}  (rotate {self.rotate.to_sexpr()})\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class DrillDefinition():
    """The ``drill`` token defines the drill attributes for a footprint pad.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_pad_drill_definition
    """

    oval: bool = False
    """The ``oval`` token defines if the drill is oval instead of round"""

    diameter: float = 0.0
    """The ``diameter`` attribute defines the drill diameter"""

    width: Optional[float] = None
    """The optional ``width`` attribute defines the width of the slot for oval drills"""

    offset: Optional[Position] = None
    """The optional ``offset`` token defines the drill offset coordinates from the center of the pad"""

    @classmethod
    def from_sexpr(cls, exp: list) -> DrillDefinition:
        """Convert the given S-Expresstion into a DrillDefinition object

        Args:
            - exp (list): Part of parsed S-Expression ``(drill ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not drill

        Returns:
            - DrillDefinition: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'drill':
            raise Exception("Expression does not have the correct type")

        object = cls()
        # Depending on the ``oval`` token, the fields may be shifted ..
        if exp[1] == 'oval':
            object.oval = True
            object.diameter = exp[2]
            object.width = exp[3]
        else:
            object.diameter = exp[1]
            if len(exp) > 2:
                object.width = exp[2]

        # The ``offset`` token may not be given
        for item in exp:
            if type(item) != type([]): continue
            if item[0] == 'offset': object.offset = Position().from_sexpr(item)
        return object

    def to_sexpr(self, indent: int = 0, newline: bool = False) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        oval = f' oval' if self.oval else ''
        width = f' {self.width}' if self.oval and self.width is not None else ''
        offset = f' (offset {self.offset.X} {self.offset.Y})' if self.offset is not None else ''

        return f'{indents}(drill{oval} {self.diameter}{width}{offset}){endline}'

@dataclass
class PadOptions():
    """The ``options`` token attributes define the settings used for custom pads. This token is
    only used when a custom pad is defined.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_custom_pad_options
    """
    clearance: str = "outline"
    """The ``clearance`` token defines the type of clearance used for a custom pad. Valid clearance
    types are ``outline`` and ``convexhull``."""

    anchor: str = "rect"
    """The ``anchor`` token defines the anchor pad shape of a custom pad. Valid anchor pad shapes
    are rect and circle."""

    @classmethod
    def from_sexpr(cls, exp: list) -> PadOptions:
        """Convert the given S-Expresstion into a PadOptions object

        Args:
            - exp (list): Part of parsed S-Expression ``(options ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not options

        Returns:
            - PadOptions: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'options':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'clearance': object.clearance = item[1]
            if item[0] == 'anchor': object.anchor = item[1]
        return object

    def to_sexpr(self, indent: int = 0, newline: bool = False) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        return f'{indents}(options (clearance {self.clearance}) (anchor {self.anchor})){endline}'

@dataclass
class Pad():
    """The ``pad`` token defines a pad in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint_pad
    """

    number: str = "x"
    """The ``number`` attribute is the pad number"""

    type: str = "smd"
    """The pad ``type`` can be defined as ``thru_hole``, ``smd``, ``connect``, or ``np_thru_hole``"""

    shape: str = "rect"
    """The pad ``shape`` can be defined as ``circle``, ``rect``, ``oval``, ``trapezoid``, ``roundrect``, or
    ``custom``"""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y coordinates and optional orientation angle of the pad"""

    locked: bool = False
    """The optional ``locked`` token defines if the footprint pad can be edited"""

    size: Position = field(default_factory=lambda: Position())         # Size uses Position class for simplicity for now
    """The ``size`` token defines the width and height of the pad"""

    drill: Optional[DrillDefinition] = None
    """The optional pad ``drill`` token defines the pad drill requirements"""

    # TODO: Test case for one-layer pad??
    layers: List[str] = field(default_factory=list)
    """The ``layers`` token defines the layer or layers the pad reside on"""

    property: Optional[str] = None
    """The optional ``property`` token defines any special properties for the pad. Valid properties
    are ``pad_prop_bga``, ``pad_prop_fiducial_glob``, ``pad_prop_fiducial_loc``, ``pad_prop_testpoint``,
    ``pad_prop_heatsink``, ``pad_prop_heatsink``, and ``pad_prop_castellated``"""

    removeUnusedLayers: bool = False
    """The optional ``removeUnusedLayers`` token specifies that the copper should be removed from
    any layers the pad is not connected to"""

    keepEndLayers: bool = False
    """The optional ``keepEndLayers`` token specifies that the top and bottom layers should be
    retained when removing the copper from unused layers"""

    roundrectRatio: Optional[float] = None
    """The optional ``roundrectRatio`` token defines the scaling factor of the pad to corner radius
    for rounded rectangular and chamfered corner rectangular pads. The scaling factor is a
    number between 0 and 1."""

    chamferRatio: Optional[float] = None   # Adds a newline before
    """The optional ``chamferRatio`` token defines the scaling factor of the pad to chamfer size.
    The scaling factor is a number between 0 and 1."""

    chamfer: List[str] = field(default_factory=list)
    """The optional ``chamfer`` token defines a list of one or more rectangular pad corners that
    get chamfered. Valid chamfer corner attributes are ``top_left``, ``top_right``, ``bottom_left``,
    and ``bottom_right``."""

    net: Optional[Net] = None
    """The optional ``net`` token defines the integer number and name string of the net connection
    for the pad."""

    tstamp: Optional[str] = None           # Used since KiCad 6
    """The optional ``tstamp`` token defines the unique identifier of the pad object"""

    pinFunction: Optional[str] = None
    """The optional ``pinFunction`` token attribute defines the associated schematic symbol pin name"""

    pinType: Optional[str] = None
    """The optional ``pinType`` token attribute defines the associated schematic pin electrical type"""

    dieLength: Optional[float] = None      # Adds a newline before
    """The optional ``dieLength`` token attribute defines the die length between the component pad
    and physical chip inside the component package"""

    solderMaskMargin: Optional[float] = None
    """The optional ``solderMaskMargin`` token attribute defines the distance between the pad and
    the solder mask for the pad. If not set, the footprint solder_mask_margin is used."""

    solderPasteMargin: Optional[float] = None
    """The optional ``solderPasteMargin`` token attribute defines the distance the solder paste
    should be changed for the pad"""

    solderPasteMarginRatio: Optional[float] = None
    """The optional ``solderPasteMarginRatio`` token attribute defines the percentage to reduce the
    pad outline by to generate the solder paste size"""

    clearance: Optional[float] = None
    """The optional ``clearance`` token attribute defines the clearance from all copper to the pad.
    If not set, the footprint clearance is used."""

    zoneConnect: Optional[int] = None
    """The optional ``zoneConnect`` token attribute defines type of zone connect for the pad. If
    not defined, the footprint zone_connection setting is used. Valid connection types are
    integers values from 0 to 3 which defines:
    - 0: Pad is not connect to zone
    - 1: Pad is connected to zone using thermal relief
    - 2: Pad is connected to zone using solid fill
    - 3: Only through hold pad is connected to zone using thermal relief
    """

    thermalWidth: Optional[float] = None
    """The optional ``thermalWidth`` token attribute defines the thermal relief spoke width used for
    zone connection for the pad. This only affects a pad connected to a zone with a thermal
    relief. If not set, the footprint thermal_width setting is used."""

    thermalGap: Optional[float] = None
    """The optional ``thermalGap`` token attribute defines the distance from the pad to the zone of
    the thermal relief connection for the pad. This only affects a pad connected to a zone
    with a thermal relief. If not set, the footprint thermal_gap setting is used."""

    customPadOptions: Optional[PadOptions] = None
    """The optional ``customPadOptions`` token defines the options when a custom pad is defined"""

    # Documentation seems wrong about primitives here. It seems like its just a list
    # of graphical objects, but the docu suggests, besides the list, two other params
    # for the primitive token: width and fill
    # These two however are note generated under the primitive token from the KiCad
    # generator. These two params may be found in gr_poly or gr_XX only.
    # So for now, the custom pad primitives are only a list of graphical objects
    customPadPrimitives: List = field(default_factory=list)
    """The optional ``customPadPrimitives`` defines the drawing objects and options used to define
    a custom pad"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Pad:
        """Convert the given S-Expresstion into a Pad object

        Args:
            - exp (list): Part of parsed S-Expression ``(pad ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not pad

        Returns:
            - Pad: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'pad':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.number = exp[1]
        object.type = exp[2]
        object.shape = exp[3]

        for item in exp[3:]:
            if type(item) != type([]):
                if item == 'locked': object.locked = True

            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'size': object.size = Position().from_sexpr(item)
            if item[0] == 'drill': object.drill = DrillDefinition().from_sexpr(item)
            if item[0] == 'layers':
                for layer in item[1:]:
                    object.layers.append(layer)
            if item[0] == 'property': object.property = item[1]
            if item[0] == 'remove_unused_layers': object.removeUnusedLayers = True
            if item[0] == 'keep_end_layers': object.keepEndLayers = True
            if item[0] == 'roundrect_rratio': object.roundrectRatio = item[1]
            if item[0] == 'chamfer_ratio': object.chamferRatio = item[1]
            if item[0] == 'chamfer':
                for chamfer in item[1:]:
                    object.chamfer.append(chamfer)
            if item[0] == 'net': object.net = Net().from_sexpr(item)
            if item[0] == 'tstamp': object.tstamp = item[1]
            if item[0] == 'pinfunction': object.pinFunction = item[1]
            if item[0] == 'pintype': object.pinType = item[1]
            if item[0] == 'die_length': object.dieLength = item[1]
            if item[0] == 'solder_mask_margin': object.solderMaskMargin = item[1]
            if item[0] == 'solder_paste_margin': object.solderPasteMargin = item[1]
            if item[0] == 'solder_paste_margin_ratio': object.solderPasteMarginRatio = item[1]
            if item[0] == 'clearance': object.clearance = item[1]
            if item[0] == 'zone_connect': object.zoneConnect = item[1]
            if item[0] == 'thermal_width': object.thermalWidth = item[1]
            if item[0] == 'thermal_gap': object.thermalGap = item[1]
            if item[0] == 'options': object.customPadOptions = PadOptions().from_sexpr(item)
            if item[0] == 'primitives':
                for primitive in item[1:]:
                    if primitive[0] == 'gr_text': object.customPadPrimitives.append(GrText().from_sexpr(primitive))
                    if primitive[0] == 'gr_text_box': object.customPadPrimitives.append(GrTextBox().from_sexpr(primitive))
                    if primitive[0] == 'gr_line': object.customPadPrimitives.append(GrLine().from_sexpr(primitive))
                    if primitive[0] == 'gr_rect': object.customPadPrimitives.append(GrRect().from_sexpr(primitive))
                    if primitive[0] == 'gr_circle': object.customPadPrimitives.append(GrCircle().from_sexpr(primitive))
                    if primitive[0] == 'gr_arc': object.customPadPrimitives.append(GrArc().from_sexpr(primitive))
                    if primitive[0] == 'gr_poly': object.customPadPrimitives.append(GrPoly().from_sexpr(primitive))
                    if primitive[0] == 'gr_curve': object.customPadPrimitives.append(GrCurve().from_sexpr(primitive))

                    # XXX: Are dimentions even implemented here?
                    if primitive[0] == 'dimension': raise NotImplementedError("Dimensions are not yet handled! Please report this bug along with the file being parsed.")
        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        champferFound, marginFound, schematicSymbolAssociated = False, False, False
        c, cr, smm, spm, spmr, cl, zc, tw, tg = '', '', '', '', '', '', '', '', ''

        layers = ' (layers'
        for layer in self.layers:
            # For some reason KiCad does not escape a layer with double-quotes if it has a
            # wildcard (*) or an ampersant (&) in it
            if "*." in layer or "&" in layer:
                layers += f' {layer}'
            else:
                layers += f' "{dequote(layer)}"'

        layers += ')'

        locked = ' locked' if self.locked else ''
        drill = f' {self.drill.to_sexpr()}' if self.drill is not None else ''
        ppty = f' (property {self.property})' if self.property is not None else ''
        rul = ' (remove_unused_layers)' if self.removeUnusedLayers else ''
        kel = ' (keep_end_layers)' if self.keepEndLayers else ''
        rrr = f' (roundrect_rratio {self.roundrectRatio})' if self.roundrectRatio is not None else ''

        net = f' {self.net.to_sexpr()}' if self.net is not None else ''
        pf = f' (pinfunction "{dequote(self.pinFunction)}")' if self.pinFunction is not None else ''
        pt = f' (pintype "{dequote(self.pinType)}")' if self.pinType is not None else ''

        # Check if a schematic symbol is associated with this footprint. This is usually set, if the
        # footprint is used in a board file.
        if net != '' or pf != '' or pt != '':
            schematicSymbolAssociated = True

        tstamp = f' (tstamp {self.tstamp})' if self.tstamp is not None else ''

        if len(self.chamfer) > 0:
            champferFound = True
            c = ' (chamfer'
            for chamfer in self.chamfer:
                c += f' {chamfer}'
            c += ')'
        if self.chamferRatio is not None:
            champferFound = True
            cr = f' (chamfer_ratio {self.chamferRatio})'

        if self.position.angle is not None:
            position = f'(at {self.position.X} {self.position.Y} {self.position.angle})'
        else:
            position = f'(at {self.position.X} {self.position.Y})'

        if self.solderMaskMargin is not None:
            marginFound = True
            smm = f' (solder_mask_margin {self.solderMaskMargin})'

        if self.solderPasteMargin is not None:
            marginFound = True
            spm = f' (solder_paste_margin {self.solderPasteMargin})'

        if self.solderPasteMarginRatio is not None:
            marginFound = True
            spmr = f' (solder_paste_margin_ratio {self.solderPasteMarginRatio})'

        if self.clearance is not None:
            marginFound = True
            cl = f' (clearance {self.clearance})'

        if self.zoneConnect is not None:
            marginFound = True
            zc = f' (zone_connect {self.zoneConnect})'

        if self.thermalWidth is not None:
            marginFound = True
            tw = f' (thermal_width {self.thermalWidth})'

        if self.thermalGap is not None:
            marginFound = True
            tg = f' (thermal_gap {self.thermalGap})'

        expression =  f'{indents}(pad "{dequote(str(self.number))}" {self.type} {self.shape}{locked} {position} (size {self.size.X} {self.size.Y}){drill}{ppty}{layers}{rul}{kel}{rrr}'
        if champferFound:
            # Only one whitespace here as all temporary strings have at least one leading whitespace
            expression += f'\n{indents} {cr}{c}'

        if self.dieLength is not None:
            expression += f'\n{indents}  (die_length {self.dieLength})'

        if marginFound or schematicSymbolAssociated:
            # Only one whitespace here as all temporary strings have at least one leading whitespace
            expression += f'\n{indents} {net}{pf}{pt}{smm}{spm}{spmr}{cl}{zc}{tw}{tg}'

        if self.customPadOptions is not None:
            expression += f'\n{indents}  {self.customPadOptions.to_sexpr()}'

        if self.customPadPrimitives is not None:
            if len(self.customPadPrimitives) > 0:
                expression += f'\n{indents}  (primitives'
                for primitive in self.customPadPrimitives:
                    expression += f'\n{primitive.to_sexpr(newline=False,indent=indent+4)}'
                expression += f'\n{indents}  )'

        expression += f'{tstamp}){endline}'
        return expression

@dataclass
class Footprint():
    """The ``footprint`` token defines a footprint.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_footprint
    """

    libraryLink: str = ""
    """The ``libraryLink`` attribute defines the link to footprint library of the footprint.
    This only applies to footprints defined in the board file format."""

    version: Optional[str] = None
    """The ``version`` token attribute defines the symbol library version using the YYYYMMDD date format"""

    generator: Optional[str] = None
    """The ``generator`` token attribute defines the program used to write the file"""

    locked: bool = False
    """The optional ``locked`` token defines a flag to indicate the footprint cannot be edited"""

    placed: bool = False
    """The optional ``placed`` token defines a flag to indicate that the footprint has not been placed"""

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the footprint is placed"""

    tedit: str = remove_prefix(hex(calendar.timegm(datetime.datetime.now().utctimetuple())), '0x')
    """The ``tedit`` token defines a the last time the footprint was edited"""

    tstamp: Optional[str] = None
    """The ``tstamp`` token defines the unique identifier for the footprint. This only applies
    to footprints defined in the board file format."""

    position: Optional[Position] = None
    """The ``position`` token defines the X and Y coordinates and rotational angle of the
    footprint. This only applies to footprints defined in the board file format."""

    description: Optional[str] = None
    """The optional ``description`` token defines a string containing the description of the footprint"""

    tags: Optional[str] = None
    """The optional ``tags`` token defines a string of search tags for the footprint"""

    properties: Dict = field(default_factory=dict)
    """The ``properties`` token defines dictionary of properties as key / value pairs where key being
    the name of the property and value being the description of the property"""

    path: Optional[str] = None
    """The ``path`` token defines the hierarchical path of the schematic symbol linked to the footprint.
    This only applies to footprints defined in the board file format."""

    autoplaceCost90: Optional[int] = None
    """The optional ``autoplaceCost90`` token defines the vertical cost of when using the automatic
    footprint placement tool. Valid values are integers 1 through 10. This only applies to footprints
    defined in the board file format."""

    autoplaceCost180: Optional[int] = None
    """The optional ``autoplaceCost180`` token defines the horizontal cost of when using the automatic
    footprint placement tool. Valid values are integers 1 through 10. This only applies to footprints
    defined in the board file format."""

    solderMaskMargin: Optional[float] = None
    """The optional ``solderMaskMargin`` token defines the solder mask distance from all pads in the
    footprint. If not set, the board solder_mask_margin setting is used."""

    solderPasteMargin: Optional[float] = None
    """The optional ``solderPasteMargin`` token defines the solder paste distance from all pads in
    the footprint. If not set, the board solder_paste_margin setting is used."""

    solderPasteRatio: Optional[float] = None
    """The optional ``solderPasteRatio`` token defines the percentage of the pad size used to define
    the solder paste for all pads in the footprint. If not set, the board solder_paste_ratio setting
    is used."""

    clearance: Optional[float] = None
    """The optional ``clearance`` token defines the clearance to all board copper objects for all pads
    in the footprint. If not set, the board clearance setting is used."""

    zoneConnect: Optional[int] = None
    """The optional ``zoneConnect`` token defines how all pads are connected to filled zone. If not
    defined, then the zone connect_pads setting is used. Valid connection types are integers values
    from 0 to 3 which defines:
      - 0: Pads are not connect to zone
      - 1: Pads are connected to zone using thermal reliefs
      - 2: Pads are connected to zone using solid fill
      - 3: Only through hold pads are connected to zone using thermal reliefs
    """

    thermalWidth: Optional[float] = None
    """The optional ``thermalWidth`` token defined the thermal relief spoke width used for zone connections
    for all pads in the footprint. This only affects pads connected to zones with thermal reliefs. If
    not set, the zone thermal_width setting is used."""

    thermalGap: Optional[float] = None
    """The optional ``thermalGap`` is the distance from the pad to the zone of thermal relief connections
    for all pads in the footprint. If not set, the zone thermal_gap setting is used. If not set, the
    zone thermal_gap setting is used."""

    attributes: Attributes = field(default_factory=lambda: Attributes())
    """The optional ``attributes`` section defines the attributes of the footprint"""

    graphicItems: List = field(default_factory=list)
    """The ``graphic`` objects section is a list of one or more graphical objects in the footprint. At a
    minimum, the reference designator and value text objects are defined. All other graphical objects
    are optional."""

    pads: List[Pad] = field(default_factory=list)
    """The optional ``pads`` section is a list of pads in the footprint"""

    zones: List[Zone] = field(default_factory=list)
    """The optional ``zones`` section is a list of keep out zones in the footprint"""

    groups: List[Group] = field(default_factory=list)
    """The optional ``groups`` section is a list of grouped objects in the footprint"""

    models: List[Model] = field(default_factory=list)
    """The ``3D model`` section defines the 3D model object associated with the footprint"""

    filePath: Optional[str] = None
    """The ``filePath`` token defines the path-like string to the library file. Automatically set when
    ``self.from_file()`` is used. Allows the use of ``self.to_file()`` without parameters."""

    @classmethod
    def from_sexpr(cls, exp: list) -> Footprint:
        """Convert the given S-Expresstion into a Footprint object

        Args:
            - exp (list): Part of parsed S-Expression ``(footprint ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not footprint

        Returns:
            - Footprint: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'module' and exp[0] != 'footprint':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.libraryLink = exp[1]
        for item in exp[2:]:
            if not isinstance(item, list):
                if item == 'locked': object.locked = True
                if item == 'placed': object.placed = True
                continue

            if (item[0] == 'version'): object.version = item[1]
            if (item[0] == 'generator'): object.generator = item[1]
            if (item[0] == 'layer'): object.layer = item[1]
            if (item[0] == 'tedit'): object.tedit = item[1]
            if (item[0] == 'tstamp'): object.tstamp = item[1]
            if (item[0] == 'descr'): object.description = item[1]
            if (item[0] == 'tags'): object.tags = item[1]
            if (item[0] == 'path'): object.path = item[1]
            if (item[0] == 'at'): object.position = Position().from_sexpr(item)
            if (item[0] == 'autoplace_cost90'): object.autoplaceCost90 = item[1]
            if (item[0] == 'autoplace_cost180'): object.autoplaceCost180 = item[1]
            if (item[0] == 'solder_mask_margin'): object.solderMaskMargin = item[1]
            if (item[0] == 'solder_paste_margin'): object.solderPasteMargin = item[1]
            if (item[0] == 'solder_paste_ratio'): object.solderPasteRatio = item[1]
            if (item[0] == 'clearance'): object.clearance = item[1]
            if (item[0] == 'zone_connect'): object.zoneConnect = item[1]
            if (item[0] == 'thermal_width'): object.thermalWidth = item[1]
            if (item[0] == 'thermal_gap'): object.thermalGap = item[1]

            if item[0] == 'attr':
                object.attributes = Attributes.from_sexpr(item)
            if item[0] == 'model':
                object.models.append(Model.from_sexpr(item))
            if item[0] == 'fp_text':
                object.graphicItems.append(FpText.from_sexpr(item))
            if item[0] == 'fp_text_box':
                object.graphicItems.append(FpTextBox.from_sexpr(item))
            if item[0] == 'fp_line':
                object.graphicItems.append(FpLine.from_sexpr(item))
            if item[0] == 'fp_rect':
                object.graphicItems.append(FpRect.from_sexpr(item))
            if item[0] == 'fp_circle':
                object.graphicItems.append(FpCircle.from_sexpr(item))
            if item[0] == 'fp_arc':
                object.graphicItems.append(FpArc.from_sexpr(item))
            if item[0] == 'fp_poly':
                object.graphicItems.append(FpPoly.from_sexpr(item))
            if item[0] == 'fp_curve':
                object.graphicItems.append(FpCurve.from_sexpr(item))
            if item[0] == 'dimension':
                raise NotImplementedError("Dimensions are not yet handled! Please report this bug along with the file being parsed.")
            if item[0] == 'pad':
                object.pads.append(Pad.from_sexpr(item))
            if item[0] == 'zone':
                object.zones.append(Zone.from_sexpr(item))
            if item[0] == 'property':
                object.properties.update({ item[1]: item[2] })
            if item[0] == 'group':
                object.groups.append(Group.from_sexpr(item))

        return object

    @classmethod
    def from_file(cls, filepath: str, encoding: Optional[str] = None) -> Footprint:
        """Load a footprint directly from a KiCad footprint file (`.kicad_mod`) and sets the
        ``self.filePath`` attribute to the given file path.

        Args:
            - filepath (str): Path or path-like object that points to the file
            - encoding (str, optional): Encoding of the input file. Defaults to None (platform 
                                        dependent encoding).

        Raises:
            - Exception: If the given path is not a file

        Returns:
            - Footprint: Object of the Footprint class initialized with the given KiCad footprint
        """
        if not path.isfile(filepath):
            raise Exception("Given path is not a file!")

        with open(filepath, 'r', encoding=encoding) as infile:
            rawFootprint = infile.read()

            fpData = sexpr.parse_sexp(rawFootprint)
            return cls.from_sexpr(fpData)

    @classmethod
    def create_new(cls, library_link: str, value: str,
                        type: str = 'other', reference: str = 'REF**') -> Footprint:
        """Creates a new empty footprint with its attributes set as KiCad would create it

        Args:
            - library_link (str): Denotes the name of the library as well as the footprint. Like `Connector:Conn01x02`)
            - value (str): The value text item (printed on the fabrication layer as ``value`` attribute)
            - type (str): Type of footprint (``smd``, ``through_hole`` or ``other``). Defaults to 'other'.
            - reference (str): Reference of the footprint. Defaults to `REF**`.
        Raises:
            - Exception: When the given type is something other than listed above

        Returns:
            - Footprint: Empty footprint
        """
        if type not in ['smd', 'through_hole', 'other']:
            raise Exception("Unsupported type was given")

        fp = cls(
            libraryLink = library_link,
            version = KIUTILS_CREATE_NEW_VERSION_STR,
            generator = 'kiutils'
        )

        # Create text items that are created when adding a new footprint to a library
        fp.graphicItems.extend(
            [
                FpText(
                    type = 'reference', text = reference, layer = 'F.SilkS',
                    effects = Effects(font=Font(thickness=0.15)),
                    position = Position(X=0, Y=-0.5, unlocked=True)
                ),
                FpText(
                    type = 'value', text = value, layer ='F.Fab',
                    effects  = Effects(font=Font(thickness=0.15)),
                    position = Position(X=0, Y=1, unlocked=True)
                ),
                FpText(
                    type = 'user', text = '${REFERENCE}', layer = 'F.Fab',
                    effects = Effects(font=Font(thickness=0.15)),
                    position = Position(X=0, Y=2.5, unlocked=True)
                )
            ]
        )

        # The type ``other`` does not set the attributes type token
        if type != 'other':
            fp.attributes.type = type

        return fp

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

    def to_sexpr(self, indent=0, newline=True, layerInFirstLine=False) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.
            - layerInFirstLine (bool): Prints the ``layer`` token in the first line. Defaults to False

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        locked = ' locked' if self.locked else ''
        placed = ' placed' if self.placed else ''
        version = f' (version {self.version})' if self.version is not None else ''
        generator = f' (generator {self.generator})' if self.generator is not None else ''
        tstamp = f' (tstamp {self.tstamp})' if self.tstamp is not None else ''

        expression =  f'{indents}(footprint "{dequote(self.libraryLink)}"{locked}{placed}{version}{generator}'
        if layerInFirstLine:
            expression += f' (layer "{dequote(self.layer)}")\n'
        else:
            expression += f'\n{indents}  (layer "{dequote(self.layer)}")\n'
        expression += f'{indents}  (tedit {self.tedit}){tstamp}\n'

        if self.position is not None:
            angle = f' {self.position.angle}' if self.position.angle is not None else ''
            expression += f'{indents}  (at {self.position.X} {self.position.Y}{angle})\n'
        if self.description is not None:
            expression += f'{indents}  (descr "{dequote(self.description)}")\n'
        if self.tags is not None:
            expression += f'{indents}  (tags "{dequote(self.tags)}")\n'
        for item in self.properties:
            expression += f'{indents}  (property "{dequote(item)}" "{dequote(self.properties[item])}")\n'
        if self.path is not None:
            expression += f'{indents}  (path "{dequote(self.path)}")\n'

        # Additional parameters used in board
        if self.autoplaceCost90 is not None:
            expression += f'{indents}  (autoplace_cost90 {self.autoplaceCost90})\n'
        if self.autoplaceCost180 is not None:
            expression += f'{indents}  (autoplace_cost180 {self.autoplaceCost180})\n'
        if self.solderMaskMargin is not None:
            expression += f'{indents}  (solder_mask_margin {self.solderMaskMargin})\n'
        if self.solderPasteMargin is not None:
            expression += f'{indents}  (solder_paste_margin {self.solderPasteMargin})\n'
        if self.solderPasteRatio is not None:
            expression += f'{indents}  (solder_paste_ratio {self.solderPasteRatio})\n'
        if self.clearance is not None:
            expression += f'{indents}  (clearance {self.clearance})\n'
        if self.zoneConnect is not None:
            expression += f'{indents}  (zone_connect {self.zoneConnect})\n'
        if self.thermalWidth is not None:
            expression += f'{indents}  (thermal_width {self.thermalWidth})\n'
        if self.thermalGap is not None:
            expression += f'{indents}  (thermal_gap {self.thermalGap})\n'

        if self.attributes is not None:
            # Note: If the attribute object has only standard values in it, it will return an
            #       empty string. Therefore, it should create its own newline and indentations only
            #       when needed.
            expression += self.attributes.to_sexpr(indent=indent+2, newline=True)

        for item in self.graphicItems:
            expression += item.to_sexpr(indent=indent+2)
        for item in self.pads:
            expression += item.to_sexpr(indent=indent+2)
        for item in self.zones:
            expression += item.to_sexpr(indent=indent+2)
        for item in self.models:
            expression += item.to_sexpr(indent=indent+2)
        for item in self.groups:
            expression += item.to_sexpr(indent=indent+2)

        expression += f'{indents}){endline}'
        return expression

