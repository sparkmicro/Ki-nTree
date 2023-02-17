"""Defines items used in KiCad schematic files

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
from typing import Optional, List, Dict

from kiutils.items.common import Position, ColorRGBA, Stroke, Effects, Property
from kiutils.utils.strings import dequote

@dataclass
class Junction():
    """The ``junction`` token defines a junction in the schematic

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_junction_section
    """

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y coordinates of the junction"""

    diameter: float = 0
    """The ``diameter`` token attribute defines the DIAMETER of the junction. A diameter of 0
       is the default diameter in the system settings."""

    color: ColorRGBA = field(default_factory=lambda: ColorRGBA())
    """The ``color`` token attributes define the Red, Green, Blue, and Alpha transparency of
       the junction. If all four attributes are 0, the default junction color is used."""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Junction:
        """Convert the given S-Expresstion into a Junction object

        Args:
            - exp (list): Part of parsed S-Expression ``(junction ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not junction

        Returns:
            - Junction: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'junction':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'color': object.color = ColorRGBA().from_sexpr(item)
            if item[0] == 'diameter': object.color = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
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

        expression =  f'{indents}(junction (at {self.position.X} {self.position.Y}) (diameter {self.diameter}) {self.color.to_sexpr()}\n'
        expression += f'{indents}  (uuid {self.uuid})\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class NoConnect():
    """The ``no_connect`` token defines a unused pin connection in the schematic

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_no_connect_section
    """

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y coordinates of the no connect"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> NoConnect:
        """Convert the given S-Expresstion into a NoConnect object

        Args:
            - exp (list): Part of parsed S-Expression ``(no_connect ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not no_connect

        Returns:
            - NoConnect: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'no_connect':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'uuid': object.uuid = item[1]
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

        return f'{indents}(no_connect (at {self.position.X} {self.position.Y}) (uuid {self.uuid})){endline}'

@dataclass
class BusEntry():
    """The ``bus_entry`` token defines a bus entry in the schematic

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_bus_entry_section
    """

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y coordinates of the bus entry"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    size: Position = field(default_factory=lambda: Position())         # Re-using Position class here
    """The ``size`` token attributes define the X and Y distance of the end point from
       the position of the bus entry"""

    stroke: Stroke = field(default_factory=lambda: Stroke())
    """The ``stroke`` defines how the bus entry is drawn"""

    @classmethod
    def from_sexpr(cls, exp: list) -> BusEntry:
        """Convert the given S-Expresstion into a BusEntry object

        Args:
            - exp (list): Part of parsed S-Expression ``(bus_entry ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not bus_entry

        Returns:
            - BusEntry: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'bus_entry':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'stroke': object.stroke = Stroke().from_sexpr(item)
            if item[0] == 'size': object.size = Position().from_sexpr(item)
            if item[0] == 'uuid': object.uuid = item[1]
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

        expression =  f'{indents}(bus_entry (at {self.position.X} {self.position.Y}) (size {self.size.X} {self.size.Y})\n'
        expression += self.stroke.to_sexpr(indent+2)
        expression += f'{indents}  (uuid {self.uuid})\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class Connection():
    """The ``wire`` and ``bus`` tokens define wires and buses in the schematic

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_wire_and_bus_section
    """

    type: str = "wire"
    """The ``type`` token defines wether the connection is a ``bus`` or a ``wire``"""

    points: List[Position] = field(default_factory=list)
    """The ``points`` token defines the list of X and Y coordinates of start and end points
       of the wire or bus"""

    stroke: Stroke = field(default_factory=lambda: Stroke())
    """The ``stroke`` defines how the connection is drawn"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Connection:
        """Convert the given S-Expresstion into a Connection object

        Args:
            - exp (list): Part of parsed S-Expression ``(wire ...)`` or ``(bus ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not wire or bus

        Returns:
            - Connection: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if not (exp[0] == 'wire' or exp[0] == 'bus'):
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.type = exp[0]
        for item in exp:
            if item[0] == 'pts':
                for point in item[1:]:
                    object.points.append(Position().from_sexpr(point))
            if item[0] == 'stroke': object.stroke = Stroke().from_sexpr(item)
            if item[0] == 'uuid': object.uuid = item[1]
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

        points = ''
        for point in self.points:
            points += f' (xy {point.X} {point.Y})'

        expression =  f'{indents}({self.type} (pts{points})\n'
        expression += self.stroke.to_sexpr(indent+2)
        expression += f'{indents}  (uuid {self.uuid})\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class Image():
    """The ``image`` token defines on or more embedded images in a schematic

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_image_section
    """

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y coordinates of the image"""

    scale: Optional[float] = None
    """The optional ``scale`` token attribute defines the scale factor (size) of the image"""

    data: List[str] = field(default_factory=list)
    """The ``data`` token attribute defines the image data in the portable network graphics
       format (PNG) encoded with MIME type base64 as a list of strings"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Image:
        """Convert the given S-Expresstion into a Image object

        Args:
            - exp (list): Part of parsed S-Expression ``(image ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not image

        Returns:
            - Image: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'image':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'scale': object.scale = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'data':
                for b64part in item[1:]:
                    object.data.append(b64part)
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

        scale = f' (scale {self.scale})' if self.scale is not None else ''

        expression =  f'{indents}(image (at {self.position.X} {self.position.Y}){scale}\n'
        expression += f'{indents}  (uuid {self.uuid})\n'
        expression += f'{indents}  (data\n'
        for b64part in self.data:
            expression += f'{indents}    {b64part}\n'
        expression += f'{indents}  )\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class PolyLine():
    """The ``polyline`` token defines one or more lines that may or may not represent a polygon

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_graphical_line_section
    """

    points: List[Position] = field(default_factory=list)
    """The ``points`` token defines the list of X/Y coordinates of to draw line(s)
       between. A minimum of two points is required."""

    stroke: Stroke = field(default_factory=lambda: Stroke())
    """The ``stroke`` defines how the graphical line is drawn"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> PolyLine:
        """Convert the given S-Expresstion into a PolyLine object

        Args:
            - exp (list): Part of parsed S-Expression ``(polyline ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not polyline

        Returns:
            - PolyLine: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'polyline':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'pts':
                for point in item[1:]:
                    object.points.append(Position().from_sexpr(point))
            if item[0] == 'stroke': object.stroke = Stroke().from_sexpr(item)
            if item[0] == 'uuid': object.uuid = item[1]
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

        points = ''
        for point in self.points:
            points += f' (xy {point.X} {point.Y})'

        expression =  f'{indents}(polyline (pts{points})\n'
        expression += self.stroke.to_sexpr(indent+2)
        expression += f'{indents}  (uuid {self.uuid})\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class Text():
    """The ``text`` token defines graphical text in a schematic

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_graphical_text_section
    """

    text: str = ""
    """The ``text`` token defines the text string"""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` token defines the X and Y coordinates and rotation angle of the text"""

    effects: Effects = field(default_factory=lambda: Effects())
    """The ``effects`` token defines how the text is drawn"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Text:
        """Convert the given S-Expresstion into a Text object

        Args:
            - exp (list): Part of parsed S-Expression ``(text ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not text

        Returns:
            - Text: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'text':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.text = exp[1]
        for item in exp[2:]:
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'effects': object.effects = Effects().from_sexpr(item)
            if item[0] == 'uuid': object.uuid = item[1]
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

        posA = f' {self.position.angle}' if self.position.angle is not None else ''

        expression =  f'{indents}(text "{dequote(self.text)}"'

        # Strings longer or equal than 50 chars have the position in the next line
        if len(self.text) >= 50:
            expression += f'\n{indents}  '
        else:
            expression += ' '
        expression += f'(at {self.position.X} {self.position.Y}{posA})\n'
        expression += self.effects.to_sexpr(indent+2)
        expression += f'{indents}  (uuid {self.uuid})\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class LocalLabel():
    """The ``label`` token defines an wire or bus label name in a schematic

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#local_label_section
    """

    text: str = ""
    """The ``text`` token defines the text in the label"""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` token defines the X and Y coordinates and rotation angle of the label"""

    effects: Effects = field(default_factory=lambda: Effects())
    """The ``effects`` token defines how the label is drawn"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> LocalLabel:
        """Convert the given S-Expresstion into a LocalLabel object

        Args:
            - exp (list): Part of parsed S-Expression ``(label ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not label

        Returns:
            - LocalLabel: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'label':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.text = exp[1]
        for item in exp[2:]:
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'effects': object.effects = Effects().from_sexpr(item)
            if item[0] == 'uuid': object.uuid = item[1]
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

        posA = f' {self.position.angle}' if self.position.angle is not None else ''

        expression =  f'{indents}(label "{dequote(self.text)}" (at {self.position.X} {self.position.Y}{posA})\n'
        expression += self.effects.to_sexpr(indent+2)
        expression += f'{indents}  (uuid {self.uuid})\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class GlobalLabel():
    """The ``global_label`` token defines a label name that is visible across all schematics in a design

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_global_label_section
    """

    text: str = ""
    """The ``text`` token defines the text in the label"""

    shape: str = "input"
    """The ``shape`` token defines the way the global label is drawn. Possible values are:
       ``input``, ``output``, ``bidirectional``, ``tri_state``, ``passive``."""

    fieldsAutoplaced: bool = False
    """The ``fields_autoplaced`` is a flag that indicates that any PROPERTIES associated
       with the global label have been place automatically"""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` token defines the X and Y coordinates and rotation angle of the label"""

    effects: Effects = field(default_factory=lambda: Effects())
    """The ``effects`` token defines how the label is drawn"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    properties: List[Property] = field(default_factory=list)
    """	The ``properties`` token defines a list of properties of the global label. Currently, the
    only supported property is the inter-sheet reference"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GlobalLabel:
        """Convert the given S-Expresstion into a GlobalLabel object

        Args:
            - exp (list): Part of parsed S-Expression ``(global_label ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not global_label

        Returns:
            - GlobalLabel: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'global_label':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.text = exp[1]
        for item in exp[2:]:
            if item[0] == 'fields_autoplaced': object.fieldsAutoplaced = True
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'effects': object.effects = Effects().from_sexpr(item)
            if item[0] == 'property': object.properties.append(Property().from_sexpr(item))
            if item[0] == 'shape': object.shape = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
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

        posA = f' {self.position.angle}' if self.position.angle is not None else ''
        fa = ' (fields_autoplaced)' if self.fieldsAutoplaced else ''

        expression =  f'{indents}(global_label "{dequote(self.text)}" (shape {self.shape}) (at {self.position.X} {self.position.Y}{posA}){fa}\n'
        expression += self.effects.to_sexpr(indent+2)
        expression += f'{indents}  (uuid {self.uuid})\n'
        for property in self.properties:
            expression += property.to_sexpr(indent+2)
        expression += f'{indents}){endline}'
        return expression

@dataclass
class HierarchicalLabel():
    """The ``hierarchical_label`` token defines a label that are used by hierarchical sheets to
    define connections between sheet in hierarchical designs

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_hierarchical_label_section
    """

    text: str = ""
    """The ``text`` token defines the text in the label"""

    shape: str = "input"
    """The ``shape`` token defines the way the global label is drawn. Possible values are:
       ``input``, ``output``, ``bidirectional``, ``tri_state``, ``passive``."""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` token defines the X and Y coordinates and rotation angle of the label"""

    effects: Effects = field(default_factory=lambda: Effects())
    """The ``effects`` token defines how the label is drawn"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> HierarchicalLabel:
        """Convert the given S-Expresstion into a HierarchicalLabel object

        Args:
            - exp (list): Part of parsed S-Expression ``(hierarchical_label ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not hierarchical_label

        Returns:
            - HierarchicalLabel: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'hierarchical_label':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.text = exp[1]
        for item in exp[2:]:
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'effects': object.effects = Effects().from_sexpr(item)
            if item[0] == 'shape': object.shape = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
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

        posA = f' {self.position.angle}' if self.position.angle is not None else ''

        expression =  f'{indents}(hierarchical_label "{dequote(self.text)}" (shape {self.shape}) (at {self.position.X} {self.position.Y}{posA})\n'
        expression += self.effects.to_sexpr(indent+2)
        expression += f'{indents}  (uuid {self.uuid})\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class SchematicSymbol():
    """The ``symbol`` token in the symbol section of the schematic defines an instance of a symbol
       from the library symbol section of the schematic

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_symbol_section
    """

    libraryIdentifier: str = ""
    """The ``libraryIdentifier`` defines which symbol in the library symbol section of the schematic
       that this schematic symbol references"""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y coordinates and angle of rotation of the symbol"""

    unit: Optional[int] = None
    """The optional ``unit`` token attribute defines which unit in the symbol library definition that the
       schematic symbol represents"""

    inBom: bool = False
    """The ``in_bom`` token attribute determines whether the schematic symbol appears in any bill
       of materials output"""

    onBoard: bool = False
    """The on_board token attribute determines if the footprint associated with the symbol is
       exported to the board via the netlist"""

    fieldsAutoplaced: bool = False
    """The ``fields_autoplaced`` is a flag that indicates that any PROPERTIES associated
       with the global label have been place automatically"""

    uuid: Optional[str] = ""
    """The optional `uuid` defines the universally unique identifier"""

    properties: List[Property] = field(default_factory=list)
    """The ``properties`` section defines a list of symbol properties of the schematic symbol"""

    pins: Dict[str, str] = field(default_factory=dict)
    """The ``pins`` token defines a dictionary with pin numbers in form of strings as keys and
       uuid's as values"""

    mirror: Optional[str] = None
    """The ``mirror`` token defines if the symbol is mirrored in the schematic. Accepted values: ``x`` or ``y``.
    When mirroring around the x and y axis at the same time use some additional rotation to get the correct
    orientation of the symbol."""

    @classmethod
    def from_sexpr(cls, exp: list) -> SchematicSymbol:
        """Convert the given S-Expresstion into a SchematicSymbol object

        Args:
            - exp (list): Part of parsed S-Expression ``(symbol ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not symbol

        Returns:
            - SchematicSymbol: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'symbol':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp[1:]:
            if item[0] == 'fields_autoplaced': object.fieldsAutoplaced = True
            if item[0] == 'lib_id': object.libraryIdentifier = item[1]
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'unit': object.unit = item[1]
            if item[0] == 'in_bom': object.inBom = True if item[1] == 'yes' else False
            if item[0] == 'on_board': object.onBoard = True if item[1] == 'yes' else False
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'property': object.properties.append(Property().from_sexpr(item))
            if item[0] == 'pin': object.pins.update({item[1]: item[2][1]})
            if item[0] == 'mirror': object.mirror = item[1]
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

        posA = f' {self.position.angle}' if self.position.angle is not None else ''
        fa = f' (fields_autoplaced)' if self.fieldsAutoplaced else ''
        inBom = 'yes' if self.inBom else 'no'
        onBoard = 'yes' if self.onBoard else 'no'
        mirror = f' (mirror {self.mirror})' if self.mirror is not None else ''
        unit = f' (unit {self.unit})' if self.unit is not None else ''

        expression =  f'{indents}(symbol (lib_id "{dequote(self.libraryIdentifier)}") (at {self.position.X} {self.position.Y}{posA}){mirror}{unit}\n'
        expression += f'{indents}  (in_bom {inBom}) (on_board {onBoard}){fa}\n'
        if self.uuid:
            expression += f'{indents}  (uuid {self.uuid})\n'
        for property in self.properties:
            expression += property.to_sexpr(indent+2)
        for number, uuid in self.pins.items():
            expression += f'{indents}  (pin "{dequote(number)}" (uuid {uuid}))\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class HierarchicalPin():
    """The ``pin`` token in a sheet object defines an electrical connection between the sheet in a
       schematic with the hierarchical label defined in the associated schematic file

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_hierarchical_sheet_pin_definition
    """

    name: str = ""
    """	The ``name`` attribute defines the name of the sheet pin. It must have an identically named
        hierarchical label in the associated schematic file."""

    connectionType: str = "input"
    """The electrical connect type token defines the type of electrical connect made by the
       sheet pin"""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y coordinates and angle of rotation of the pin"""

    effects: Effects = field(default_factory=lambda: Effects())
    """The ``effects`` section defines how the pin name text is drawn"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    @classmethod
    def from_sexpr(cls, exp: list) -> HierarchicalPin:
        """Convert the given S-Expresstion into a HierarchicalPin object

        Args:
            - exp (list): Part of parsed S-Expression ``(pin ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not pin

        Returns:
            - HierarchicalPin: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'pin':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.name = exp[1]
        object.connectionType = exp[2]
        for item in exp[3:]:
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'effects': object.effects = Effects().from_sexpr(item)
            if item[0] == 'uuid': object.uuid = item[1]
        return object

    def to_sexpr(self, indent=4, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 4.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        posA = f' {self.position.angle}' if self.position.angle is not None else ''

        expression =  f'{indents}(pin "{dequote(self.name)}" {self.connectionType} (at {self.position.X} {self.position.Y}{posA})\n'
        expression += self.effects.to_sexpr(indent+2)
        expression += f'{indents}  (uuid {self.uuid})\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class HierarchicalSheet():
    """The ``sheet`` token defines a hierarchical sheet of the schematic

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_hierarchical_sheet_section
    """

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y coordinates and angle of rotation of the sheet in the schematic"""

    width: float = 0
    """The ``width`` token defines the width of the sheet"""

    height: float = 0
    """The ``height`` token defines the height of the sheet"""

    fieldsAutoplaced: bool = False
    """The ``fields_autoplaced`` is a flag that indicates that any PROPERTIES associated
       with the global label have been place automatically"""

    stroke: Stroke = field(default_factory=lambda: Stroke())
    """The ``stroke`` defines how the sheet outline is drawn"""

    fill: ColorRGBA = field(default_factory=lambda: ColorRGBA())
    """The fill defines the color how the sheet is filled"""

    uuid: str = ""
    """The ``uuid`` defines the universally unique identifier"""

    sheetName: Property = field(default_factory=lambda: Property(key="Sheet name"))
    """The ``sheetName`` is a property that defines the name of the sheet. The property's
       key should therefore be set to `Sheet name`"""

    fileName: Property = field(default_factory=lambda: Property(key="Sheet file"))
    """The ``fileName`` is a property that defines the file name of the sheet. The property's
       key should therefore be set to `Sheet file`"""

    pins: List[HierarchicalPin] = field(default_factory=list)
    """The ``pins`` section is a list of hierarchical pins that map a hierarchical label defined in
       the associated schematic file"""

    @classmethod
    def from_sexpr(cls, exp: list) -> HierarchicalSheet:
        """Convert the given S-Expresstion into a HierarchicalSheet object

        Args:
            - exp (list): Part of parsed S-Expression ``(sheet ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not sheet

        Returns:
            - HierarchicalSheet: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'sheet':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp[1:]:
            if item[0] == 'fields_autoplaced': object.fieldsAutoplaced = True
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'stroke': object.stroke = Stroke().from_sexpr(item)
            if item[0] == 'size':
                object.width = item[1]
                object.height = item[2]
            if item[0] == 'fill':
                object.fill = ColorRGBA().from_sexpr(item[1])
                object.fill.precision = 4
            if item[0] == 'uuid': object.uuid = item[1]
            if item[0] == 'property':
                if item[1] == 'Sheet name': object.sheetName = Property().from_sexpr(item)
                if item[1] == 'Sheet file': object.fileName = Property().from_sexpr(item)
            if item[0] == 'pin': object.pins.append(HierarchicalPin().from_sexpr(item))
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

        fa = ' (fields_autoplaced)' if self.fieldsAutoplaced else ''

        expression =  f'{indents}(sheet (at {self.position.X} {self.position.Y}) (size {self.width} {self.height}){fa}\n'
        expression += self.stroke.to_sexpr(indent+2)
        expression += f'{indents}  (fill {self.fill.to_sexpr()})\n'
        expression += f'{indents}  (uuid {self.uuid})\n'
        expression += self.sheetName.to_sexpr(indent+2)
        expression += self.fileName.to_sexpr(indent+2)
        for pin in self.pins:
            expression += pin.to_sexpr(indent+2)
        expression += f'{indents}){endline}'
        return expression

@dataclass
class HierarchicalSheetInstance():
    """The sheet_instance token defines the per sheet information for the entire schematic. This
       section will only exist in schematic files that are the root sheet of a project

    Documentation:
           https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_hierarchical_sheet_instance_section
    """

    instancePath: str = "/"
    """The ``instancePath`` attribute is the path to the sheet instance"""

    page: str = "1"
    """The ``page`` token defines the page number of the schematic represented by the sheet
       instance information. Page numbers can be any valid string."""

    @classmethod
    def from_sexpr(cls, exp: list) -> HierarchicalSheetInstance:
        """Convert the given S-Expresstion into a HierarchicalSheetInstance object

        Args:
            - exp (list): Part of parsed S-Expression ``(path ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not path

        Returns:
            - HierarchicalSheetInstance: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'path':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.instancePath = exp[1]
        for item in exp[2:]:
            if item[0] == 'page': object.page = item[1]
        return object

    def to_sexpr(self, indent=4, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 4.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        return f'{indents}(path "{dequote(self.instancePath)}" (page "{dequote(self.page)}")){endline}'

@dataclass
class SymbolInstance():
    """The ``symbol_instance`` token defines the per symbol information for the entire schematic

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/#_symbol_instance_section
    """

    path: str = "/"
    """The ``path`` attribute is the path to the sheet instance"""

    reference: str = ""
    """The ``reference`` token attribute is a string that defines the reference designator for
       the symbol instance"""

    unit: int = 0
    """The unit token attribute is a integer ordinal that defines the symbol unit for the
       symbol instance. For symbols that do not define multiple units, this will always be 1."""

    value: str = ""
    """The value token attribute is a string that defines the value field for the symbol instance"""

    footprint: str = ""
    """The ``footprint`` token attribute is a string that defines the LIBRARY_IDENTIFIER for footprint associated with the symbol instance"""

    @classmethod
    def from_sexpr(cls, exp: list) -> SymbolInstance:
        """Convert the given S-Expresstion into a SymbolInstance object

        Args:
            - exp (list): Part of parsed S-Expression ``(path ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not path

        Returns:
            - SymbolInstance: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'path':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.path = exp[1]
        for item in exp[2:]:
            if item[0] == 'reference': object.reference = item[1]
            if item[0] == 'unit': object.unit = item[1]
            if item[0] == 'value': object.value = item[1]
            if item[0] == 'footprint': object.footprint = item[1]
        return object

    def to_sexpr(self, indent=4, newline=True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 4.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        expression =  f'{indents}(path "{dequote(self.path)}"\n'
        expression += f'{indents}  (reference "{dequote(self.reference)}") (unit {self.unit}) (value "{dequote(self.value)}") (footprint "{dequote(self.footprint)}")\n'
        expression += f'{indents}){endline}'
        return expression
