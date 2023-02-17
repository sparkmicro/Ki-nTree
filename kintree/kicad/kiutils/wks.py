"""Classes for worksheets (.kicad_wks) and its contents

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    24.06.2022 - created

Documentation taken from:
    https://dev-docs.kicad.org/en/file-formats/sexpr-worksheet/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List
from os import path

from kiutils.items.common import Justify
from kiutils.utils.strings import dequote
from kiutils.utils import sexpr
from kiutils.misc.config import KIUTILS_CREATE_NEW_GENERATOR_STR, KIUTILS_CREATE_NEW_VERSION_STR

@dataclass
class WksFontSize():
    """The ``WksFontSize`` token defines the size of a font in a worksheet"""

    width: float = 1.0
    """The ``width`` token defines the width of the font. Defaults to 1."""

    height: float = 1.0
    """The ``height`` token defines the height of the font. Defaults to 1."""

    @classmethod
    def from_sexpr(cls, exp: list) -> WksFontSize:
        """Convert the given S-Expresstion into a WksFontSize object

        Args:
            - exp (list): Part of parsed S-Expression ``(size ...)``

        Raises:
            - Exception: When given parameter's type is not a list or its length is not equal to 3
            - Exception: When the first item of the list is not ``size``

        Returns:
            - WksFontSize: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list) or len(exp) != 3:
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'size':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.width = exp[1]
        object.height = exp[2]
        return object

    def to_sexpr(self, indent=0, newline=False):
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        return f'{indents}(size {self.width} {self.height}){endline}'

@dataclass
class WksFont():
    """The ``WksFont`` token defines how a text is drawn"""

    linewidth: Optional[float] = None
    """The optional ``linewidth`` token defines the width of the font's lines"""

    size: Optional[WksFontSize] = None
    """The optional ``size`` token defines the size of the font"""

    bold: bool = False
    """The ``bold`` token defines if the font is drawn bold. Defaults to False."""

    italic: bool = False
    """The ``italic`` token defines if the font is drawn italic. Defaults to False."""

    @classmethod
    def from_sexpr(cls, exp: list) -> WksFont:
        """Convert the given S-Expresstion into a WksFont object

        Args:
            - exp (list): Part of parsed S-Expression ``(font ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not ``font``

        Returns:
            - WksFont: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'font':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if type(item) != type([]):
                if item == 'bold': object.bold = True
                if item == 'italic': object.italic = True
                continue
            if item[0] == 'linewidth': object.linewidth = item[1]
            if item[0] == 'size': object.size = WksFontSize().from_sexpr(item)
        return object

    def to_sexpr(self, indent=0, newline=False):
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object. Will return an empty string, if all members of this
                   class are set to ``None``.
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        lw = f' (linewidth {self.linewidth})' if self.linewidth is not None else ''
        size = f' {self.size.to_sexpr()}' if self.size is not None else ''
        bold = f' bold' if self.bold else ''
        italic = f' italic' if self.italic else ''

        if lw == '' and size == '' and bold == '' and italic == '':
            return ''
        else:
            return f'{indents}(font{lw}{size}{bold}{italic}){endline}'

@dataclass
class WksPosition():
    """The ``WksPosition`` token defines the positional coordinates and rotation of an worksheet
    object.
    """

    X: float = 0.0
    """The ``X`` attribute defines the horizontal position of the object. Defaults to 0."""

    Y: float = 0.0
    """The ``Y`` attribute defines the vertical position of the object. Defaults to 0."""

    corner: Optional[str] = None
    """The optional ``corner`` token is used to define the initial corner for repeating"""

    @classmethod
    def from_sexpr(cls, exp: list) -> WksPosition:
        """Convert the given S-Expresstion into a WksPosition object

        Args:
            - exp (list): Part of parsed S-Expression ``(xxx ...)``

        Raises:
            - Exception: When the given expression is not of type ``list`` or the list is less than
                         3 items long

        Returns:
            - WksPosition: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list) or len(exp) < 3:
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.X = exp[1]
        object.Y = exp[2]

        # The last parameter refers to the corner token, if any is present
        if len(exp) > 3:
            object.corner = exp[3]

        return object

    def to_sexpr(self) -> str:
        """This object does not have a direct S-Expression representation."""
        raise NotImplementedError("This object does not have a direct S-Expression representation")

@dataclass
class Line():
    """The ``Line`` token defines how a line is drawn in a work sheet

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-worksheet/#_graphical_line"""

    name: str = ""
    """The ``name`` token defines the name of the line object"""

    start: WksPosition = field(default_factory=lambda: WksPosition())
    """The ``start`` token defines the start position of the line"""

    end: WksPosition = field(default_factory=lambda: WksPosition())
    """The ``end`` token defines the end position of the line"""

    option: Optional[str] = None
    """The optional ``option`` token defines on which pages the line shall be shown. Possible values
    are:
    - None: Item will be shown on all pages
    - `notonpage1`: On all pages except page 1
    - `page1only`: Only visible on page 1"""

    lineWidth: Optional[float] = None
    """The optional ``lineWidth`` token attribute defines the width of the rectangle lines"""

    repeat: Optional[int] = None
    """The optional ``repeat`` token defines the count for repeated incremental lines"""

    incrx: Optional[float] = None
    """The optional ``incrx`` token defines the repeat distance on the X axis"""

    incry: Optional[float] = None
    """The optional ``incry`` token defines the repeat distance on the Y axis"""

    comment: Optional[str] = None
    """The optional ``comment`` token is a comment for the line object"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Line:
        """Convert the given S-Expresstion into a Line object

        Args:
            - exp (list): Part of parsed S-Expression ``(line ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not ``tbtext``

        Returns:
            - Line: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'line':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp[1:]:
            if item[0] == 'name': object.name = item[1]
            if item[0] == 'start': object.start = WksPosition().from_sexpr(item)
            if item[0] == 'end': object.end = WksPosition().from_sexpr(item)
            if item[0] == 'option': object.option = item[1]
            if item[0] == 'linewidth': object.lineWidth = item[1]
            if item[0] == 'repeat': object.repeat = item[1]
            if item[0] == 'incrx': object.incrx = item[1]
            if item[0] == 'incry': object.incry = item[1]
            if item[0] == 'comment': object.comment = item[1]
        return object

    def to_sexpr(self, indent=2, newline=True):
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        start_corner = f' {self.start.corner}' if self.start.corner is not None else ''
        end_corner = f' {self.end.corner}' if self.end.corner is not None else ''
        option = f' (option {self.option})' if self.option is not None else ''
        repeat = f' (repeat {self.repeat})' if self.repeat is not None else ''
        incrx = f' (incrx {self.incrx})' if self.incrx is not None else ''
        incry = f' (incry {self.incry})' if self.incry is not None else ''
        comment = f' (comment "{dequote(self.comment)}")\n' if self.comment is not None else ''
        lw = f' (linewidth {self.lineWidth})' if self.lineWidth is not None else ''

        expression  = f'{indents}(line (name "{dequote(self.name)}") '
        expression += f'(start {self.start.X} {self.start.Y}{start_corner}) '
        expression += f'(end {self.end.X} {self.end.Y}{end_corner})'
        expression += f'{option}{lw}{repeat}{incrx}{incry}{comment}){endline}'
        return expression

@dataclass
class Rect():
    """The ``Rect`` token defines how a rectangle is drawn in a work sheet

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-worksheet/#_graphical_rectangle"""

    name: str = ""
    """The ``name`` token defines the name of the rectangle object"""

    start: WksPosition = field(default_factory=lambda: WksPosition())
    """The ``start`` token defines the start position of the rectangle"""

    end: WksPosition = field(default_factory=lambda: WksPosition())
    """The ``end`` token defines the end position of the rectangle"""

    option: Optional[str] = None
    """The optional ``option`` token defines on which pages the rectangle shall be shown. Possible values
    are:
    - None: Item will be shown on all pages
    - `notonpage1`: On all pages except page 1
    - `page1only`: Only visible on page 1"""

    lineWidth: Optional[float] = None
    """The optional ``lineWidth`` token attribute defines the width of the rectangle lines"""

    repeat: Optional[int] = None
    """The optional ``repeat`` token defines the count for repeated incremental rectangles"""

    incrx: Optional[float] = None
    """The optional ``incrx`` token defines the repeat distance on the X axis"""

    incry: Optional[float] = None
    """The optional ``incry`` token defines the repeat distance on the Y axis"""

    comment: Optional[str] = None
    """The optional ``comment`` token is a comment for the rectangle object"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Rect:
        """Convert the given S-Expresstion into a Rect object

        Args:
            - exp (list): Part of parsed S-Expression ``(rect ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not ``rect``

        Returns:
            - Rect: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'rect':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp[1:]:
            if item[0] == 'name': object.name = item[1]
            if item[0] == 'start': object.start = WksPosition().from_sexpr(item)
            if item[0] == 'end': object.end = WksPosition().from_sexpr(item)
            if item[0] == 'option': object.option = item[1]
            if item[0] == 'linewidth': object.lineWidth = item[1]
            if item[0] == 'repeat': object.repeat = item[1]
            if item[0] == 'incrx': object.incrx = item[1]
            if item[0] == 'incry': object.incry = item[1]
            if item[0] == 'comment': object.comment = item[1]
        return object

    def to_sexpr(self, indent=2, newline=True):
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        start_corner = f' {self.start.corner}' if self.start.corner is not None else ''
        end_corner = f' {self.end.corner}' if self.end.corner is not None else ''
        option = f' (option {self.option})' if self.option is not None else ''
        repeat = f' (repeat {self.repeat})' if self.repeat is not None else ''
        incrx = f' (incrx {self.incrx})' if self.incrx is not None else ''
        incry = f' (incry {self.incry})' if self.incry is not None else ''
        comment = f' (comment "{dequote(self.comment)}")\n' if self.comment is not None else ''
        lw = f' (linewidth {self.lineWidth})' if self.lineWidth is not None else ''

        expression  = f'{indents}(rect (name "{dequote(self.name)}") '
        expression += f'(start {self.start.X} {self.start.Y}{start_corner}) '
        expression += f'(end {self.end.X} {self.end.Y}{end_corner})'
        expression += f'{option}{lw}{repeat}{incrx}{incry}{comment}){endline}'
        return expression

@dataclass
class Polygon():
    """The ``Polygon`` token defines a graphical polygon in a worksheet

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-worksheet/#_graphical_polygon
    """

    name: str = ""
    """The ``name`` token defines the name of the polygon"""

    position: WksPosition = field(default_factory=lambda: WksPosition())
    """The ``position`` token defines the coordinates of the polygon"""

    option: Optional[str] = None
    """The optional ``option`` token defines on which pages the polygon shall be shown. Possible values
    are:
    - None: Item will be shown on all pages
    - `notonpage1`: On all pages except page 1
    - `page1only`: Only visible on page 1"""

    rotate: Optional[float] = None
    """The optional ``rotate`` token defines the rotation angle of the polygon object"""

    coordinates: List[WksPosition] = field(default_factory=list)
    """The ``coordinates`` token defines a list of X/Y coordinates that forms the polygon"""

    repeat: Optional[int] = None
    """The optional ``repeat`` token defines the count for repeated incremental polygons"""

    incrx: Optional[float] = None
    """The optional ``incrx`` token defines the repeat distance on the X axis"""

    incry: Optional[float] = None
    """The optional ``incry`` token defines the repeat distance on the Y axis"""

    comment: Optional[str] = None
    """The optional ``comment`` token is a comment for the polygon object"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Polygon:
        """Convert the given S-Expresstion into a Polygon object

        Args:
            - exp (list): Part of parsed S-Expression ``(polygon ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not ``polygon``

        Returns:
            - Polygon: Object of the class initialized with the given S-Expression
        """
        # TODO: Polygons seem to not be available in the WKS editor GUI. Are those still a feature?
        raise NotImplementedError("Polygons are not yet handled! Please report this bug along with the file being parsed.")

    def to_sexpr(self, indent=0, newline=False):
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        raise NotImplementedError("Polygons are not yet handled! Please report this bug along with the file being parsed.")

@dataclass
class Bitmap():
    """The ``Polygon`` token defines on or more embedded images

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-worksheet/#_image
    """

    name: str = ""
    """The ``name`` token defines the name of the bitmap"""

    position: WksPosition = field(default_factory=lambda: WksPosition())
    """The ``position`` token defines the coordinates of the bitmap"""

    option: Optional[str] = None
    """The optional ``option`` token defines on which pages the image shall be shown. Possible values
    are:
    - None: Item will be shown on all pages
    - `notonpage1`: On all pages except page 1
    - `page1only`: Only visible on page 1"""

    scale: float = 1.0
    """The ``scale`` token defines the scale of the bitmap object"""

    repeat: Optional[int] = None
    """The optional ``repeat`` token defines the count for repeated incremental bitmaps"""

    incrx: Optional[float] = None
    """The optional ``incrx`` token defines the repeat distance on the X axis"""

    incry: Optional[float] = None
    """The optional ``incry`` token defines the repeat distance on the Y axis"""

    # Comments seem to be buggy as of 25.06.2022 ..
    comment: Optional[str] = None
    """The optional ``comment`` token is a comment for the bitmap object"""

    # TODO: Parse this nonesense as a binary struct to make it more useful
    pngdata: List[str] = field(default_factory=list)
    """The ``pngdata`` token defines a list of strings representing up to 32 bytes per entry of
    the image being saved.

    Format:
    - "xx xx xx xx xx (..) xx "

    The list must be 32byte aligned, leaving a space after the last byte as shown in the format
    example.
    """

    @classmethod
    def from_sexpr(cls, exp: list) -> Bitmap:
        """Convert the given S-Expresstion into a Bitmap object

        Args:
            - exp (list): Part of parsed S-Expression ``(bitmap ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not ``bitmap``

        Returns:
            - Bitmap: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'bitmap':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp[1:]:
            if item[0] == 'name': object.name = item[1]
            if item[0] == 'pos': object.position = WksPosition().from_sexpr(item)
            if item[0] == 'option': object.option = item[1]
            if item[0] == 'scale': object.scale = item[1]
            if item[0] == 'repeat': object.repeat = item[1]
            if item[0] == 'incrx': object.incrx = item[1]
            if item[0] == 'incry': object.incry = item[1]
            if item[0] == 'comment': object.comment = item[1]
            if item[0] == 'pngdata':
                if len(item) < 2: continue
                for data in item[1:]:
                    if data[0] != 'data': continue
                    object.pngdata.append(data[1])
        return object

    def to_sexpr(self, indent=2, newline=True):
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        repeat = f' (repeat {self.repeat})' if self.repeat is not None else ''
        incrx = f' (incrx {self.incrx})' if self.incrx is not None else ''
        incry = f' (incry {self.incry})' if self.incry is not None else ''
        option = f' (option {self.option})' if self.option is not None else ''
        corner = f' {self.position.corner}' if self.position.corner is not None else ''

        expression  = f'{indents}(bitmap (name "{dequote(self.name)}") '
        expression += f'(pos {self.position.X} {self.position.Y}{corner}){option} (scale {self.scale})'
        expression += f'{repeat}{incrx}{incry}\n'
        if self.comment is not None:
            # Here KiCad decides to only use 1 space for some unknown reason ..
            expression += f' (comment "{dequote(self.comment)}")\n'
        expression += f'{indents}(pngdata\n'
        for data in self.pngdata:
            expression += f'{indents}  (data "{data}")\n'
        expression += f'{indents}  )\n'
        expression += f'{indents}){endline}'
        return expression


@dataclass
class TbText():
    """The ``TbText`` token define text used in the title block of a work sheet

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-worksheet/#_title_block_text"""

    text: str = ""
    """The ``text`` token defines the text itself"""

    name: str = ""
    """The ``name`` token defines the name of the text object"""

    position: WksPosition = field(default_factory=lambda: WksPosition())
    """The ``position`` token defines the position of the text"""

    option: Optional[str] = None
    """The optional ``option`` token defines on which pages the text shall be shown. Possible values
    are:
    - None: Item will be shown on all pages
    - `notonpage1`: On all pages except page 1
    - `page1only`: Only visible on page 1"""

    rotate: Optional[float] = None
    """The optional ``rotate`` token defines the rotation of the text in degrees"""

    font: WksFont = field(default_factory=lambda: WksFont())
    """The ``font`` token define how the text is drawn"""

    justify: Optional[Justify] = None
    """The optional ``justify`` token defines the justification of the text"""

    maxlen: Optional[float] = None
    """The optional ``maxlen`` token defines the maximum length of the text"""

    maxheight: Optional[float] = None
    """The optional ``maxheight`` token defines the maximum height of the text"""

    repeat: Optional[int] = None
    """The optional ``repeat`` token defines the count for repeated incremental text"""

    incrx: Optional[float] = None
    """The optional ``incrx`` token defines the repeat distance on the X axis"""

    incry: Optional[float] = None
    """The optional ``incry`` token defines the repeat distance on the Y axis"""

    incrlabel: Optional[int] = None
    """The optional ``incrlabel`` token defines the amount of characters that are moved with every
    repeated incremental text"""

    comment: Optional[str] = None
    """The optional ``comment`` token is a comment for the text object"""

    @classmethod
    def from_sexpr(cls, exp: list) -> TbText:
        """Convert the given S-Expresstion into a TbText object

        Args:
            - exp (list): Part of parsed S-Expression ``(tbtext ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not ``tbtext``

        Returns:
            - TbText: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'tbtext':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.text = exp[1]
        for item in exp[2:]:
            if item[0] == 'name': object.name = item[1]
            if item[0] == 'pos': object.position = WksPosition().from_sexpr(item)
            if item[0] == 'option': object.option = item[1]
            if item[0] == 'rotate': object.rotate = item[1]
            if item[0] == 'font': object.font = WksFont().from_sexpr(item)
            if item[0] == 'justify': object.justify = Justify().from_sexpr(item)
            if item[0] == 'maxlen': object.maxlen = item[1]
            if item[0] == 'maxheight': object.maxheight = item[1]
            if item[0] == 'repeat': object.repeat = item[1]
            if item[0] == 'incrx': object.incrx = item[1]
            if item[0] == 'incry': object.incry = item[1]
            if item[0] == 'incrlabel': object.incrlabel = item[1]
            if item[0] == 'comment': object.comment = item[1]
        return object

    def to_sexpr(self, indent=2, newline=True):
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        corner = f' {self.position.corner}' if self.position.corner is not None else ''
        repeat = f' (repeat {self.repeat})' if self.repeat is not None else ''
        incrx = f' (incrx {self.incrx})' if self.incrx is not None else ''
        incry = f' (incry {self.incry})' if self.incry is not None else ''
        option = f' (option {self.option})' if self.option is not None else ''
        rotate = f' (rotate {self.rotate})' if self.rotate is not None else ''
        justify = f' {self.justify.to_sexpr()}' if self.justify is not None else ''
        maxlen = f' (maxlen {self.maxlen})' if self.maxlen is not None else ''
        maxheight = f' (maxheight {self.maxheight})' if self.maxheight is not None else ''
        incrlabel = f' (incrlabel {self.incrlabel})' if self.incrlabel is not None else ''
        font = f' {self.font.to_sexpr()}' if self.font.to_sexpr() != '' else ''

        expression  = f'{indents}(tbtext "{dequote(self.text)}" (name "{dequote(self.name)}") '
        expression += f'(pos {self.position.X} {self.position.Y}{corner}){option}{rotate}'
        expression += f'{font}{justify}{maxlen}{maxheight}{repeat}{incrx}{incry}{incrlabel}'
        if self.comment is not None:
            expression += f' (comment "{dequote(self.comment)}")\n'
        expression += f'){endline}'
        return expression


@dataclass
class TextSize():
    """The ``TextSize`` define the default width and height of text"""

    width: float = 1.5
    """The ``width`` token defines the default width of a text element. Defaults to 1,5."""

    height: float = 1.5
    """The ``height`` token defines the default height of a text element. Defaults to 1,5."""

    @classmethod
    def from_sexpr(cls, exp: list) -> TextSize:
        """Convert the given S-Expresstion into a TextSize object

        Args:
            - exp (list): Part of parsed S-Expression ``(textsize ...)``

        Raises:
            - Exception: When given parameter's type is not a list or when its not exactly 3 long
            - Exception: When the first item of the list is not ``textsize``

        Returns:
            - TextSize: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list) or len(exp) != 3:
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'textsize':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.width = exp[1]
        object.height = exp[2]
        return object

    def to_sexpr(self, indent=0, newline=False):
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        return f'{indents}(textsize {self.width} {self.height}){endline}'

@dataclass
class Setup():
    """The ``setup`` token defines the configuration information for the work sheet

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-worksheet/#_set_up_section"""

    textSize: TextSize = field(default_factory=lambda: TextSize())
    """The ``textSize`` token defines the default width and height of text"""

    lineWidth: float = 0.15
    """The ``lineWidth`` token attribute defines the default width of lines. Defaults to 0,15."""

    textLineWidth: float = 0.15
    """The ``textLineWidth`` token attribute define the default width of the lines used to draw 
    text. Defaults to 0,15."""

    leftMargin: float = 10.0
    """The ``leftMargin`` token defines the distance from the left edge of the page"""

    rightMargin: float = 10.0
    """The ``rightMargin`` token defines the distance from the right edge of the page"""

    topMargin: float = 10.0
    """The ``topMargin`` token defines the distance from the top edge of the page"""

    bottomMargin: float = 10.0
    """The ``bottomMargin`` token defines the distance from the bottom edge of the page"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Setup:
        """Convert the given S-Expresstion into a Setup object

        Args:
            - exp (list): Part of parsed S-Expression ``(setup ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not ``setup``

        Returns:
            - Setup: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'setup':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp[1:]:
            if item[0] == 'textsize': object.textSize = TextSize().from_sexpr(item)
            if item[0] == 'linewidth': object.lineWidth = item[1]
            if item[0] == 'textlinewidth': object.textLineWidth = item[1]
            if item[0] == 'left_margin': object.leftMargin = item[1]
            if item[0] == 'right_margin': object.rightMargin = item[1]
            if item[0] == 'top_margin': object.topMargin = item[1]
            if item[0] == 'bottom_margin': object.bottomMargin = item[1]
        return object

    def to_sexpr(self, indent=2, newline=True):
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        # KiCad puts no spaces between tokens here
        expression =  f'{indents}(setup {self.textSize.to_sexpr()}(linewidth {self.lineWidth})'
        expression += f'(textlinewidth {self.textLineWidth})\n{indents}'
        expression += f'(left_margin {self.leftMargin})(right_margin {self.rightMargin})'
        expression += f'(top_margin {self.topMargin})(bottom_margin {self.bottomMargin})'
        expression += f'){endline}'

        return expression

@dataclass
class WorkSheet():
    """The ``WorkSheet`` token defines a KiCad worksheet (.kicad_wks file)

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-worksheet/#_header_section"""

    version: str = KIUTILS_CREATE_NEW_VERSION_STR
    """The ``version`` token defines the work sheet version using the YYYYMMDD date format"""

    generator: str = KIUTILS_CREATE_NEW_GENERATOR_STR
    """The ``generator`` token defines the program used to write the file"""

    setup: Setup = field(default_factory=lambda: Setup())
    """The ``setup`` token defines the configuration information for the work sheet"""

    drawingObjects: List = field(default_factory=list)
    """The ``drawingObjects`` token can contain zero or more texts, lines, rectangles, polys or images"""

    filePath: Optional[str] = None
    """The ``filePath`` token defines the path-like string to the board file. Automatically set when
    ``self.from_file()`` is used. Allows the use of ``self.to_file()`` without parameters."""

    @classmethod
    def from_sexpr(cls, exp: list) -> WorkSheet:
        """Convert the given S-Expresstion into a WorkSheet object

        Args:
            - exp (list): Part of parsed S-Expression ``(kicad_wks ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not ``kicad_wks``

        Returns:
            - WorkSheet: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'kicad_wks':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp[1:]:
            if item[0] == 'version': object.version = item[1]
            if item[0] == 'generator': object.generator = item[1]
            if item[0] == 'setup': object.setup = Setup().from_sexpr(item)
            if item[0] == 'rect': object.drawingObjects.append(Rect().from_sexpr(item))
            if item[0] == 'line': object.drawingObjects.append(Line().from_sexpr(item))
            if item[0] == 'polygon': object.drawingObjects.append(Polygon().from_sexpr(item))
            if item[0] == 'tbtext': object.drawingObjects.append(TbText().from_sexpr(item))
            if item[0] == 'bitmap': object.drawingObjects.append(Bitmap().from_sexpr(item))
        return object

    @classmethod
    def from_file(cls, filepath: str, encoding: Optional[str] = None) -> WorkSheet:
        """Load a worksheet directly from a KiCad worksheet file (`.kicad_wks`) and sets the
        ``self.filePath`` attribute to the given file path.

        Args:
            - filepath (str): Path or path-like object that points to the file
            - encoding (str, optional): Encoding of the input file. Defaults to None (platform 
                                        dependent encoding).

        Raises:
            - Exception: If the given path is not a file

        Returns:
            - WorkSheet: Object of the WorkSheet class initialized with the given KiCad worksheet
        """
        if not path.isfile(filepath):
            raise Exception("Given path is not a file!")

        with open(filepath, 'r', encoding=encoding) as infile:
            item = cls.from_sexpr(sexpr.parse_sexp(infile.read()))
            item.filePath = filepath
            return item

    @classmethod
    def create_new(cls) -> WorkSheet:
        """Creates a new empty worksheet as KiCad would create it

        Returns:
            WorkSheet: A empty worksheet
        """
        return cls(
            version = KIUTILS_CREATE_NEW_VERSION_STR,
            generator = KIUTILS_CREATE_NEW_GENERATOR_STR
        )

    def to_file(self, filepath = None):
        """Save the object to a file in S-Expression format

        Args:
            - filepath (str, optional): Path-like string to the file. Defaults to None. If not set, 
                                        the attribute ``self.filePath`` will be used instead.

        Raises:
            - Exception: If no file path is given via the argument or via `self.filePath`
        """
        if filepath is None:
            if self.filePath is None:
                raise Exception("File path not set")
            filepath = self.filePath

        with open(filepath, 'w') as outfile:
            outfile.write(self.to_sexpr())

    def to_sexpr(self, indent=0, newline=True):
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        expression =  f'{indents}(kicad_wks (version {self.version}) (generator {self.generator})\n'
        expression += self.setup.to_sexpr(indent+2)
        for item in self.drawingObjects:
            expression += item.to_sexpr(indent+2)
        expression += f'{indents}){endline}'

        return expression