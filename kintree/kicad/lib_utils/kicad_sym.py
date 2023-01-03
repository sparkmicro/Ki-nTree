""" DISCLAIMER
kicad_sym classes and methods were directly imported from: https://gitlab.com/kicad/libraries/kicad-library-utils
Last import date: Jan 3rd, 2023
"""

"""
Library for processing KiCad's symbol files.
"""

import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import sexpr


class KicadFileFormatError(ValueError):
    """any kind of problem discovered while parsing a KiCad file"""


# KiCad can only handle multiples of 90 degrees
VALID_ROTATIONS = frozenset({0, 90, 180, 270})


def mil_to_mm(mil: float) -> float:
    return round(mil * 0.0254, 6)


def mm_to_mil(mm: float) -> float:
    return round(mm / 0.0254)


def _parse_at(i):
    sexpr_at = _get_array(i, "at")[0]
    posx = sexpr_at[1]
    posy = sexpr_at[2]
    if len(sexpr_at) == 4:
        rot = sexpr_at[3]
    else:
        rot = None
    return (posx, posy, rot)


def _get_array(
    data,
    value,
    result: Optional[List[Any]] = None,
    level: int = 0,
    max_level: Optional[int] = None,
):
    """return the array which has value as first element"""
    if result is None:
        result = []

    if max_level is not None and max_level <= level:
        return result

    level += 1

    for i in data:
        if isinstance(i, list):
            _get_array(i, value, result, level=level, max_level=max_level)
        else:
            if i == value:
                result.append(data)
    return result


def _get_array2(data, value):
    ret = []
    for i in data:
        if isinstance(i, list) and i[0] == value:
            ret.append(i)
    return ret


def _get_color(sexpr) -> Optional["Color"]:
    col = None
    for i in sexpr:
        if isinstance(i, list) and i[0] == "color":
            col = Color(i[1], i[2], i[3], i[4])
    return col


def _get_stroke(sexpr) -> Tuple[Optional[int], Optional["Color"]]:
    width = None
    col = None
    for i in sexpr:
        if isinstance(i, list) and i[0] == "stroke":
            width = _get_value_of(i, "width")
            col = _get_color(i)
            break
    return (width, col)


def _get_fill(sexpr) -> Tuple[Optional[Any], Optional["Color"]]:
    fill = None
    col = None
    for i in sexpr:
        if isinstance(i, list) and i[0] == "fill":
            fill = _get_value_of(i, "type")
            col = _get_color(i)
            break
    return (fill, col)


def _get_xy(sexpr, lookup) -> Tuple[float, float]:
    for i in sexpr:
        if isinstance(i, list) and i[0] == lookup:
            return (i[1], i[2])
    return (0.0, 0.0)


def _get_value_ofRecursively(data, path, item_to_get=False):
    """return the array which has value as first element, but recursively

    if item_to_get is != 0, return the array element with that index
    """
    # if we walked the whole path we are done. return the data
    if not path:
        # in some cases it is useful to only get the 2nd item, for
        # example ['lenght', 42] should just return 42
        if item_to_get != 0:
            return data[item_to_get]
        return data

    for i in data:
        # look at sub-arrays, if their first element matches the path-spec,
        # strip the front item from the path list and do this recursively
        if isinstance(i, list) and i[0] == path[0]:
            return _get_value_ofRecursively(i, path[1:], item_to_get)


def _get_value_of(data, lookup, default=None):
    """find the array which has lookup as first element, return its 2nd element"""
    for i in data:
        if isinstance(i, list) and i[0] == lookup:
            return i[1]
    return default


def _has_value(data, lookup) -> bool:
    """return true if the lookup item exists"""
    for i in data:
        if isinstance(i, list) and i[0] == lookup:
            return True
    return False


class KicadSymbolBase:
    def as_json(self):
        return json.dumps(self, default=lambda x: x.__dict__, indent=2)

    def compare_pos(self, x, y):
        if hasattr(self, "posx") and hasattr(self, "posy"):
            return round(self.posx, 6) == round(x, 6) and round(self.posy, 6) == round(
                y, 6
            )
        return False

    def is_unit(self, unit, demorgan):
        if hasattr(self, "unit") and hasattr(self, "demorgan"):
            return self.unit == unit and self.demorgan == demorgan
        return False

    @classmethod
    def quoted_string(cls, s: str) -> str:
        s = re.sub(r"\n", r"\\n", s)
        return '"' + s + '"'

    @classmethod
    def dir_to_rotation(cls, d: str) -> int:
        if d == "R":
            return 0
        elif d == "U":
            return 90
        elif d == "L":
            return 180
        elif d == "D":
            return 270
        else:
            raise ValueError(
                f"Invalid direction requested: {d} (should be one of: R / U / L / D"
            )


@dataclass
class Color(KicadSymbolBase):
    """Encode the color of an entiry. Currently not used in the kicad_sym format"""

    r: int
    g: int
    b: int
    a: int


@dataclass
class TextEffect(KicadSymbolBase):
    """Encode the text effect of an entiry"""

    sizex: float
    sizey: float
    is_italic: bool = False
    is_bold: bool = False
    is_hidden: bool = False
    is_mirrored: bool = False
    h_justify: str = "center"
    v_justify: str = "center"
    color: Optional[Color] = None
    font: Optional[str] = None

    @classmethod
    def new_mil(cls, size: float) -> "TextEffect":
        return cls(mil_to_mm(size), mil_to_mm(size))

    def get_sexpr(self):
        fnt = ["font", ["size", self.sizex, self.sizey]]
        if self.is_italic:
            fnt.append("italic")
        if self.is_bold:
            fnt.append("bold")
        sx = ["effects", fnt]
        if self.is_mirrored:
            sx.append("mirror")
        if self.color:
            sx.append(self.color.get_sexpr())
        if self.is_hidden:
            sx.append("hide")

        justify = ["justify"]
        if self.h_justify and self.h_justify != "center":
            justify.append(self.h_justify)
        if self.v_justify and self.v_justify != "center":
            justify.append(self.v_justify)

        if len(justify) > 1:
            sx.append(justify)
        return sx

    @classmethod
    def from_sexpr(cls, sexpr):
        if sexpr.pop(0) != "effects":
            return None
        font = _get_array(sexpr, "font")[0]
        (sizex, sizey) = _get_xy(font, "size")
        is_italic = "italic" in font
        is_bold = "bold" in font
        is_hidden = "hide" in sexpr
        is_mirrored = "mirror" in sexpr
        justify = _get_array2(sexpr, "justify")
        h_justify = "center"
        v_justify = "center"
        if justify:
            if "top" in justify[0]:
                v_justify = "top"
            if "bottom" in justify[0]:
                v_justify = "bottom"
            if "left" in justify[0]:
                h_justify = "left"
            if "right" in justify[0]:
                h_justify = "right"
        return cls(
            sizex,
            sizey,
            is_italic,
            is_bold,
            is_hidden,
            is_mirrored,
            h_justify,
            v_justify,
        )


@dataclass
class AltFunction(KicadSymbolBase):
    name: str
    etype: str
    shape: str = "line"

    def get_sexpr(self) -> List[str]:
        return ["alternate", self.quoted_string(self.name), self.etype, self.shape]

    @classmethod
    def from_sexpr(cls, sexpr) -> "AltFunction":
        (identifier, name, etype, shape) = sexpr
        return AltFunction(name, etype, shape)


@dataclass
class Pin(KicadSymbolBase):
    name: str
    number: str
    etype: str
    posx: float = 0.0
    posy: float = 0.0
    rotation: int = 0
    shape: str = "line"
    length: float = 2.54
    is_global: bool = False
    is_hidden: bool = False
    number_int: Optional[int] = None
    name_effect: Optional[TextEffect] = None
    number_effect: Optional[TextEffect] = None
    altfuncs: List[AltFunction] = field(default_factory=list)
    unit: int = 0
    demorgan: int = 0

    def __post_init__(self):
        # try to parse the pin_number into an integer if possible
        if self.number_int is None and re.match(r"^\d+$", self.number):
            self.number_int = int(self.number)
        # There is some weird thing going on with the instance creation of name_effect and
        # number_effect.
        # when creating lots of pins from scratch, the id() of their name_effect member is the same
        # that is most likely the result of some optimization
        # to circumvent that, we create instances explicitly
        if self.name_effect is None:
            self.name_effect = TextEffect(1.27, 1.27)
        if self.number_effect is None:
            self.number_effect = TextEffect(1.27, 1.27)

    @classmethod
    def _parse_name_or_number(cls, i, typ="name"):
        """Convert a sexpr pin-name or pin-number into a python dict"""
        sexpr_n = _get_array(i, typ)[0]
        name = sexpr_n[1]
        effects = TextEffect.from_sexpr(_get_array(sexpr_n, "effects")[0])
        return (name, effects)

    def get_sexpr(self):
        sx = [
            "pin",
            self.etype,
            self.shape,
            ["at", self.posx, self.posy, self.rotation],
        ]
        if self.is_global:
            sx.append("global")
        sx.append(["length", self.length])
        if self.is_hidden:
            sx.append("hide")
        sx.append(["name", self.quoted_string(self.name), self.name_effect.get_sexpr()])
        sx.append(
            ["number", self.quoted_string(self.number), self.number_effect.get_sexpr()]
        )
        for altfn in self.altfuncs:
            sx.append(altfn.get_sexpr())

        return sx

    def get_direction(self) -> str:
        if self.rotation == 0:
            return "R"
        elif self.rotation == 90:
            return "U"
        elif self.rotation == 180:
            return "L"
        elif self.rotation == 270:
            return "D"
        else:
            raise NotImplementedError(f"Invalid 'rotation' of Pin: {self.rotation}")

    def is_duplicate(self, p: "Pin") -> bool:
        if (
            p.number == self.number
            and p.unit == self.unit
            and p.demorgan == self.demorgan
        ):
            return True
        return False

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, demorgan: int) -> "Pin":
        is_global = False
        # The first 3 items are pin, type and shape
        if sexpr.pop(0) != "pin":
            return None
        etype = sexpr.pop(0)
        shape = sexpr.pop(0)
        # the 4th item (global) is optional
        if sexpr[0] == "global":
            sexpr.pop(0)
            is_global = True
        # fetch more properties
        is_hidden = "hide" in sexpr
        length = _get_value_of(sexpr, "length")
        (posx, posy, rotation) = _parse_at(sexpr)
        (name, name_effect) = cls._parse_name_or_number(sexpr)
        (number, number_effect) = cls._parse_name_or_number(sexpr, typ="number")

        if rotation not in VALID_ROTATIONS:
            raise ValueError(
                f"Invalid 'rotation' attribute value for pin: {rotation}"
                f" (must be one of {set(VALID_ROTATIONS)})"
            )
        altfuncs = []
        alt_n = _get_array(sexpr, "alternate")
        for alt_sexpr in alt_n:
            altfuncs.append(AltFunction.from_sexpr(alt_sexpr))
        # we also need the pin-number as integer, try to convert it.
        # Some pins won't work since they are called 'MP' or similar
        number_int = None
        try:
            number_int = int(number)
        except ValueError:
            pass
        # create and return a pin with the extracted values
        return Pin(
            name,
            number,
            etype,
            posx,
            posy,
            rotation,
            shape,
            length,
            is_global,
            is_hidden,
            number_int,
            name_effect,
            number_effect,
            altfuncs=altfuncs,
            unit=unit,
            demorgan=demorgan,
        )


@dataclass
class Circle(KicadSymbolBase):
    centerx: float
    centery: float
    radius: float
    stroke_width: float = 0.254
    stroke_color: Optional[Color] = None
    fill_type: str = "none"
    fill_color: Optional[Color] = None
    unit: int = 0
    demorgan: int = 0

    def get_sexpr(self) -> List[Any]:
        sx = [
            "circle",
            ["center", self.centerx, self.centery],
            ["radius", self.radius],
            ["stroke", ["width", self.stroke_width]],
            ["fill", ["type", self.fill_type]],
        ]
        return sx

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, demorgan: int):
        # The first 3 items are pin, type and shape
        if sexpr.pop(0) != "circle":
            return None
        # the 1st element
        (centerx, centery) = _get_xy(sexpr, "center")
        radius = _get_value_of(sexpr, "radius")
        (stroke, scolor) = _get_stroke(sexpr)
        (fill, fcolor) = _get_fill(sexpr)
        return Circle(
            centerx,
            centery,
            radius,
            stroke,
            scolor,
            fill,
            fcolor,
            unit=unit,
            demorgan=demorgan,
        )


@dataclass
class Arc(KicadSymbolBase):
    # (arc (start -5.08 -1.27) (mid 0 -6.35) (end 5.08 -1.27)
    startx: float
    starty: float
    endx: float
    endy: float
    midx: float
    midy: float
    stroke_width: float = 0.254
    stroke_color: Optional[Color] = None
    fill_type: str = "none"
    fill_color: Optional[Color] = None
    unit: int = 0
    demorgan: int = 0

    def get_sexpr(self) -> List[Any]:
        sx = [
            "arc",
            ["start", self.startx, self.starty],
            ["mid", self.midx, self.midy],
            ["end", self.endx, self.endy],
        ]
        sx.append(["stroke", ["width", self.stroke_width]])
        sx.append(["fill", ["type", self.fill_type]])
        return sx

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, demorgan: int) -> Optional["Arc"]:
        if sexpr.pop(0) != "arc":
            return None
        (startx, starty) = _get_xy(sexpr, "start")
        (endx, endy) = _get_xy(sexpr, "end")
        (midx, midy) = _get_xy(sexpr, "mid")
        (stroke, scolor) = _get_stroke(sexpr)
        (fill, fcolor) = _get_fill(sexpr)
        return Arc(
            startx,
            starty,
            endx,
            endy,
            midx,
            midy,
            stroke,
            scolor,
            fill,
            fcolor,
            unit=unit,
            demorgan=demorgan,
        )


@dataclass
class Point(KicadSymbolBase):
    x: float
    y: float

    @classmethod
    def new_mil(cls, x: float, y: float) -> "Point":
        return cls(mil_to_mm(x), mil_to_mm(y))

    def get_sexpr(self):
        return ["xy", self.x, self.y]


@dataclass
class Polyline(KicadSymbolBase):
    points: List[Point]
    stroke_width: float = 0.254
    stroke_color: Optional[Color] = None
    fill_type: str = "none"
    fill_color: Optional[Color] = None
    unit: int = 0
    demorgan: int = 0

    def get_sexpr(self):
        pts_list = [x.get_sexpr() for x in self.points]
        pts_list.insert(0, "pts")
        sx = [
            "polyline",
            pts_list,
            ["stroke", ["width", self.stroke_width]],
            ["fill", ["type", self.fill_type]],
        ]
        return sx

    def is_closed(self) -> bool:
        # if the last and first point are the same, we consider the polyline closed
        # a closed triangle will have 4 points (A-B-C-A) stored in the list of points
        return (len(self.points) > 3) and (self.points[0] == self.points[-1])

    def get_boundingbox(self) -> Tuple[float, float, float, float]:
        if self.points:
            minx = min(p.x for p in self.points)
            maxx = max(p.x for p in self.points)
            miny = min(p.y for p in self.points)
            maxy = max(p.y for p in self.points)
            return (maxx, maxy, minx, miny)
        else:
            return (0, 0, 0, 0)

    def as_rectangle(self) -> "Rectangle":
        (maxx, maxy, minx, miny) = self.get_boundingbox()
        return Rectangle(
            minx,
            maxy,
            maxx,
            miny,
            self.stroke_width,
            self.stroke_color,
            self.fill_type,
            self.fill_color,
            unit=self.unit,
            demorgan=self.demorgan,
        )

    def get_center_of_boundingbox(self) -> Tuple[float, float]:
        (maxx, maxy, minx, miny) = self.get_boundingbox()
        return ((minx + maxx) / 2, ((miny + maxy) / 2))

    def is_rectangle(self) -> bool:
        # a rectangle has 5 points and is closed
        if len(self.points) != 5 or not self.is_closed():
            return False

        # construct lines between the points
        p0 = self.points[0]
        for p1_idx in range(1, len(self.points)):
            p1 = self.points[p1_idx]
            dx = p1.x - p0.x
            dy = p1.y - p0.y
            if dx != 0 and dy != 0:
                # if a line is neither horizontal or vertical its not
                # part of a rectangle
                return False
            # select next point
            p0 = p1

        return True

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, demorgan: int) -> Optional["Polyline"]:
        pts = []
        if sexpr.pop(0) != "polyline":
            return None
        for p in _get_array(sexpr, "pts")[0]:
            if "xy" in p:
                pts.append(Point(p[1], p[2]))

        (stroke, scolor) = _get_stroke(sexpr)
        (fill, fcolor) = _get_fill(sexpr)
        return Polyline(pts, stroke, scolor, fill, fcolor, unit=unit, demorgan=demorgan)


@dataclass
class Text(KicadSymbolBase):
    text: str
    posx: float
    posy: float
    rotation: float
    effects: TextEffect
    unit: int = 0
    demorgan: int = 0

    def get_sexpr(self) -> List[Any]:
        sx = [
            "text",
            self.quoted_string(self.text),
            ["at", self.posx, self.posy, self.rotation],
            self.effects.get_sexpr(),
        ]
        return sx

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, demorgan: int) -> Optional["Text"]:
        if sexpr.pop(0) != "text":
            return None
        text = sexpr.pop(0)
        (posx, posy, rotation) = _parse_at(sexpr)
        effects = TextEffect.from_sexpr(_get_array(sexpr, "effects")[0])
        return Text(text, posx, posy, rotation, effects, unit=unit, demorgan=demorgan)


@dataclass
class Rectangle(KicadSymbolBase):
    """
    Some v6 symbols use rectangles, newer ones encode them as polylines.
    At some point in time we can most likely remove this class since its not used anymore
    """

    startx: float
    starty: float
    endx: float
    endy: float
    stroke_width: float = 0.254
    stroke_color: Optional[Color] = None
    fill_type: str = "background"
    fill_color: Optional[Color] = None
    unit: int = 0
    demorgan: int = 0

    @classmethod
    def new_mil(
        cls, sx: float, sy: float, ex: float, ey: float, fill: str = "background"
    ) -> "Rectangle":
        r = cls(mil_to_mm(sx), mil_to_mm(sy), mil_to_mm(ex), mil_to_mm(ey))
        if fill in ["none", "outline", "background"]:
            r.fill_type = fill
        return r

    def get_sexpr(self) -> List[Any]:
        sx = [
            "rectangle",
            ["start", self.startx, self.starty],
            ["end", self.endx, self.endy],
            ["stroke", ["width", self.stroke_width]],
            ["fill", ["type", self.fill_type]],
        ]
        return sx

    def as_polyline(self) -> Polyline:
        pts = [
            Point(self.startx, self.starty),
            Point(self.endx, self.starty),
            Point(self.endx, self.endy),
            Point(self.startx, self.endy),
            Point(self.startx, self.starty),
        ]
        return Polyline(
            pts,
            self.stroke_width,
            self.stroke_color,
            self.fill_type,
            self.fill_color,
            unit=self.unit,
            demorgan=self.demorgan,
        )

    def get_center(self) -> Tuple[float, float]:
        x = (self.endx + self.startx) / 2.0
        y = (self.endy + self.starty) / 2.0
        return (x, y)

    @classmethod
    def from_sexpr(cls, sexpr, unit: int, demorgan: int) -> Optional["Rectangle"]:
        if sexpr.pop(0) != "rectangle":
            return None
        # the 1st element
        (startx, starty) = _get_xy(sexpr, "start")
        (endx, endy) = _get_xy(sexpr, "end")
        (stroke, scolor) = _get_stroke(sexpr)
        (fill, fcolor) = _get_fill(sexpr)
        return Rectangle(
            startx,
            starty,
            endx,
            endy,
            stroke,
            scolor,
            fill,
            fcolor,
            unit=unit,
            demorgan=demorgan,
        )


@dataclass
class Property(KicadSymbolBase):
    name: str
    value: str
    idd: int
    posx: float = 0.0
    posy: float = 0.0
    rotation: float = 0.0
    effects: Optional[TextEffect] = None

    def __post_init__(self):
        # There is some weird thing going on with the instance creation of effect.
        # Do the same trick as we do with Pin().
        if self.effects is None:
            self.effects = TextEffect(1.27, 1.27)

    def get_sexpr(self) -> List[Any]:
        sx = [
            "property",
            self.quoted_string(self.name),
            self.quoted_string(self.value),
            ["id", self.idd],
            ["at", self.posx, self.posy, self.rotation],
            self.effects.get_sexpr(),
        ]
        return sx

    def set_pos_mil(self, x: float, y: float, rot: int = 0) -> None:
        self.posx = mil_to_mm(x)
        self.posy = mil_to_mm(y)
        # TODO: verify whether we should really (silently) restrict the rotation of all properties
        if rot in VALID_ROTATIONS:
            self.rotation = rot

    @classmethod
    def from_sexpr(cls, sexpr, unit: int = 0) -> Optional["Property"]:
        if sexpr.pop(0) != "property":
            return None
        name = sexpr.pop(0)
        value = sexpr.pop(0)
        idd = _get_value_of(sexpr, "id")
        (posx, posy, rotation) = _parse_at(sexpr)
        effects = TextEffect.from_sexpr(_get_array(sexpr, "effects")[0])
        return Property(name, value, idd, posx, posy, rotation, effects)


@dataclass
class KicadSymbol(KicadSymbolBase):
    name: str
    libname: str
    filename: str = field(compare=False)
    properties: List[Property] = field(default_factory=list)
    pins: List[Pin] = field(default_factory=list)
    rectangles: List[Rectangle] = field(default_factory=list)
    circles: List[Circle] = field(default_factory=list)
    arcs: List[Arc] = field(default_factory=list)
    polylines: List[Polyline] = field(default_factory=list)
    texts: List[Text] = field(default_factory=list)
    pin_names_offset: float = 0.508
    hide_pin_names: bool = False
    hide_pin_numbers: bool = False
    is_power: bool = False
    in_bom: bool = True
    on_board: bool = True
    extends: Optional[str] = None
    unit_count: int = 0
    demorgan_count: int = 0

    def __post_init__(self):
        if self.filename == "":
            raise ValueError("Filename can not be empty")
        self.libname = Path(self.filename).stem

    def get_sexpr(self) -> List[str]:
        # add header
        full_name = self.quoted_string("{}".format(self.name))
        sx = ["symbol", full_name]
        if self.extends:
            sx.append(["extends", self.quoted_string(self.extends)])

        pn = ["pin_names"]
        if self.pin_names_offset != 0.508:
            pn.append(["offset", self.pin_names_offset])
        if self.hide_pin_names:
            pn.append("hide")
        if len(pn) > 1:
            sx.append(pn)

        sx.append(["in_bom", "yes" if self.in_bom else "no"])
        sx.append(["on_board", "yes" if self.on_board else "no"])
        if self.is_power:
            sx.append(["power"])
        if self.hide_pin_numbers:
            sx.append(["pin_numbers", "hide"])

        # add properties
        for prop in self.properties:
            sx.append(prop.get_sexpr())

        # add units
        for d in range(0, self.demorgan_count + 1):
            for u in range(0, self.unit_count + 1):
                hdr = self.quoted_string("{}_{}_{}".format(self.name, u, d))
                sx_i = ["symbol", hdr]
                for pin in (
                    self.arcs
                    + self.circles
                    + self.texts
                    + self.rectangles
                    + self.polylines
                    + self.pins
                ):
                    if pin.is_unit(u, d):
                        sx_i.append(pin.get_sexpr())

                if len(sx_i) > 2:
                    sx.append(sx_i)

        return sx

    def get_center_rectangle(self, units: List[int]) -> Optional[Polyline]:
        # return a polyline for the requested unit that is a rectangle
        # and is closest to the center
        candidates = {}
        # building a dict with floats as keys.. there needs to be a rule against that^^
        pl_rects = [i.as_polyline() for i in self.rectangles]
        pl_rects.extend(pl for pl in self.polylines if pl.is_rectangle())
        for pl in pl_rects:
            if pl.unit in units:
                # extract the center, calculate the distance to origin
                (x, y) = pl.get_center_of_boundingbox()
                dist = math.sqrt(x * x + y * y)
                candidates[dist] = pl

        if candidates:
            # sort the list return the first (smallest) item
            return candidates[sorted(candidates.keys())[0]]
        return None

    def get_pinstacks(self) -> Dict[str, List[Pin]]:
        stacks = {}
        for pin in self.pins:
            # if the unit is 0 that means this pin is common to all units
            unit_list = [pin.unit]
            if pin.unit == 0:
                unit_list = list(range(1, self.unit_count + 1))

            # if the unit is 0 that means this pin is common to all units
            demorgan_list = [pin.demorgan]
            if pin.demorgan == 0:
                demorgan_list = list(range(1, self.demorgan_count + 1))

            # add the pin to the correct stack
            for demorgan in demorgan_list:
                for unit in unit_list:
                    loc = "x{0}_y{1}_u{2}_d{3}".format(
                        pin.posx, pin.posy, unit, demorgan
                    )
                    if loc in stacks:
                        stacks[loc].append(pin)
                    else:
                        stacks[loc] = [pin]
        return stacks

    def get_property(self, pname: str) -> Optional[Property]:
        for p in self.properties:
            if p.name == pname:
                return p

        return None

    def add_default_properties(self) -> None:
        defaults = [
            {"i": 0, "n": "Reference", "v": "U", "h": False},
            {"i": 1, "n": "Value", "v": self.name, "h": False},
            {"i": 2, "n": "Footprint", "v": "", "h": True},
            {"i": 3, "n": "Datasheet", "v": "", "h": True},
            {"i": 4, "n": "ki_locked", "v": "", "h": True},
            {"i": 5, "n": "ki_keywords", "v": "", "h": True},
            {"i": 6, "n": "ki_description", "v": "", "h": True},
            {"i": 7, "n": "ki_fp_filters", "v": "", "h": False},
        ]

        for prop in defaults:
            if self.get_property(prop["n"]) is None:
                p = Property(prop["n"], prop["v"], prop["i"])
                p.effects.is_hidden = prop["h"]
                self.properties.append(p)

    @classmethod
    def new(
        cls,
        name: str,
        libname: str,
        reference: str = "U",
        footprint: str = "",
        datasheet: str = "",
        keywords: str = "",
        description: str = "",
        fp_filters: str = "",
    ):
        sym = cls(name, libname, libname + ".kicad_sym")
        sym.add_default_properties()
        sym.get_property("Reference").value = reference
        sym.get_property("Footprint").value = footprint
        sym.get_property("Datasheet").value = datasheet
        sym.get_property("ki_keywords").value = keywords
        sym.get_property("ki_description").value = description
        if isinstance(fp_filters, list):
            fp_filters = " ".join(fp_filters)
        sym.get_property("ki_fp_filters").value = fp_filters
        return sym

    def get_fp_filters(self) -> List[str]:
        filters = self.get_property("ki_fp_filters")
        if filters:
            return filters.value.split(" ")
        else:
            return []

    def is_graphic_symbol(self) -> bool:
        return self.extends is None and (
            not self.pins or self.get_property("Reference").value == "#SYM"
        )

    def is_power_symbol(self) -> bool:
        return self.is_power

    def is_locked(self) -> bool:
        return self.get_property("ki_locked") is not None

    def get_pins_by_name(self, name: str) -> List[Pin]:
        pins = []
        for pin in self.pins:
            if pin.name == name:
                pins += [pin]
        return pins

    def get_pins_by_number(self, num) -> Optional[Pin]:
        for pin in self.pins:
            # @todo num does not exist in pin...
            if pin.num == str(num):
                return pin
        return None

    def filter_pins(
        self,
        name: Optional[str] = None,
        direction: Optional[str] = None,
        electrical_type: Optional[str] = None,
    ) -> List[Pin]:
        pins = []
        for pin in self.pins:
            if (
                (name and pin.name == name)
                or (direction and pin.rotation == self.dir_to_rotation(direction))
                or (electrical_type and pin.etype == electrical_type)
            ):
                pins.append(pin)
        return pins

    # Heuristics, which tries to determine whether this is a "small" component (resistor,
    # capacitor, LED, diode, transistor, ...).
    def is_small_component_heuristics(self) -> bool:
        if len(self.pins) <= 2:
            return True

        filled_rect = self.get_center_rectangle(range(self.unit_count))

        # if there is no filled rectangle as symbol outline and we have 3 or 4 pins, we assume this
        # is a small symbol
        if (3 <= len(self.pins) <= 4) and (filled_rect is None):
            return True

        return False


@dataclass
class KicadLibrary(KicadSymbolBase):
    """
    A class to parse kicad_sym files format of the KiCad
    """

    filename: str
    symbols: List[KicadSymbol] = field(default_factory=list)
    generator: str = "kicad-library-utils"
    version: str = "20211014"

    def write(self) -> None:
        lib_file = open(self.filename, "w")
        lib_file.write(self.get_sexpr())
        lib_file.close()

    def get_sexpr(self) -> str:
        sx = [
            "kicad_symbol_lib",
            ["version", self.version],
            ["generator", self.generator],
        ]
        for sym in self.symbols:
            sx.append(sym.get_sexpr())
        return sexpr.build_sexp(sx)

    @classmethod
    def from_file(cls, filename: str) -> "KicadLibrary":
        """
        Parse a symbol library from a file.

        raises KicadFileFormatError in case of problems
        """
        library = KicadLibrary(filename)

        # read the s-expression data
        with open(filename) as f:
            # parse s-expr
            try:
                sexpr_data = sexpr.parse_sexp(f.read())
            except ValueError as exc:
                raise KicadFileFormatError(
                    f"Problem while parsing the s-expr file: {exc}"
                ) from None
        sym_list = _get_array(sexpr_data, "symbol", max_level=2)

        # Because of the various file format changes in the development of kicad v6 and v7, we want
        # to ensure that this parser is only used with v6 files. Any other version will most likely
        # not work as expected. So just don't load them at all.
        version = _get_value_of(sexpr_data, "version")
        if str(version) != "20211014":
            raise KicadFileFormatError('Version of symbol file is not "20211014"')

        # itertate over symbol
        for item in sym_list:
            item_type = item.pop(0)
            if item_type != "symbol":
                raise KicadFileFormatError(f"Unexpected token found: {item_type}")
            # retrieving the `partname`, even if formatted as `libname:partname` (legacy format)
            partname = item.pop(0).split(":")[-1]

            # we found a new part, extract the symbol name
            symbol = KicadSymbol(str(partname), libname=filename, filename=filename)

            # extract extends property
            extends = _get_array2(item, "extends")
            if extends:
                symbol.extends = extends[0][1]

            # extract properties
            for prop in _get_array(item, "property"):
                try:
                    # TODO: do not append the new property, if it is None
                    symbol.properties.append(Property.from_sexpr(prop))
                except ValueError as exc:
                    raise KicadFileFormatError(
                        f"Failed to import '{partname}': {exc}"
                    ) from exc

            # get flags
            symbol.in_bom = _get_value_of(item, "in_bom", "no") == "yes"
            symbol.on_board = _get_value_of(item, "on_board", "no") == "yes"
            if _has_value(item, "power"):
                symbol.is_power = True

            # get pin-numbers properties
            pin_numbers_info = _get_array2(item, "pin_numbers")
            if pin_numbers_info:
                if "hide" in pin_numbers_info[0]:
                    symbol.hide_pin_numbers = True

            # get pin-name properties
            pin_names_info = _get_array2(item, "pin_names")
            if pin_names_info:
                if "hide" in pin_names_info[0]:
                    symbol.hide_pin_names = True
                # sometimes the pin_name_offset value does not exist, then use 20mil as default
                symbol.pin_names_offset = _get_value_of(
                    pin_names_info[0], "offset", 0.508
                )

            # get the actual geometry information
            # it is split over units
            subsymbols = _get_array2(item, "symbol")
            for unit_data in subsymbols:
                # we found a new 'subpart' (no clue how to call it properly)
                subpart_type = unit_data.pop(0)
                if subpart_type != "symbol":
                    raise KicadFileFormatError(
                        f"Unexpected token found as 'subsymbol' of {item_type}: {subpart_type}"
                    )
                name = unit_data.pop(0)

                # split the name
                m1 = re.match(r"^" + re.escape(partname) + r"_(\d+?)_(\d+?)$", name)
                if not m1:
                    raise KicadFileFormatError(
                        "Failed to parse subsymbol due to invalid name: {name}"
                    )

                (unit_idx, demorgan_idx) = (m1.group(1), m1.group(2))
                unit_idx = int(unit_idx)
                demorgan_idx = int(demorgan_idx)

                # update the amount of units, alternative-styles (demorgan)
                symbol.unit_count = max(unit_idx, symbol.unit_count)
                symbol.demorgan_count = max(demorgan_idx, symbol.demorgan_count)

                # extract pins and graphical items
                for pin in _get_array(unit_data, "pin"):
                    try:
                        symbol.pins.append(Pin.from_sexpr(pin, unit_idx, demorgan_idx))
                    except ValueError as valexc:
                        raise KicadFileFormatError(
                            f"Failed to parse symbol {partname}: {valexc}"
                        ) from None
                for circle in _get_array(unit_data, "circle"):
                    symbol.circles.append(
                        Circle.from_sexpr(circle, unit_idx, demorgan_idx)
                    )
                for arc in _get_array(unit_data, "arc"):
                    symbol.arcs.append(Arc.from_sexpr(arc, unit_idx, demorgan_idx))
                for rect in _get_array(unit_data, "rectangle"):
                    # symbol.polylines.append(
                    #     Rectangle.from_sexpr(rect, unit, demorgan).as_polyline()
                    # )
                    symbol.rectangles.append(
                        Rectangle.from_sexpr(rect, unit_idx, demorgan_idx)
                    )
                for poly in _get_array(unit_data, "polyline"):
                    symbol.polylines.append(
                        Polyline.from_sexpr(poly, unit_idx, demorgan_idx)
                    )
                for text in _get_array(unit_data, "text"):
                    symbol.texts.append(Text.from_sexpr(text, unit_idx, demorgan_idx))

            # add it to the list of symbols
            library.symbols.append(symbol)

        return library


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        a = KicadLibrary.from_file(sys.argv[1])
        a.generator = "kicad_symbol_editor"
        a.version = "20200908"
        print(a.get_sexpr())
    else:
        print("pass a .kicad_sym file please")
