"""Defines all syntax that is shared across the symbol library, footprint library,
   schematic, board and work sheet file formats.

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    02.02.2022 - created

Documentation taken from:
    https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_common_syntax
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict

from kiutils.utils.strings import dequote

@dataclass
class Position():
    """The ``position`` token defines the positional coordinates and rotation of an object.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_position_identifier
    """

    X: float = 0.0
    """The ``X`` attribute defines the horizontal position of the object"""

    Y: float = 0.0
    """The ``Y`` attribute defines the vertical position of the object"""

    angle: Optional[float] = None
    """The optional ``angle`` attribute defines the rotational angle of the object. Not all
    objects have rotational position definitions. Symbol text angles are stored in tenths
    of a degree. All other angles are stored in degrees."""

    # TODO: What is this? Documentation does not tell ..
    unlocked: bool = False
    """The ``unlocked`` token's description has to be defined yet .."""

    @classmethod
    def from_sexpr(cls, exp: list) -> Position:
        """Convert the given S-Expresstion into a Position object

        Args:
            - exp (list): Part of parsed S-Expression ``(xxx ...)``

        Raises:
            - Exception: When the given expression is not of type ``list`` or the list is less than
                         3 items long

        Returns:
            - Position: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list) or len(exp) < 3:
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.X = exp[1]
        object.Y = exp[2]
        if len(exp) >= 4:
            # More than four components means X, Y, and either angle or unlocked are present
            if exp[3] != 'unlocked':
                object.angle = exp[3]

        for item in exp:
            if item == 'unlocked': object.unlocked = True

        return object

    def to_sexpr(self) -> str:
        """This object does not have a direct S-Expression representation."""
        raise NotImplementedError("This object does not have a direct S-Expression representation")


@dataclass
class Coordinate():
    """The ``coordinate`` token defines a three-dimentional position"""

    X: float = 0.0
    """The ``X`` token defines the position of the object on the x-axis"""

    Y: float = 0.0
    """The ``Y`` token defines the position of the object on the y-axis"""

    Z: float = 0.0
    """The ``Z`` token defines the position of the object on the z-axis"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Coordinate:
        """Convert the given S-Expresstion into a Coordinate object

        Args:
            - exp (list): Part of parsed S-Expression ``(xyz ...)``

        Raises:
            - Exception: When given parameter's type is not a list or the list is not 4 items long
            - Exception: When the first item of the list is not xyz

        Returns:
            - Coordinate: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list) or len(exp) != 4:
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'xyz':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.X = exp[1]
        object.Y = exp[2]
        object.Z = exp[3]
        return object

    def to_sexpr(self, indent=0, newline=False) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        return f'{indents}(xyz {self.X} {self.Y} {self.Z}){endline}'


@dataclass
class ColorRGBA():
    """The ``color`` token defines a RGBA color"""

    R: int = 0
    """The ``R`` token defines the red channel of the color"""

    G: int = 0
    """The ``G`` token defines the green channel of the color"""

    B: int = 0
    """The ``B`` token defines the blue channel of the color"""

    A: int = 0
    """The ``A`` token defines the alpha channel of the color"""

    precision: Optional[int] = None
    """Wether the output of ``to_sexpr()`` should have a set number of precision after the decimal
    point of the ``self.A`` attribute"""

    @classmethod
    def from_sexpr(cls, exp: list) -> ColorRGBA:
        """Convert the given S-Expresstion into a ColorRGBA object

        Args:
            - exp (list): Part of parsed S-Expression ``(color ...)``

        Raises:
            - Exception: When given parameter's type is not a list or the list is not 5 items long
            - Exception: When the first item of the list is not color

        Returns:
            - ColorRGBA: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list) or len(exp) != 5:
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'color':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.R = exp[1]
        object.G = exp[2]
        object.B = exp[3]
        object.A = exp[4]
        return object

    def to_sexpr(self, indent=0, newline=False) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        if self.precision is not None:
            alpha = f'{self.A:.{self.precision}f}'
        else:
            alpha = f'{self.A}'

        return f'{indents}(color {self.R} {self.G} {self.B} {alpha}){endline}'

@dataclass
class Stroke():
    """The ``stroke`` token defines how the outlines of graphical objects are drawn.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/#_stroke_definition
    """

    width: float = 0.0
    """The ``width`` token attribute defines the line width of the graphic object"""

    type: str = "dash"
    """The ``type`` token attribute defines the line style of the graphic object. Valid stroke line styles are:
    - ``dash``, ``dash_dot``, ``dash_dot_dot`` (version 7), ``dot``, ``default``, ``solid``
    """

    color: ColorRGBA = field(default_factory=lambda: ColorRGBA())
    """The ``color`` token attributes define the line red, green, blue, and alpha color settings"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Stroke:
        """Convert the given S-Expresstion into a Stroke object

        Args:
            - exp (list): Part of parsed S-Expression ``(stroke ...)``

        Raises:
            - Exception: When given parameter's type is not a list or the list is not 4 items long
            - Exception: When the first item of the list is not stroke

        Returns:
            - Stroke: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list) or len(exp) != 4:
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'stroke':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if type(item) != type([]):
                continue
            if item[0] == 'width': object.width = item[1]
            if item[0] == 'type':  object.type = item[1]
            if item[0] == 'color': object.color = ColorRGBA.from_sexpr(item)
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
        expression = f'{indents}(stroke (width {self.width}) (type {self.type}) {self.color.to_sexpr()}){endline}'
        return expression



@dataclass
class Font():
    """The ``font`` token attributes define how text is shown.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/#_text_effects
    """
    face: Optional[str] = None
    """The optional 'face' token indicates the font family. It should be a TrueType font family
    name or "KiCad Font" for the KiCad stroke font. (Kicad version 7)"""

    height: float = 1.0
    """The 'height' token attributes define the font's height"""

    width: float = 1.0
    """The 'width' token attributes define the font's width"""

    thickness: Optional[float] = None
    """The 'thickness' token attribute defines the line thickness of the font"""

    bold: bool = False
    """The 'bold' token specifies if the font should be bold"""

    italic: bool = False
    """The 'italic' token specifies if the font should be italicized"""

    lineSpacing: Optional[float] = None
    """The 'line_spacing' token specifies the spacing between lines as a ratio of standard
    line-spacing. (Not yet supported)"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Font:
        """Convert the given S-Expresstion into a Font object

        Args:
            - exp (list): Part of parsed S-Expression ``(font ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not font

        Returns:
            - Font: Object of the class initialized with the given S-Expression
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
            if item[0] == 'face': object.face = item[1]
            if item[0] == 'size':
                object.height = item[1]
                object.width = item[2]
            if item[0] == 'thickness': object.thickness = item[1]
            if item[0] == 'line_spacing': object.lineSpacing = item[1]
        return object

    def to_sexpr(self, indent=0, newline=False) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''
        face_name, thickness, bold, italic, linespacing = '', '', '', '', ''

        if self.face is not None:        face_name = f'(face {self.face}) '
        if self.thickness is not None:   thickness = f' (thickness {self.thickness})'
        if self.bold == True:            bold = ' bold'
        if self.italic == True:          italic = ' italic'
        if self.lineSpacing is not None: linespacing = f' (line_spacing {self.lineSpacing})'

        expression = f'{indents}(font {face_name}(size {self.height} {self.width}){thickness}{bold}{italic}{linespacing}){endline}'
        return expression

@dataclass
class Justify():
    """The ``justify`` token defines the justification of a text object

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/#_text_effects
    """

    horizontally: Optional[str] = None
    """The ``horizontally`` token sets the horizontal justification. Valid values are ``right`` or ``left``"""

    vertically: Optional[str] = None
    """The ``vertically`` token sets the vertical justification. Valid values are ``top`` or ``bottom``"""

    mirror: bool = False
    """The ``mirror`` token defines if the text is mirrored or not"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Justify:
        """Convert the given S-Expresstion into a Justify object

        Args:
            - exp (list): Part of parsed S-Expression ``(justify ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not justify

        Returns:
            - Justify: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'justify':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            # 'center' is the standard on vertical but not on horizontal in work sheets
            if item == 'left' or item == 'right' or item == 'center': object.horizontally = item
            if item == 'top' or item == 'bottom': object.vertically = item
            if item == 'mirror': object.mirror = True
        return object

    def to_sexpr(self, indent=0, newline=False) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 0.
            - newline (bool): Adds a newline to the end of the output. Defaults to False.

        Returns:
            - str: S-Expression of this object or an empty string (depending on given indentation 
              and newline settings) if no justification is given. This will cause the text to be 
              horizontally and vertically aligend
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        if self.horizontally is None and self.vertically is None and self.mirror == False:
            return f'{indents}{endline}';

        horizontally, vertically, mirror = '', '', ''

        if self.horizontally is not None: horizontally = f' {self.horizontally}'
        if self.vertically is not None: vertically = f' {self.vertically}'
        if self.mirror: mirror = f' mirror'

        expression = f'{indents}(justify{horizontally}{vertically}{mirror}){endline}'
        return expression

@dataclass
class Effects():
    """All text objects can have an optional effects section that defines how the text is displayed.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/#_text_effects
    """

    font: Font = field(default_factory=lambda: Font())
    """The ``font`` token defines how the text is shown"""

    justify: Justify = field(default_factory=lambda: Justify())
    """The ``justify`` token defines the justification of the text"""

    hide: bool = False
    """The optional ``hide`` token defines if the text is hidden"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Effects:
        """Convert the given S-Expresstion into a Effects object

        Args:
            - exp (list): Part of parsed S-Expression ``(effects ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not effects

        Returns:
            - Effects: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'effects':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if type(item) != type([]):
                if item == 'hide': object.hide = True
                else: continue
            if item[0] == 'font': object.font = Font().from_sexpr(item)
            if item[0] == 'justify': object.justify = Justify().from_sexpr(item)
        return object

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

        justification = f' {self.justify.to_sexpr()}' if self.justify.to_sexpr() != '' else ''
        hide = f' hide' if self.hide else ''

        expression =  f'{indents}(effects {self.font.to_sexpr()}{justification}{hide}){endline}'
        return expression


@dataclass
class Net():
    """The ``net`` token defines the number and name of a net"""

    number: int = 0
    """The ``number`` token defines the integer number of the net"""

    name: str = ""
    """The ``name`` token defines the name of the net"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Net:
        """Convert the given S-Expresstion into a Net object

        Args:
            - exp (list): Part of parsed S-Expression ``(net ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not net

        Returns:
            - Net: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'net':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.number = exp[1]
        object.name = exp[2]
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

        return f'{indents}(net {self.number} "{dequote(self.name)}"){endline}'

@dataclass
class Group():
    """The ``group`` token defines a group of items.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_group
    """

    name: str = ""
    """The ``name`` attribute defines the name of the group"""

    locked: bool = False
    """The ``locked`` token defines if the group may be moved or not"""

    id: str = ""
    """The ``id`` token attribute defines the unique identifier of the group"""

    members: List[str] = field(default_factory=list)
    """The ``members`` token attributes define a list of unique identifiers of the objects belonging to the group"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Group:
        """Convert the given S-Expresstion into a Group object

        Args:
            - exp (list): Part of parsed S-Expression ``(group ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not group

        Returns:
            - Group: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'group':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.name = exp[1]
        for item in exp:
            if type(item) != type([]):
                if item == 'locked': object.locked = True
                continue
            if item[0] == 'id': object.id = item[1]
            if item[0] == 'members':
                for member in item[1:]:
                    object.members.append(member)
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

        expression =  f'{indents}(group "{dequote(self.name)}"{locked} (id {self.id})\n'
        expression += f'{indents}  (members\n'
        for member in self.members:
            expression += f'{indents}    {member}\n'

        expression += f'{indents}  )\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class PageSettings():
    """The ``paper`` token defines the drawing page size and orientation.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/#_page_settings
    """
    paperSize: str = "A4"
    """The ``paperSize`` token defines the size of the paper. Valid sizes are `A0`, `A1`, `A2`,
    `A3`, `A4`, `A5`, ``A``, ``B``, ``C``, ``D`` and ``E``. When using user-defines page sizes, set 
    this to ``User``"""

    width: Optional[float] = None
    """The ``width`` token sets the width of a user-defines page size"""

    height: Optional[float] = None
    """The ``height`` token sets the height of a user-defines page size"""

    portrait: bool = False
    """The ``portrait`` token defines if the page is in portrait or landscape mode"""

    @classmethod
    def from_sexpr(cls, exp: list) -> PageSettings:
        """Convert the given S-Expresstion into a PageSettings object

        Args:
            - exp (list): Part of parsed S-Expression ``(paper ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not paper
            - Exception: When the paper type is set to ``User`` and the list's length is not 4

        Returns:
            - PageSettings: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'paper':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.paperSize = exp[1]
        if object.paperSize == "User":
            if len(exp) < 4:
                raise Exception("PageSettings: Expected more data for paper type 'User'")

            object.width = exp[2]
            object.height = exp[3]
        for item in exp:
            if type(item) != type([]):
                if item == 'portrait': object.portrait = True
                continue
        return object

    def to_sexpr(self, indent: int = 2, newline: bool = True) -> str:
        """Generate the S-Expression representing this object

        Args:
            - indent (int): Number of whitespaces used to indent the output. Defaults to 2.
            - newline (bool): Adds a newline to the end of the output. Defaults to True.

        Raises:
            - Exception: When paper size is set to ``User`` and width or height is not specified

        Returns:
            - str: S-Expression of this object
        """
        indents = ' '*indent
        endline = '\n' if newline else ''

        width, height = '', ''
        portrait = ' portrait' if self.portrait else ''
        if self.paperSize == 'User':
            if self.width is None or self.height is None:
                raise Exception("Page size set to 'User' but width or height not specified")
            width = f' {self.width}'
            height = f' {self.height}'
        return f'{indents}(paper "{dequote(self.paperSize)}"{width}{height}{portrait}){endline}'

@dataclass
class TitleBlock():
    """The ``title_block`` token defines the contents of the title block.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/#_title_block
    """

    title: Optional[str] = None
    """The optional ``title`` token attribute is a quoted string that defines the document title"""

    date: Optional[str] = None
    """The optional ``date`` token attribute is a quoted string that defines the document date using the YYYY-MM-DD format"""

    revision: Optional[str] = None
    """The optional ``revision`` token attribute is a quoted string that defines the document revision"""

    company: Optional[str] = None
    """The optional ``company`` token attribute is a quoted string that defines the document company name"""

    comments: Dict[int, str] = field(default_factory=dict)
    """The ``comments`` token attributes define a dictionary of document comments where the key is
    a number from 1 to 9 and the value is a comment string"""

    @classmethod
    def from_sexpr(cls, exp: list) -> TitleBlock:
        """Convert the given S-Expresstion into a TitleBlock object

        Args:
            - exp (list): Part of parsed S-Expression ``(title_block ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not title_block

        Returns:
            - TitleBlock: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'title_block':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'title': object.title = item[1]
            if item[0] == 'date': object.date = item[1]
            if item[0] == 'rev': object.revision = item[1]
            if item[0] == 'company': object.company = item[1]
            if item[0] == 'comment': object.comments.update({item[1]: item[2]})
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

        expression =  f'{indents}(title_block\n'
        if self.title is not None:
            expression += f'{indents}  (title "{dequote(self.title)}")\n'

        if self.date is not None:
            expression += f'{indents}  (date "{dequote(self.date)}")\n'

        if self.revision is not None:
            expression += f'{indents}  (rev "{dequote(self.revision)}")\n'

        if self.company is not None:
            expression += f'{indents}  (company "{dequote(self.company)}")\n'

        for number, comment in self.comments.items():
            expression += f'{indents}  (comment {number} "{dequote(comment)}")\n'
        expression += f'{indents}){endline}'
        return expression

@dataclass
class Property():
    """The ``property`` token defines a symbol property when used inside a ``symbol`` definition.

    Documentation:
        https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html#_symbol_property
    """

    key: str = ""
    """The ``key`` string defines the name of the property and must be unique"""

    value: str = ""
    """The ``value`` string defines the value of the property"""

    id: int = 0
    """The id token defines an integer ID for the property and must be unique"""

    position: Position = field(default_factory=lambda: Position(angle=0))
    """The ``position`` defines the X and Y coordinates as well as the rotation angle of the property.
    All three items will initially be set to zero."""

    effects: Optional[Effects] = None
    """The ``effects`` section defines how the text is displayed"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Property:
        """Convert the given S-Expresstion into a Property object

        Args:
            - exp (list): Part of parsed S-Expression ``(property ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not property

        Returns:
            - Property: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'property':
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.key = exp[1]
        object.value = exp[2]
        for item in exp[3:]:
            if item[0] == 'id': object.id = item[1]
            if item[0] == 'at': object.position = Position().from_sexpr(item)
            if item[0] == 'effects': object.effects = Effects().from_sexpr(item)
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

        posA = f' {self.position.angle}' if self.position.angle is not None else ''

        expression =  f'{indents}(property "{dequote(self.key)}" "{dequote(self.value)}" (id {self.id}) (at {self.position.X} {self.position.Y}{posA})'
        if self.effects is not None:
            expression += f'\n{self.effects.to_sexpr(indent+2)}'
            expression += f'{indents}){endline}'
        else:
            expression += f'){endline}'
        return expression
