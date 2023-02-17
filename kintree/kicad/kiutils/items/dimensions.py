"""The dimensions are used to mark spots in the board file for their dimensions (units, metric,
imperial, etc)

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    14.06.2022 - created

Documentation taken from:
    https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_dimension
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

from kiutils.items.common import Position
from kiutils.items.gritems import GrText
from kiutils.utils.strings import dequote

@dataclass
class DimensionFormat():
    """The ``format`` token defines the text formatting of a dimension

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_dimension_format
    """

    prefix: Optional[str] = None
    """The optional ``prefix`` token defines the string to add to the beginning of the dimension text"""

    suffix: Optional[str] = None
    """The optional ``suffix`` token defines the string to add to the end of the dimension text"""

    units: int = 3
    """The ``units`` token defines the dimension units used to display the dimension text. Valid units
    are as follows:
    - 0: Inches
    - 1: Mils
    - 2: Millimeters
    - 3: Automatic"""

    unitsFormat: int = 1
    """The ``unitsFormat`` token defines how the unit's suffix is formatted. Valid units formats are
    as follows:
    - 0: No suffix
    - 1: Bare suffix
    - 2: Wrap suffix in parenthesis"""

    precision: int = 4
    """The ``precision`` token defines the number of significant digits to display"""

    overrideValue: Optional[str] = None
    """The optional ``overrideValue`` token defines the text to substitute for the actual physical
    dimension"""

    suppressZeroes: bool = False
    """The ``suppressZeroes`` token removes all trailing zeros from the dimension text"""

    @classmethod
    def from_sexpr(cls, exp: list) -> DimensionFormat:
        """Convert the given S-Expresstion into a DimensionFormat object

        Args:
            - exp (list): Part of parsed S-Expression ``(format ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not format

        Returns:
            - DimensionFormat: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'format':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp[1:]:
            if type(item) != type([]):
                if item == 'suppress_zeroes': object.suppressZeroes = True
                continue
            if item[0] == 'prefix': object.prefix = item[1]
            if item[0] == 'suffix': object.suffix = item[1]
            if item[0] == 'units': object.units = item[1]
            if item[0] == 'units_format': object.unitsFormat = item[1]
            if item[0] == 'precision': object.precision = item[1]
            if item[0] == 'override_value': object.overrideValue = item[1]
            pass
        return object

    def to_sexpr(self, indent: int = 4, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 4.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        prefix = f' (prefix "{dequote(self.prefix)}")' if self.prefix is not None else ''
        suffix = f' (suffix "{dequote(self.suffix)}")' if self.suffix is not None else ''
        overwrite_val = f' (override_value "{dequote(self.overrideValue)}")' if self.overrideValue is not None else ''
        suppress_zeroes = f' suppress_zeroes' if self.suppressZeroes else ''

        expression =  f'{indents}(format{prefix}{suffix} (units {self.units}) (units_format {self.unitsFormat}) (precision {self.precision}){overwrite_val}{suppress_zeroes}){endline}'
        return expression

@dataclass
class DimensionStyle():
    """The ``style`` token defines the style of a dimension

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_dimension_style
    """

    thickness: float = 0.0
    """The ``thickness`` token defines the line thickness of the dimension"""

    arrowLength: float = 0.0
    """The ``arrowLength`` token defines the length of the dimension arrows"""

    textPositionMode: int = 0
    """The ``textPositionMode`` token defines the position mode of the dimension text. Valid position
    modes are as follows:
    - 0: Text is outside the dimension line
    - 1: Text is in line with the dimension line
    - 2: Text has been manually placed by the user"""

    extensionHeight: Optional[float] = None
    """The optional ``extensionHeight`` token defines the length of the extension lines past the
    dimension crossbar"""

    textFrame: Optional[int] = None
    """The optional ``textFrame`` token defines the style of the frame around the dimension text. This
    only applies to leader dimensions. Valid text frames are as follows:
    - 0: No text frame
    - 1: Rectangle
    - 2: Circle
    - 3:Rounded rectangle"""

    extensionOffset: Optional[float] = None
    """The optional ``extensionOffset`` token defines the distance from feature points to extension
    line start"""

    keepTextAligned: bool = False
    """The ``keepTextAligned`` token indicates that the dimension text should be kept in line with the
    dimension crossbar. When false, the dimension text is shown horizontally regardless of the
    orientation of the dimension."""

    @classmethod
    def from_sexpr(cls, exp: list) -> DimensionStyle:
        """Convert the given S-Expresstion into a DimensionStyle object

        Args:
            - exp (list): Part of parsed S-Expression ``(style ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not style

        Returns:
            - DimensionStyle: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'style':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp[1:]:
            if type(item) != type([]):
                if item == 'keep_text_aligned': object.keepTextAligned = True
                continue
            if item[0] == 'thickness': object.thickness = item[1]
            if item[0] == 'arrow_length': object.arrowLength = item[1]
            if item[0] == 'text_position_mode': object.textPositionMode = item[1]
            if item[0] == 'extension_height': object.extensionHeight = item[1]
            if item[0] == 'text_frame': object.textFrame = item[1]
            if item[0] == 'extension_offset': object.extensionOffset = item[1]
        return object

    def to_sexpr(self, indent: int = 4, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 4.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        extension_height = f' (extension_height {self.extensionHeight})' if self.extensionHeight is not None else ''
        text_frame = f' (text_frame {self.textFrame})' if self.textFrame is not None else ''
        extension_offset = f' (extension_offset {self.extensionOffset})' if self.extensionOffset is not None else ''
        keep_aligned = f' keep_text_aligned' if self.keepTextAligned else ''

        expression =  f'{indents}(style (thickness {self.thickness}) (arrow_length {self.arrowLength}) (text_position_mode {self.textPositionMode}){extension_height}{text_frame}{extension_offset}{keep_aligned}){endline}'
        return expression

@dataclass
class Dimension():
    """The ``dimension`` token defines a dimension in the PCB

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_dimension
    """

    locked: bool = False
    """The optional ``locked`` token specifies if the dimension can be moved"""

    type: str = "aligned"
    """The ``type`` token defines the type of dimension. Valid dimension types are ``aligned``,
    ``leader``, ``center``, ``orthogonal`` (and ``radial`` in KiCad version 7)"""

    layer: str = "F.Cu"
    """The ``layer`` token defines the canonical layer the polygon resides on"""

    tstamp: Optional[str] = None
    """The ``tstamp`` token defines the unique identifier for the footprint. This only applies
    to footprints defined in the board file format."""

    pts: List[Position] = field(default_factory=list)
    """The ``pts`` token define the list of xy coordinates of the dimension"""

    height: Optional[float] = None
    """The optional ``height`` token defines the height of aligned dimensions"""

    orientation: Optional[float] = None
    """The optional ``orientation`` token defines the rotation angle for orthogonal dimensions"""

    leaderLength: Optional[float] = None
    """The optional ``leaderLength`` token attribute defines the distance from the marked radius to
    the knee for radial dimensions."""

    grText: Optional[GrText] = None
    """The optional ``grText`` token define the dimension text formatting for all dimension types
    except center dimensions"""

    format: Optional[DimensionFormat] = None
    """The optional ``format`` token define the dimension formatting for all dimension types except
    center dimensions"""

    style: DimensionStyle = field(default_factory=lambda: DimensionStyle())
    """The ``style`` token defines the dimension style information"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Dimension:
        """Convert the given S-Expresstion into a Dimension object

        Args:
            - exp (list): Part of parsed S-Expression ``(dimension ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not dimension

        Returns:
            - Dimension: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'dimension':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp[1:]:
            if type(item) != type([]):
                if item == 'locked': object.locked = True
                continue
            if item[0] == 'type': object.type = item[1]
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'tstamp': object.tstamp = item[1]
            if item[0] == 'height': object.height = item[1]
            if item[0] == 'orientation': object.orientation = item[1]
            if item[0] == 'leader_length': object.leaderLength = item[1]
            if item[0] == 'gr_text': object.grText = GrText().from_sexpr(item)
            if item[0] == 'format': object.format = DimensionFormat().from_sexpr(item)
            if item[0] == 'style': object.style = DimensionStyle().from_sexpr(item)
            if item[0] == 'pts':
                for point in item[1:]:
                    object.pts.append(Position().from_sexpr(point))

        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Raises:
            - Exception: When number of coordinate points of the dimension equals 0

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        points = ''
        for point in self.pts:
            points = f'{points} (xy {point.X} {point.Y})'
        if len(points) == 0:
            raise Exception("Number of points must not be zero")

        expression =   f'{indents}(dimension (type {self.type}) (layer "{self.layer}") (tstamp {self.tstamp})\n'
        expression +=  f'{indents}  (pts{points})\n'
        if self.height is not None:
            expression +=  f'{indents}  (height {self.height})\n'
        if self.orientation is not None:
            expression +=  f'{indents}  (orientation {self.orientation})\n'
        if self.leaderLength is not None:
            expression +=  f'{indents}  (leader_length {self.leaderLength})\n'
        if self.grText is not None:
            expression += self.grText.to_sexpr(indent+2)
        if self.format is not None:
            expression += self.format.to_sexpr(indent+2)
        expression += self.style.to_sexpr(indent+2)
        expression +=  f'{indents}){endline}'
        return expression