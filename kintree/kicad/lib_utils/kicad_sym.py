''' DISCLAIMER
kicad_sym classes and methods were directly imported from: https://gitlab.com/kicad/libraries/kicad-library-utils
'''
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List
from pathlib import Path

import re, math
import sys, os

from . import sexpr

def mil_to_mm(mil):
    return round(mil * 0.0254, 6)

def mm_to_mil(mm):
    return round(mm / 0.0254)

def _parse_at(i):
    sexpr_at = _get_array(i, 'at')[0]
    posx = sexpr_at[1]
    posy = sexpr_at[2]
    if len(sexpr_at) == 4:
      rot = sexpr_at[3]
    else:
      rot = None
    return (posx, posy, rot)

def _get_array(data, value, result=None, level=0, max_level=None):
    """return the array which has value as first element"""
    if result is None: result = []

    if max_level is not None and max_level <= level:
        return result

    level += 1

    for i in data:
        if type(i) == type([]):
            _get_array(i, value, result, level=level, max_level=max_level)
        else:
            if i == value:
                result.append(data)
    return result

def _get_array2(data, value):
    ret = []
    for i in data:
        if type(i) == type([]) and i[0] == value:
            ret.append(i)
    return ret

def _get_color(sexpr):
    col = None
    for i in sexpr:
        if type(i) == type([]) and i[0] == 'color':
            col = Color(i[1], i[2], i[3], i[4])
    return col


def _get_stroke(sexpr):
    width = None
    col = None
    for i in sexpr:
        if type(i) == type([]) and i[0] == 'stroke':
            width = _get_value_of(i, 'width')
            col = _get_color(i)
            break
    return (width, col)

def _get_fill(sexpr):
    fill = None
    col = None
    for i in sexpr:
        if type(i) == type([]) and i[0] == 'fill':
            fill = _get_value_of(i, 'type')
            col = _get_color(i)
            break
    return (fill, col)

def _get_xy(sexpr, lookup):
    for i in sexpr:
        if type(i) == type([]) and i[0] == lookup:
            return (i[1], i[2])
    return (0, 0)

def _get_value_ofRecursively(data, path, item_to_get=False):
    """return the array which has value as first element, but recursively

        if item_to_get is != 0, return the array element with that index
    """
    # if we walked the whole path we are done. return the data
    if len(path) == 0:
        # in some cases it is usefull to only get the 2nd item, for
        # example ['lenght', 42] should just return 42
        if item_to_get != 0:
            return data[item_to_get]
        return data

    for i in data:
        # look at sub-arrays, if their first element matches the path-spec,
        # strip the front item from the path list and do this recursively
        if type(i) == type([]) and i[0] == path[0]:
            return _get_value_ofRecursively(i, path[1:], item_to_get)

def _get_value_of(data, lookup, default=None):
    """find the array which has lookup as first element, return its 2nd element"""
    for i in data:
        if type(i) == type([]) and i[0] == lookup:
            return i[1]
    return default

def _has_value(data, lookup):
    """return true if the lookup item exists"""
    for i in data:
        if type(i) == type([]) and i[0] == lookup:
            return True
    return False

class KicadSymbolBase(object):
    def as_json(self):
      return json.dumps(self, default=lambda x: x.__dict__, indent=2)

    def compare_pos(s, x, y):
        if 'posx' in s.__dict__ and 'posy' in s.__dict__:
            return round(s.posx, 6) == round(x, 6) and round(s.posy, 6) == round(y, 6)
        return False

    def is_unit(s, unit, demorgan):
        if 'unit' in s.__dict__ and 'demorgan' in s.__dict__:
              return s.unit == unit and s.demorgan == demorgan
        return False

    @classmethod
    def quoted_string(cls, s):
        s = re.sub(r'\n', r'\\n', s)
        return '"' + s + '"'

    @classmethod
    def dir_to_rotation(cls, d):
       if d == 'R':
           return 0
       if d == 'U':
           return 90
       if d == 'L':
           return 180
       if d == 'D':
           return 270

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
    color: Color = None
    font: str = None

    @classmethod
    def new_mil(cls, size):
      te = cls(mil_to_mm(size), mil_to_mm(size))
      return te

    def get_sexpr(s):
      fnt = ['font', ['size', s.sizex, s.sizey]]
      if s.is_italic: fnt.append('italic')
      if s.is_bold: fnt.append('bold')
      sx = ['effects', fnt]
      if s.is_mirrored: sx.append('mirror')
      if s.color: sx.append(s.color.get_sexpr())
      if s.is_hidden: sx.append('hide')

      justify = ['justify']
      if s.h_justify and s.h_justify != 'center': justify.append(s.h_justify)
      if s.v_justify and s.v_justify != 'center': justify.append(s.v_justify)
 
      if len(justify) > 1: sx.append(justify)
      return sx
  
    @classmethod
    def from_sexpr(cls, sexpr):
        sexpr_orig = sexpr.copy()
        if (sexpr.pop(0) != 'effects'):
            return None
        font = _get_array(sexpr, 'font')[0]
        (sizex, sizey) = _get_xy(font, 'size')
        is_italic = 'italic' in font
        is_bold = 'bold' in font
        is_hidden = 'hide' in sexpr
        is_mirrored = 'mirror' in sexpr
        justify = _get_array2(sexpr, 'justify')
        h_justify = "center"
        v_justify = "center"
        if justify:
            if 'top' in justify[0]: v_justify = 'top'
            if 'bottom' in justify[0]: v_justify = 'bottom'
            if 'left' in justify[0]: h_justify = 'left'
            if 'right' in justify[0]: h_justify = 'right'
        return cls(sizex, sizey, is_italic, is_bold, is_hidden, is_mirrored, h_justify, v_justify)

@dataclass
class Pin(KicadSymbolBase):
    name: str
    number: str
    etype: str
    posx: float = 0
    posy: float = 0
    rotation: int = 0
    shape: str = 'line'
    length: float = 2.54
    is_global: bool = False
    is_hidden: bool = False
    number_int: int = None
    name_effect: TextEffect = None
    number_effect: TextEffect = None
    unit: int = 0
    demorgan: int = 0

    def __post_init__(self):
        # try to parse the pin_number into an integer if possible
        if self.number_int == None and re.match(r'^\d+$', self.number):
            self.number_int = int(self.number)
        # there is some weird thing going on with the instance creation of name_effect and number_effect
        # when creating lots of pins from scratch, the id() of their name_effect member is the same
        # that is most likely the result of some optimization
        # to circumvent that, we create instances explicitly
        if self.name_effect == None:
            self.name_effect = TextEffect(1.27, 1.27)
        if self.number_effect == None:
            self.number_effect = TextEffect(1.27, 1.27)

    @classmethod
    def _parse_name_or_number(cls, i, typ='name'):
        """ Convert a sexpr pin-name or pin-number into a python dict """
        sexpr_n = _get_array(i, typ)[0]
        name = sexpr_n[1]
        effects = TextEffect.from_sexpr(_get_array(sexpr_n, 'effects')[0])
        return (name, effects)

    def get_sexpr(s):
        sx = [
            'pin', s.etype, s.shape, ['at', s.posx, s.posy, s.rotation],
        ]
        if s.is_global:
            sx.append( 'global')
        sx.append(['length', s.length])
        if s.is_hidden:
            sx.append('hide')
        sx.append(['name', s.quoted_string(s.name), s.name_effect.get_sexpr()])
        sx.append(['number', s.quoted_string(s.number), s.number_effect.get_sexpr()])
        return sx

    def get_direction(s):
       if s.rotation == 0:
         return 'R'
       elif s.rotation == 90:
         return 'U'
       elif s.rotation == 180:
         return 'L'
       elif s.rotation == 270:
         return 'D'

    def is_duplicate(s, p):
       if p.number == s.number and p.unit == s.unit and p.demorgan == s.demorgan:
           return True

    @classmethod
    def from_sexpr(cls, sexpr, unit, demorgan):
        sexpr_orig = sexpr.copy()
        is_global = False
        # The first 3 items are pin, type and shape
        if (sexpr.pop(0) != 'pin'):
            return None
        etype = sexpr.pop(0)
        shape = sexpr.pop(0)
        # the 4th item (global) is optional
        if sexpr[0] == 'global':
            sexpr.pop(0)
            is_global = True
        # fetch more properties
        is_hidden = 'hide' in sexpr
        length = _get_value_of(sexpr, 'length')
        (posx, posy, rotation) = _parse_at(sexpr)
        (name, name_effect) = cls._parse_name_or_number(sexpr)
        (number, number_effect) = cls._parse_name_or_number(sexpr, typ='number')
        # we also need the pin-number as integer, try to convert it.
        # Some pins won't work since they are called 'MP' or similar
        number_int = None
        try:
            number_int = int(number)
        except ValueError:
            pass
        # create and return a pin with the just extraced values
        return Pin(name,
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
                   unit = unit,
                   demorgan = demorgan)

@dataclass
class Circle(KicadSymbolBase):
    centerx: float
    centery: float
    radius: float
    stroke_width: float = 0.254
    stroke_color: Color = None
    fill_type: str = 'none'
    fill_color: Color = None
    unit: int = 0
    demorgan: int = 0

    def get_sexpr(s):
        sx = [
            'circle', ['center', s.centerx, s.centery], ['radius', s.radius],
            ['stroke', ['width', s.stroke_width]],
            ['fill', ['type', s.fill_type]]
        ]
        return sx

    @classmethod
    def from_sexpr(cls, sexpr, unit, demorgan):
        sexpr_orig = sexpr.copy()
        # The first 3 items are pin, type and shape
        if (sexpr.pop(0) != 'circle'):
            return None
        # the 1st element
        (centerx, centery) = _get_xy(sexpr, 'center')
        radius = _get_value_of(sexpr, 'radius')
        (stroke, scolor) = _get_stroke(sexpr)
        (fill, fcolor) = _get_fill(sexpr)
        return Circle(centerx, centery, radius, stroke, scolor, fill, fcolor, unit = unit, demorgan = demorgan)

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
    stroke_color: Color = None
    fill_type: str = 'none'
    fill_color: Color = None
    unit: int = 0
    demorgan: int = 0

    def get_sexpr(s):
        sx = [ 'arc', ['start', s.startx, s.starty], ['mid', s.midx, s.midy], ['end', s.endx, s.endy]]
        sx.append(['stroke', ['width', s.stroke_width]])
        sx.append(['fill', ['type', s.fill_type]])
        return sx

    @classmethod
    def from_sexpr(cls, sexpr, unit, demorgan):
        sexpr_orig = sexpr.copy()
        if (sexpr.pop(0) != 'arc'):
            return None
        (startx, starty) = _get_xy(sexpr, 'start')
        (endx, endy) = _get_xy(sexpr, 'end')
        (midx, midy) = _get_xy(sexpr, 'mid')
        (stroke, scolor) = _get_stroke(sexpr)
        (fill, fcolor) = _get_fill(sexpr)
        return Arc(startx, starty, endx, endy, midx, midy, stroke, scolor, fill, fcolor, unit=unit, demorgan=demorgan)

@dataclass
class Point(KicadSymbolBase):
    x: float
    y: float

    @classmethod
    def new_mil(c, x, y):
        return c(mil_to_mm(x), mil_to_mm(y))

    def get_sexpr(s):
      return ['xy', s.x, s.y]

@dataclass
class Polyline(KicadSymbolBase):
    points: List[Point]
    stroke_width: float = 0.254
    stroke_color: Color = None
    fill_type: str = 'none'
    fill_color: Color = None
    unit: int = 0
    demorgan: int = 0

    def get_sexpr(s):
        pts_list = list(map(lambda x: x.get_sexpr(), s.points))
        pts_list.insert(0, 'pts')
        sx = [
            'polyline', pts_list,
            ['stroke', ['width', s.stroke_width]],
            ['fill', ['type', s.fill_type]]
        ]
        return sx

    def is_closed(s):
        # if the last and first point are the same, we consider the polyline closed
        # a closed triangle will have 4 points (A-B-C-A) stored in the list of points
        return len(s.points) > 3 and s.points[0].__eq__(s.points[-1])

    def get_boundingbox(s):
        (minx, maxx, miny, maxy) = (0, 0, 0, 0)
        for p in s.points:
            minx = min(minx, p.x)
            maxx = max(maxx, p.x)
            miny = min(miny, p.y)
            maxy = max(maxy, p.y)
        return(maxx, maxy, minx, miny)

    def as_rectangle(s):
        (maxx, maxy, minx, miny) = s.get_boundingbox()
        return Rectangle(minx, maxy, maxx, miny, s.stroke_width, s.stroke_color, s.fill_type, s.fill_color, unit=s.unit, demorgan=s.demorgan)

    def get_center_of_boundingbox(s):
        (maxx, maxy, minx, miny) = s.get_boundingbox()
        return ((minx + maxx) / 2, ((miny + maxy) / 2))

    def is_rectangle(s):
        # a rectangle has 5 points and is closed
        if len(s.points) != 5 or not s.is_closed():
            return False

        # construct lines between the points
        p0 = s.points[0]
        for p1_idx in range(1, len(s.points)):
            p1 = s.points[p1_idx]
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
    def from_sexpr(cls, sexpr, unit, demorgan):
        sexpr_orig = sexpr.copy()
        pts = []
        if (sexpr.pop(0) != 'polyline'):
            return None
        for p in _get_array(sexpr, 'pts')[0]:
            if 'xy' in p:
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

    def get_sexpr(s):
        sx = [
            'text', s.quoted_string(s.text),
            ['at', s.posx, s.posy, s.rotation],
            s.effects.get_sexpr()
        ]
        return sx

    @classmethod
    def from_sexpr(cls, sexpr, unit, demorgan):
        sexpr_orig = sexpr.copy()
        pts = []
        if (sexpr.pop(0) != 'text'):
            return None
        text = sexpr.pop(0)
        (posx, posy, rotation) = _parse_at(sexpr)
        effects = TextEffect.from_sexpr(_get_array(sexpr, 'effects')[0])
        return Text(text, posx, posy, rotation, effects, unit = unit, demorgan = demorgan)

@dataclass
class Rectangle(KicadSymbolBase):
    """Some v6 symbols use rectangles, newer ones encode them as polylines.
       At some point in time we can most likely remove this class since its not used anymore"""
    startx: float
    starty: float
    endx: float
    endy: float
    stroke_width: float = 0.254
    stroke_color: Color = None
    fill_type: str = 'background'
    fill_color: Color = None
    unit: int = 0
    demorgan: int = 0

    @classmethod
    def new_mil(c, sx, sy, ex, ey, fill = 'background'):
        r = c(mil_to_mm(sx), mil_to_mm(sy), mil_to_mm(ex), mil_to_mm(ey))
        if fill in ['none', 'outline', 'background']:
            r.fill_type = fill
        return r

    def get_sexpr(s):
        sx = [
            'rectangle', ['start', s.startx, s.starty], ['end', s.endx, s.endy],
            ['stroke', ['width', s.stroke_width]],
            ['fill', ['type', s.fill_type]]
        ]
        return sx

    def as_polyline(s):
        pts = [
            Point(s.startx, s.starty),
            Point(s.endx, s.starty),
            Point(s.endx, s.endy),
            Point(s.startx, s.endy),
            Point(s.startx, s.starty),
        ]
        return Polyline(pts, s.stroke_width, s.stroke_color, s.fill_type, s.fill_color, unit=s.unit, demorgan=s.demorgan)

    def get_center(s):
        x = (s.endx + s.startx)  / 2
        y = (s.endy + s.starty) / 2
        return (x, y)

    @classmethod
    def from_sexpr(cls, sexpr, unit, demorgan):
        sexpr_orig = sexpr.copy()
        if (sexpr.pop(0) != 'rectangle'):
            return None
        # the 1st element
        (startx, starty) = _get_xy(sexpr, 'start')
        (endx, endy) = _get_xy(sexpr, 'end')
        (stroke, scolor) = _get_stroke(sexpr)
        (fill, fcolor) = _get_fill(sexpr)
        return Rectangle(startx, starty, endx, endy, stroke, scolor, fill, fcolor, unit=unit, demorgan=demorgan)

@dataclass
class Property(KicadSymbolBase):
    name: str
    value: str
    idd: int
    posx: float = 0
    posy: float = 0
    rotation: float = 0
    effects: TextEffect = None

    def __post_init__(self):
        # there is some weird thing going on with the instance creation of effect. Do the same trick as
        # we do with Pin()
        if self.effects == None:
            self.effects = TextEffect(1.27, 1.27)
    
    def get_sexpr(s):
        sx = [
            'property', s.quoted_string(s.name), s.quoted_string(s.value), ['id', s.idd],
            ['at', s.posx, s.posy, s.rotation],
            s.effects.get_sexpr()
        ]
        return sx

    def set_pos_mil(self, x, y, rot = 0):
        self.posx = mil_to_mm(x)
        self.posy = mil_to_mm(y)
        if rot in [0, 90, 180, 270]:
            self.rotation = rot

    @classmethod
    def from_sexpr(cls, sexpr, unit=0):
        sexpr_orig = sexpr.copy()
        if (sexpr.pop(0) != 'property'):
            return None
        name = sexpr.pop(0)
        value = sexpr.pop(0)
        idd = _get_value_of(sexpr, 'id')
        (posx, posy, rotation) = _parse_at(sexpr)
        effects = TextEffect.from_sexpr(_get_array(sexpr, 'effects')[0])
        return Property(name, value, idd, posx, posy, rotation, effects)

@dataclass
class KicadSymbol(KicadSymbolBase):
    name: str
    libname: str
    filename: str
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
    extends: str = None
    unit_count: int = 0
    demorgan_count: int = 0

    def __post_init__(self):
        if self.filename == "":
            raise ValueError("Filename can not be empty")
        self.libname = Path(self.filename).stem

    def get_sexpr(s):
        # add header
        full_name = s.quoted_string("{}".format(s.name))
        sx = [
            'symbol', full_name
        ]
        if s.extends:
            sx.append(['extends', s.quoted_string(s.extends)])

        pn = ['pin_names']
        if s.pin_names_offset != 0.508:
            pn.append(['offset', s.pin_names_offset])
        if s.hide_pin_names:
            pn.append('hide')
        if len(pn) > 1:
            sx.append(pn)

        if s.in_bom:
            sx.append(['in_bom', 'yes'])
        if s.on_board:
            sx.append(['on_board', 'yes'])
        if s.is_power:
            sx.append(['power'])
        if s.hide_pin_numbers:
            sx.append(['pin_numbers', 'hide'])



        # add properties
        for prop in s.properties:
            sx.append(prop.get_sexpr())

        # add units
        for d in range(0, s.demorgan_count + 1):
            for u in range(0, s.unit_count + 1):
                hdr = s.quoted_string("{}_{}_{}".format(s.name, u, d))
                sx_i = ['symbol', hdr]
                for pin in s.arcs + s.circles + s.texts + s.rectangles + s.polylines + s.pins:
                    if pin.is_unit(u, d):
                        sx_i.append(pin.get_sexpr())

                if len(sx_i) > 2:
                  sx.append(sx_i)

        return sx

    def get_center_rectangle(s, units: List):
        # return a polyline for the requested unit that is a rectangle
        # and is closest to the center
        candidates = {}
        # building a dict with floats as keys.. there needs to be a rule against that^^
        pl_rects = [i.as_polyline() for i in s.rectangles]
        pl_rects.extend(filter(lambda pl : pl.is_rectangle(), s.polylines))
        for pl in pl_rects:
          if pl.unit in units:
            # extract the center, calculate the distance to origin
            (x, y) = pl.get_center_of_boundingbox()
            dist = math.sqrt(x*x + y*y)
            candidates[dist] = pl

        if len(candidates) > 0:
            # sort the list return the first (smalles) item
            return candidates[sorted(candidates.keys())[0]]
        return None

    def get_pinstacks(s):
        stacks = {}
        for pin in s.pins:
            # if the unit is 0 that means this pin is common to all units
            unit_list = [pin.unit]
            if pin.unit == 0:
                unit_list = list(range(1, s.unit_count + 1))

            # if the unit is 0 that means this pin is common to all units
            demorgan_list = [pin.demorgan]
            if pin.demorgan == 0:
                demorgan_list = list(range(1, s.demorgan_count + 1))

            # add the pin to the correct stack
            for demorgan in demorgan_list:
                for unit in unit_list:
                    loc = "x{0}_y{1}_u{2}_d{3}".format(pin.posx, pin.posy, unit, demorgan)
                    if loc in stacks:
                        stacks[loc].append(pin)
                    else:
                        stacks[loc] = [pin]
        return stacks

    def get_property(self, pname):
        for p in self.properties:
            if p.name == pname:
                return p
        return None

    def add_default_properties(self):
        defaults = [
            {'i': 0, 'n': "Reference", 'v': "U", 'h': False},
            {'i': 1, 'n': "Value", 'v': self.name, 'h': False},
            {'i': 2, 'n': "Footprint", 'v': "", 'h': True},
            {'i': 3, 'n': "Datasheet", 'v': "", 'h': True},
            {'i': 4, 'n': "ki_locked", 'v': "", 'h': True},
            {'i': 5, 'n': "ki_keywords", 'v': "", 'h': True},
            {'i': 6, 'n': "ki_description", 'v': "", 'h': True},
            {'i': 7, 'n': "ki_fp_filters", 'v': "", 'h': False}
        ]

        for prop in defaults:
            if self.get_property(prop['n']) == None:
                p = Property(prop['n'], prop['v'], prop['i'])
                p.effects.is_hidden = prop['h']
                self.properties.append(p)

    @classmethod
    def new(cls, name, libname, reference="U", footprint="", datasheet="", keywords="", description="", fp_filters=""):
        sym = cls(name, libname)
        sym.add_default_properties()
        sym.get_property('Reference').value = reference
        sym.get_property('Footprint').value = footprint
        sym.get_property('Datasheet').value = datasheet
        sym.get_property('ki_keywords').value = keywords
        sym.get_property('ki_description').value = description
        if type(fp_filters) is list:
            fp_filters = " ".join(fp_filters)
        sym.get_property('ki_fp_filters').value = fp_filters
        return sym

    def get_fp_filters(self):
        filters = self.get_property('ki_fp_filters')
        if filters:
            return filters.value.split(" ")
        else:
            return []

    def is_graphic_symbol(self):
        return self.extends == None and (len(self.pins) == 0 or self.get_property('Reference').value == '#SYM')

    def is_power_symbol(self):
        return self.is_power

    def is_locked(self):
      return self.get_property('ki_locked') != None

    def does_extend(self):
        return does_extend

    def get_pins_by_name(self, name):
        pins = []
        for pin in self.pins:
            if pin.name == name:
                pins.append(pin)
        return pins

    def get_pins_by_number(self, num):
        for pin in self.pins:
            if pin.num == str(num):
                return pin
        return None

    def filter_pins(self, name=None, direction=None, electrical_type=None):
        pins = []
        for pin in self.pins:
            if ((name and pin.name == name)
                    or (direction and pin.rotation == self.dir_to_rotation(direction))
                    or (electrical_type
                        and pin.etype == electrical_type)):
                pins.append(pin)
        return pins


    # heuristics, which tries to determine whether this is a "small" component (resistor, capacitor, LED, diode, transistor, ...)
    def is_small_component_heuristics(self):
        if len(self.pins) <= 2:
            return True

        filled_rect = self.get_center_rectangle(range(self.unit_count))

        # if there is no filled rectangle as symbol outline and we have 3 or 4 pins, we assume this
        # is a small symbol
        if len(self.pins) >= 3 and len(self.pins) <= 4 and filled_rect == None:
            return True

        return False


@dataclass
class KicadLibrary(KicadSymbolBase):
    """
    A class to parse kicad_sym files format of the KiCad
    """
    filename: str
    symbols: List[KicadSymbol] = field(default_factory=list)
    generator: str = 'kicad-library-utils'
    version: str = '20211218'

    def write(s):
        lib_file = open(s.filename,"w")
        lib_file.write(s.get_sexpr())
        lib_file.close()


    def get_sexpr(s):
        sx = [
            'kicad_symbol_lib', ['version', s.version], ['generator', s.generator]
        ]
        for sym in s.symbols:
            sx.append(sym.get_sexpr())
        return sexpr.format_sexp(sexpr.build_sexp(sx), max_nesting=4)

    @classmethod
    def from_file(cls, filename):
        library = KicadLibrary(filename)

        # read the s-expression data
        f_name = open(filename)
        lines = ''.join(f_name.readlines())

        #i parse s-expr
        sexpr_data = sexpr.parse_sexp(lines)
        sym_list = _get_array(sexpr_data, 'symbol', max_level=2)
        f_name.close()

        # itertate over symbol
        for item in sym_list:
            if item.pop(0) != 'symbol':
                raise ValueError('unexpected token in file')
            # retrieving only the `partname` if formated as `libname:partname` (legacy format)
            partname = item.pop(0).split(':')[-1]

            # we found a new part, extract the symbol name
            symbol = KicadSymbol(str(partname), libname = filename, filename = filename)

            # extract extends property
            extends = _get_array2(item, 'extends')
            if len(extends) > 0:
              symbol.extends = extends[0][1]

            # extract properties
            for prop in _get_array(item, 'property'):
                symbol.properties.append(Property.from_sexpr(prop))

            # get flags
            if _has_value(item, 'in_bom'):
                symbol.in_bom = True
            if _has_value(item, 'power'):
                symbol.is_power = True
            if _has_value(item, 'on_board'):
                symbol.on_board = True

            # get pin-numbers properties
            pin_numbers_info = _get_array2(item, 'pin_numbers')
            if pin_numbers_info:
                if 'hide' in pin_numbers_info[0]:
                    symbol.hide_pin_numbers = True

            # get pin-name properties
            pin_names_info = _get_array2(item, 'pin_names')
            if pin_names_info:
                if 'hide' in pin_names_info[0]:
                    symbol.hide_pin_names = True
                # sometimes the pin_name_offset value does not exist, then use 20mil as default
                symbol.pin_names_offset = _get_value_of(pin_names_info[0], 'offset', 0.508)


            # get the actual geometry information
            # it is split over units
            subsymbols = _get_array2(item, 'symbol')
            for unit_data in subsymbols:
                # we found a new 'subpart' (no clue how to call it properly)
                if unit_data.pop(0) != 'symbol':
                    raise ValueError('unexpected token in file')
                name = unit_data.pop(0)

                # split the name
                m1 = re.match(r'^'+re.escape(partname)+'_(\d+?)_(\d+?)$', name)
                if not m1:
                    raise ValueError('failed to parse subsymbol')

                (unit_idx, demorgan_idx) = (m1.group(1), m1.group(2))
                unit_idx = int(unit_idx)
                demorgan_idx = int(demorgan_idx)

                # update the amount of units, alternative-styles (demorgan)
                symbol.unit_count = max(unit_idx, symbol.unit_count)
                symbol.demorgan_count = max(demorgan_idx, symbol.demorgan_count)

                # extract pins and graphical items
                for pin in _get_array(unit_data, 'pin'):
                    symbol.pins.append(Pin.from_sexpr(pin, unit_idx, demorgan_idx))
                for circle in _get_array(unit_data, 'circle'):
                    symbol.circles.append(Circle.from_sexpr(circle, unit_idx, demorgan_idx))
                for arc in _get_array(unit_data, 'arc'):
                    symbol.arcs.append(Arc.from_sexpr(arc, unit_idx, demorgan_idx))
                for rect in _get_array(unit_data, 'rectangle'):
                    #symbol.polylines.append(Rectangle.from_sexpr(rect, unit, demorgan).as_polyline())
                    symbol.rectangles.append(Rectangle.from_sexpr(rect, unit_idx, demorgan_idx))
                for poly in _get_array(unit_data, 'polyline'):
                    symbol.polylines.append(Polyline.from_sexpr(poly, unit_idx, demorgan_idx))
                for text in _get_array(unit_data, 'text'):
                    symbol.texts.append(Text.from_sexpr(text, unit_idx, demorgan_idx))

            # add it to the list of symbols
            library.symbols.append(symbol)


        return library

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        a = KicadLibrary.from_file(sys.argv[1])
        a.generator = 'kicad_symbol_editor'
        a.version = '20200908'
        print(a.get_sexpr())
    else:
        print("pass a .kicad_sym file please")
