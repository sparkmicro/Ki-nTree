"""The graphical items are footprint and board items that are outside of the connectivity items.
   This includes graphical items on technical, user, and copper layers. Graphical items are also
   used to define complex pad geometries.

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    10.02.2022 - created

Documentation taken from:
    https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphic_items
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List

from kiutils.items.common import Effects, Position, Stroke
from kiutils.utils.strings import dequote

@dataclass
class GrText():
    """The ``gr_text`` token defines a graphical text.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_text
    """

    text: str = ""
    """The ``text`` attribute is a string that defines the text"""

    position: Position = field(default_factory=lambda: Position())
    """The ``position`` defines the X and Y position coordinates and optional orientation angle of the text"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the text resides on"""

    effects: Effects = field(default_factory=lambda: Effects())
    """The ``effects`` token defines how the text is displayed"""

    tstamp: Optional[str] = None      # Used since KiCad 6
    """The ``tstamp`` token defines the unique identifier of the text object"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrText:
        """Convert the given S-Expresstion into a GrText object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_text ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_text

        Returns:
            - GrText: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_text':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.text = exp[1]
        for item in exp[2:]:
            if type(item) != type([]):
                if item == 'locked': object.locked = True
                continue
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'effects': object.effects = Effects().from_sexpr(item)
            if item[0] == 'tstamp': object.tstamp = item[1]
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

        posA = f' {self.position.angle}' if self.position.angle is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        tstamp = f' (tstamp {self.tstamp})' if self.tstamp is not None else ''
        locked = f' locked' if self.locked else ''

        expression =  f'{indents}(gr_text{locked} "{dequote(self.text)}" (at {self.position.X} {self.position.Y}{posA}){layer}{tstamp}\n'
        expression += f'{indents}  {self.effects.to_sexpr()}'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class GrTextBox():
    """TBD when KiCad 7 is released

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_text_box
    """

    locked: bool = False
    text: str = "text"
    start: Optional[Position] = None
    end: Optional[Position] = None
    pts: List[Position] = field(default_factory=list)
    angle: Optional[float] = None
    layer: str = "F.Cu"
    tstamp: Optional[str] = None
    effects: Effects = field(default_factory=lambda: Effects())
    stroke: Stroke = field(default_factory=lambda: Stroke())
    renderCache: Optional[str] = None

    @classmethod
    def from_sexpr(cls, exp: list) -> GrTextBox:
        """Not implemented yet"""
        raise NotImplementedError("GrTextBoxes are not yet handled! Please report this bug along with the file being parsed.")

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Not implemented yet"""
        raise NotImplementedError("GrTextBoxes are not yet handled! Please report this bug along with the file being parsed.")

@dataclass
class GrLine():
    """The ``gr_line`` token defines a graphical line.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_line
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the start of the line"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the end of the line"""

    angle: Optional[float] = None
    """The optional ``angle`` token defines the rotational angle of the line"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the rectangle resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the rectangle. (prior to version 7)"""

    tstamp: Optional[str] = None      # Used since KiCad 6
    """The ``tstamp`` token defines the unique identifier of the rectangle object"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrLine:
        """Convert the given S-Expresstion into a GrLine object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_line ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_line

        Returns:
            - GrLine: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_line':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if type(item) != type([]):
                if item == 'locked': object.locked = True
                continue
            if item[0] == 'start': object.start = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'tstamp': object.tstamp = item[1]
            if item[0] == 'width': object.width = item[1]
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
        locked = f' locked' if self.locked else ''

        tstamp = f' (tstamp {self.tstamp})' if self.tstamp is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        angle = f' (angle {self.angle}' if self.angle is not None else ''

        return f'{indents}(gr_line{locked} (start {self.start.X} {self.start.Y}) (end {self.end.X} {self.end.Y}){angle}{layer} (width {self.width}){tstamp}){endline}'

@dataclass
class GrRect():
    """The ``gr_rect`` token defines a graphical rectangle.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_rectangle
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the upper left corner of the rectangle"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the low right corner of the rectangle"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the rectangle resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the rectangle. (prior to version 7)"""

    fill: Optional[str] = None
    """The optional ``fill`` toke defines how the rectangle is filled. Valid fill types are solid and none. If not defined, the rectangle is not filled"""

    tstamp: Optional[str] = None      # Used since KiCad 6
    """The ``tstamp`` token defines the unique identifier of the rectangle object"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrRect:
        """Convert the given S-Expresstion into a GrRect object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_rect ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_rect

        Returns:
            - GrRect: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_rect':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if type(item) != type([]):
                if item == 'locked': object.locked = True
                continue
            if item[0] == 'start': object.start = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'tstamp': object.tstamp = item[1]
            if item[0] == 'fill': object.fill = item[1]
            if item[0] == 'width': object.width = item[1]
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
        locked = f' locked' if self.locked else ''

        tstamp = f' (tstamp {self.tstamp})' if self.tstamp is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        fill = f' (fill {self.fill})' if self.fill is not None else ''

        return f'{indents}(gr_rect{locked} (start {self.start.X} {self.start.Y}) (end {self.end.X} {self.end.Y}){layer} (width {self.width}){fill}{tstamp}){endline}'

@dataclass
class GrCircle():
    """The ``gr_circle `` token defines a graphical circle.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_circle
    """

    center: Position = field(default_factory=lambda: Position())
    """The ``center`` token defines the coordinates of the center of the circle"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the low right corner of the circle"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the circle resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the circle. (prior to version 7)"""

    fill: Optional[str] = None
    """The optional ``fill`` toke defines how the circle is filled. Valid fill types are solid and none. If not defined, the rectangle is not filled"""

    tstamp: Optional[str] = None      # Used since KiCad 6
    """The ``tstamp`` token defines the unique identifier of the circle object"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrCircle:
        """Convert the given S-Expresstion into a GrCircle object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_circle ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_circle

        Returns:
            - GrCircle: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_circle':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if type(item) != type([]):
                if item == 'locked': object.locked = True
                continue
            if item[0] == 'center': object.center = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'tstamp': object.tstamp = item[1]
            if item[0] == 'fill': object.fill = item[1]
            if item[0] == 'width': object.width = item[1]

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
        locked = f' locked' if self.locked else ''

        tstamp = f' (tstamp {self.tstamp})' if self.tstamp is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        fill = f' (fill {self.fill})' if self.fill is not None else ''

        return f'{indents}(gr_circle{locked} (center {self.center.X} {self.center.Y}) (end {self.end.X} {self.end.Y}){layer} (width {self.width}){fill}{tstamp}){endline}'

@dataclass
class GrArc():
    """The ``gr_arc`` token defines a graphic arc.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_arc
    """

    start: Position = field(default_factory=lambda: Position())
    """The ``start`` token defines the coordinates of the start position of the arc radius"""

    mid: Position = field(default_factory=lambda: Position())
    """The ``mid`` token defines the coordinates of the midpoint along the arc"""

    end: Position = field(default_factory=lambda: Position())
    """The ``end`` token defines the coordinates of the end position of the arc radius"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the arc resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the arc. (prior to version 7)"""

    tstamp: Optional[str] = None      # Used since KiCad 6
    """The ``tstamp`` token defines the unique identifier of the arc object."""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrArc:
        """Convert the given S-Expresstion into a GrArc object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_arc ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_arc

        Returns:
            - GrArc: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_arc':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if type(item) != type([]):
                if item == 'locked': object.locked = True
                continue
            if item[0] == 'start': object.start = Position.from_sexpr(item)
            if item[0] == 'mid': object.mid = Position.from_sexpr(item)
            if item[0] == 'end': object.end = Position.from_sexpr(item)
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'tstamp': object.tstamp = item[1]
            if item[0] == 'width': object.width = item[1]

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
        locked = f' locked' if self.locked else ''

        tstamp = f' (tstamp {self.tstamp})' if self.tstamp is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''

        return f'{indents}(gr_arc{locked} (start {self.start.X} {self.start.Y}) (mid {self.mid.X} {self.mid.Y}) (end {self.end.X} {self.end.Y}){layer} (width {self.width}){tstamp}){endline}'

@dataclass
class GrPoly():
    """The ``gr_poly`` token defines a graphic polygon in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_polygon
    """

    layer: Optional[str] = None
    """The ``coordinates`` define the list of X/Y coordinates of the polygon outline"""

    coordinates: List[Position] = field(default_factory=list)
    """The ``layer`` token defines the canonical layer the polygon resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the polygon. (prior to version 7)"""

    fill: Optional[str] = None
    """The optional ``fill`` toke defines how the polygon is filled. Valid fill types are solid and none. If not defined, the rectangle is not filled"""

    tstamp: Optional[str] = None      # Used since KiCad 6
    """The ``tstamp`` token defines the unique identifier of the polygon object"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrPoly:
        """Convert the given S-Expresstion into a GrPoly object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_poly ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_poly

        Returns:
            - GrPoly: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_poly':
            raise Exception("Expression does not have the correct type")

        object = cls()

        for item in exp:
            if type(item) != type([]):
                if item == 'locked': object.locked = True
                continue
            if item[0] == 'pts':
                for point in item[1:]:
                    object.coordinates.append(Position().from_sexpr(point))
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'tstamp': object.tstamp = item[1]
            if item[0] == 'fill': object.fill = item[1]
            if item[0] == 'width': object.width = item[1]

        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True, pts_newline: bool = False) -> str:
        """Generate the S-Expression representing this object. When no coordinates are set
        in the polygon, the resulting S-Expression will be left empty.

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.
            - pts_newline (bool): Adds a newline for the ``(pts ..)`` token as KiCad treats
                                  this different in Board files than Footprint files. Defaults to 
                                  False.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        if len(self.coordinates) == 0:
            return f'{indents}{endline}'

        tstamp = f' (tstamp {self.tstamp})' if self.tstamp is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        fill = f' (fill {self.fill})' if self.fill is not None else ''
        locked = f' locked' if self.locked else ''

        if pts_newline:
            expression =  f'{indents}(gr_poly{locked}\n'
            expression += f'{indents}  (pts\n'
        else:
            expression =  f'{indents}(gr_poly{locked} (pts\n'

        for point in self.coordinates:
            expression += f'{indents}    (xy {point.X} {point.Y})\n'
        expression += f'{indents}  ){layer} (width {self.width}){fill}{tstamp}){endline}'
        return expression

@dataclass
class GrCurve():
    """The ``gr_curve`` token defines a graphic Cubic Bezier curve in a footprint definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_graphical_curve
    """
    coordinates: List[Position] = field(default_factory=list)
    """The ``coordinates`` define the list of X/Y coordinates of the curve outline"""

    layer: Optional[str] = None
    """The ``layer`` token defines the canonical layer the curve resides on"""

    width: Optional[float] = 0.12     # Used for KiCad < 7
    """The ``width`` token defines the line width of the curve. (prior to version 7)"""

    tstamp: Optional[str] = None      # Used since KiCad 6
    """The ``tstamp`` token defines the unique identifier of the curve object"""

    locked: bool = False
    """The ``locked`` token defines if the object may be moved or not"""

    @classmethod
    def from_sexpr(cls, exp: list) -> GrCurve:
        """Convert the given S-Expresstion into a GrCurve object

        Args:
            - exp (list): Part of parsed S-Expression ``(gr_curve ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not gr_curve

        Returns:
            - GrCurve: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'gr_curve':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if type(item) != type([]):
                if item == 'locked': object.locked = True
                continue
            if item[0] == 'pts':
                for point in item[1:]:
                    object.coordinates.append(Position().from_sexpr(point))
            if item[0] == 'layer': object.layer = item[1]
            if item[0] == 'tstamp': object.tstamp = item[1]
            if item[0] == 'width': object.width = item[1]

        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object. When no coordinates are set
        in the curve, the resulting S-Expression will be left empty.

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        if len(self.coordinates) == 0:
            return f'{indents}{endline}'

        tstamp = f' (tstamp {self.tstamp})' if self.tstamp is not None else ''
        layer =  f' (layer "{dequote(self.layer)}")' if self.layer is not None else ''
        locked = f' locked' if self.locked else ''

        expression = f'{indents}(gr_curve{locked} (pts\n'
        for point in self.coordinates:
            expression += f'{indents}  (xy {point.X} {point.Y})\n'
        expression += f'{indents}){layer} (width {self.width}{tstamp}){endline}'
        return expression
