""" DISCLAIMER
Sexpr classes and methods were directly imported from: https://gitlab.com/kicad/libraries/kicad-library-utils
Last import date: Dec 1st, 2022
"""

"""
code extracted from: http://rosettacode.org/wiki/S-Expressions
"""

import re
from typing import Any, Optional

dbg: bool = False

term_regex = r"""(?mx)
    \s*(?:
        (?P<brackl>\()|
        (?P<brackr>\))|
        (?P<num>[+-]?\d+\.\d+(?=[\ \)])|\-?\d+(?=[\ \)]))|
        (?P<sq>"([^"]|(?<=\\)")*")|
        (?P<s>[^(^)\s]+)
       )"""


class SexprError(ValueError):
    pass


def parse_sexp(sexp: str) -> Any:
    stack = []
    out = []
    if dbg:
        print("%-6s %-14s %-44s %-s" % tuple("term value out stack".split()))
    for termtypes in re.finditer(term_regex, sexp):
        term, value = [(t, v) for t, v in termtypes.groupdict().items() if v][0]
        if dbg:
            print("%-7s %-14s %-44r %-r" % (term, value, out, stack))

        if term == "brackl":
            stack.append(out)
            out = []
        elif term == "brackr":
            if not stack:
                raise SexprError("Trouble with nesting of brackets")
            tmpout, out = out, stack.pop(-1)
            out.append(tmpout)
        elif term == "num":
            v = float(value)
            if v.is_integer():
                v = int(v)
            out.append(v)
        elif term == "sq":
            out.append(value[1:-1].replace(r"\"", '"'))
        elif term == "s":
            out.append(value)
        else:
            raise NotImplementedError(
                "The term '{}' with value '{}' is unknown.".format(term, value)
            )
    if stack:
        raise SexprError("Trouble with nesting of brackets")
    return out[0]


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


def build_sexp(exp, key=None) -> str:
    out = ""

    # Special case for multi-values
    if isinstance(exp, list):
        out += "(" + " ".join(build_sexp(x) for x in exp) + ")"
        return out
    # elif isinstance(exp, str) and re.search(r'[\s()]', exp):
    #    out += '"%s"' % repr(exp)[1:-1].replace('"', r'\"')
    #    print(exp, '"%s"' % repr(exp)[1:-1].replace('"', r'\"'))
    elif isinstance(exp, float):
        out += str(exp)
    elif isinstance(exp, int):
        out += str(exp)
    elif isinstance(exp, str):
        out += exp
    else:
        if exp == "":
            out += '""'
        else:
            out += "%s" % exp

    if key is not None:
        out = "({key} {val})".format(key=key, val=out)

    return out


def format_sexp(sexp: str, indentation_size: int = 2, max_nesting: int = 2) -> str:
    out = ""
    n = 0
    for termtypes in re.finditer(term_regex, sexp):
        indentation = ""
        term, value = [(t, v) for t, v in termtypes.groupdict().items() if v][0]
        if term == "brackl":
            if out:
                if n <= max_nesting:
                    if out[-1] == " ":
                        out = out[:-1]
                    indentation = "\n" + (" " * indentation_size * n)
                else:
                    if out[-1] == ")":
                        out += " "
            n += 1
        elif term == "brackr":
            if out and out[-1] == " ":
                out = out[:-1]
            n -= 1
        elif term == "num":
            value += " "
        elif term == "sq":
            value += " "
        elif term == "s":
            value += " "
        else:
            raise NotImplementedError(
                "The term '{}' with value '{}' is unknown.".format(term, value)
            )

        out += indentation + value

    out += "\n"
    return out


if __name__ == "__main__":
    sexp = """ ( ( data "quoted data" 123 4.5)
         (data "with \\"escaped quotes\\"")
         (data (123 (4.5) "(more" "data)")))"""

    print("Input S-expression: %r" % (sexp,))
    parsed = parse_sexp(sexp)
    print("\nParsed to Python:", parsed)

    print("\nThen back to: '%s'" % build_sexp(parsed))
    print("\nThen back to: '%s'" % format_sexp(build_sexp(parsed)))
