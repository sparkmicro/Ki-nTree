""" DISCLAIMER
Sexpr classes and methods were directly imported from: https://gitlab.com/kicad/libraries/kicad-library-utils
Last import date: Jan 3rd, 2023
"""

"""
code extracted from: http://rosettacode.org/wiki/S-Expressions
"""

import re
from typing import Any, Optional

dbg: bool = False

term_regex = r"""(?mx)
    \s*(?:
        (\()|
        (\))|
        ([+-]?\d+\.\d+(?=[\ \)]))|
        (\-?\d+(?=[\ \)]))|
        "((?:[^"]|(?<=\\)")*)"|
        ([^(^)\s]+)
       )"""


class SexprError(ValueError):
    pass


def parse_sexp(sexp: str) -> Any:
    re_iter = re.finditer(term_regex, sexp)
    rv = list(_parse_sexp_internal(re_iter))

    for leftover in re_iter:
        lparen, rparen, *rest = leftover.groups()
        if lparen or any(rest):
            raise SexprError(f'Leftover garbage after end of expression at position {leftover.start()}')  # noqa: E501

        elif rparen:
            raise SexprError(f'Unbalanced closing parenthesis at position {leftover.start()}')

    if len(rv) == 0:
        raise SexprError('No or empty expression')

    if len(rv) > 1:
        raise SexprError('Missing initial opening parenthesis')

    return rv[0]


def _parse_sexp_internal(re_iter) -> Any:
    for match in re_iter:
        lparen, rparen, float_num, integer_num, quoted_str, bare_str = match.groups()

        if lparen:
            yield list(_parse_sexp_internal(re_iter))
        elif rparen:
            break
        elif bare_str is not None:
            yield bare_str
        elif quoted_str is not None:
            yield quoted_str.replace('\\"', '"')
        elif float_num:
            yield float(float_num)
        elif integer_num:
            yield int(integer_num)


# Form a valid sexpr (single line)
def SexprItem(val: Any, key: Optional[str] = None) -> str:
    if key:
        fmt = "(" + key + " {val})"
    else:
        fmt = "{val}"

    if val is None or isinstance(val, str) and len(val) == 0:
        val = '""'
    elif isinstance(val, (list, tuple)):
        val = " ".join([SexprItem(v) for v in val])
    elif isinstance(val, dict):
        values = []
        for key in val.keys():
            values.append(SexprItem(val[key], key))
        val = " ".join(values)
    elif isinstance(val, float):
        val = str(round(val, 10)).rstrip("0").rstrip(".")
    elif isinstance(val, int):
        val = str(val)
    elif isinstance(val, str) and re.search(r"[\s()\"]", val):
        val = '"%s"' % repr(val)[1:-1].replace('"', r"\"")

    return fmt.format(val=val)


class SexprBuilder:
    def __init__(self, key):
        self.indent: int = 0
        self.output: str = ""
        self.items = []
        if key is not None:
            self.startGroup(key, newline=False)

    def _indent(self) -> None:
        self.output += " " * 2 * self.indent

    def _newline(self) -> None:
        self.output += "\n"

    def _addItems(self) -> None:
        self.output += " ".join(str(i) for i in self.items)
        self.items = []

    def startGroup(
        self, key: Optional[Any] = None, newline: bool = True, indent: bool = False
    ) -> None:
        self._addItems()
        if newline and indent:
            self.indent += 1
        if newline:
            self._newline()
            self._indent()
        self.output += "("
        if key:
            self.output += str(key) + " "

    def endGroup(self, newline: bool = True) -> None:
        self._addItems()
        if newline:
            self._newline()
            if self.indent > 0:
                self.indent -= 1
            self._indent()
        self.output += ")"

    def addOptItem(self, key, item, newline: bool = True, indent: bool = False):
        if item in [None, 0, False]:
            return

        self.addItems({key: item}, newline=newline, indent=indent)

    def addItem(self, item, newline: bool = True, indent: bool = False):
        self._addItems()
        if newline and indent:
            self.indent += 1
        if newline:
            self.newLine()
        self.items.append(SexprItem(item))

    # Add a (preformatted) item
    def addItems(self, items, newline: bool = True, indent: bool = False):
        self._addItems()
        if indent:
            self.indent += 1
        if newline:
            self.newLine()
        if isinstance(items, (list, tuple)):
            for item in items:
                self.items.append(SexprItem(item))
        else:
            self.items.append(SexprItem(items))

    def newLine(self, indent: bool = False) -> None:
        self._addItems()
        self._newline()
        if indent:
            self.indent += 1
        self._indent()

    def unIndent(self) -> None:
        if self.indent > 0:
            self.indent -= 1


def build_sexp(exp, indent='  ') -> str:
    # Special case for multi-values
    if isinstance(exp, list):
        joined = '('
        for i, elem in enumerate(exp):
            if 1 <= i <= 5 and len(joined) < 120 and not isinstance(elem, list):
                joined += ' '
            elif i >= 1:
                joined += '\n' + indent
            joined += build_sexp(elem, indent=f'{indent}  ')
        return joined + ')'

    if exp == '':
        return '""'

    return str(exp)


def format_sexp(sexp: str, indentation_size: int = 2, max_nesting: int = 2) -> str:
    out = ''
    n = 0
    for match in re.finditer(term_regex, sexp):
        indentation = ""
        lparen, rparen, float_num, integer_num, quoted_str, bare_str = match.groups()
        if lparen:
            if out:
                if n <= max_nesting:
                    if out[-1] == ' ':
                        out = out[:-1]
                    indentation = '\n' + (' ' * indentation_size * n)
                else:
                    if out[-1] == ')':
                        out += ' '
            n += 1
            out += indentation + '('
        elif rparen:
            if out and out[-1] == ' ':
                out = out[:-1]
            n -= 1
            out += indentation + ')'
        elif float_num:
            out += indentation + float_num + ' '
        elif integer_num:
            out += indentation + integer_num + ' '
        elif quoted_str is not None:
            out += f'{indentation}"{quoted_str}" '
        elif bare_str is not None:
            out += indentation + bare_str + ' '

    out += '\n'
    return out


if __name__ == "__main__":
    sexp = """ ( ( data "quoted data" 123 4.5)
         (data "with \\"escaped quotes\\"")
         (data (123 (4.5) "(more" "data)")))"""

    print("Input S-expression:")
    print(sexp)
    parsed = parse_sexp(sexp)
    print("\nParsed to Python:", parsed)

    print("\nThen back to: '%s'" % build_sexp(parsed))
    print("\nThen back to: '%s'" % format_sexp(build_sexp(parsed)))
