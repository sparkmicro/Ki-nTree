"""Classes to manage KiCad footprint and symbol library tables

Author:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0

Major changes:
    19.02.2022 - created
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List
from os import path

from kiutils.utils.strings import dequote
from kiutils.utils import sexpr

@dataclass
class Library():
    """The ``library`` token defines either a symbol library or a footprint library in
    a library table file (``fp_lib_table`` or ``sym_lib_table``)"""

    name: str = ""
    """The ``name`` token defines the name of the library as displayed in the project"""

    type: str = "KiCad"
    """The ``type`` token defines the type of the library, usually ``KiCad``"""

    uri: str = ""
    """The ``uri`` token defines the path to the library files"""

    options: str = ""
    """The ``options`` token (..) TBD"""

    description: str = ""
    """The ``description`` token (..) TBD"""

    @classmethod
    def from_sexpr(cls, exp: list) -> Library:
        """Convert the given S-Expresstion into a Library object

        Args:
            - exp (list): Part of parsed S-Expression ``(lib ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not lib

        Returns:
            - Library: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if exp[0] != 'lib':
            raise Exception("Expression does not have the correct type")

        object = cls()
        for item in exp:
            if item[0] == 'name': object.name = item[1]
            if item[0] == 'type': object.type = item[1]
            if item[0] == 'uri': object.uri = item[1]
            if item[0] == 'options': object.options = item[1]
            if item[0] == 'descr': object.description = item[1]
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

        return f'{indents}(lib (name "{dequote(self.name)}")(type "{dequote(self.type)}")(uri "{dequote(self.uri)}")(options "{dequote(self.options)}")(descr "{dequote(self.description)}")){endline}'

@dataclass
class LibTable():
    """The ``libtable`` token defines the ``fp_lib_table`` or ``sym_lib_table`` file of KiCad"""

    type: str = 'sym_lib_table'
    """The ``type`` token defines the type of the library table. Valid values are ``fp_lib_table`` or
    ``sym_lib_table``."""

    libs: List[Library] = field(default_factory=list)
    """The ``libs`` token holds a list of librarys that this library table object holds"""

    filePath: Optional[str] = None
    """The ``filePath`` token defines the path-like string to the library file. Automatically set when
    ``self.from_file()`` is used. Allows the use of ``self.to_file()`` without parameters."""

    @classmethod
    def from_sexpr(cls, exp: list) -> LibTable:
        """Convert the given S-Expresstion into a LibTable object

        Args:
            - exp (list): Part of parsed S-Expression ``(sym_lib_table ...)`` or ``(fp_lib_table ...)``

        Raises:
            - Exception: When given parameter's type is not a list
            - Exception: When the first item of the list is not lib

        Returns:
            - LibTable: Object of the class initialized with the given S-Expression
        """
        if not isinstance(exp, list):
            raise Exception("Expression does not have the correct type")

        if not (exp[0] == 'fp_lib_table' or exp[0] == 'sym_lib_table'):
            raise Exception("Expression does not have the correct type")

        object = cls()
        object.type = exp[0]
        for item in exp:
            if item[0] == 'lib': object.libs.append(Library().from_sexpr(item))
        return object

    @classmethod
    def from_file(cls, filepath: str, encoding: Optional[str] = None) -> LibTable:
        """Load a library table directly from a KiCad library table file and sets the
        ``self.filePath`` attribute to the given file path.

        Args:
            - filepath (str): Path or path-like object that points to the file
            - encoding (str, optional): Encoding of the input file. Defaults to None (platform 
                                        dependent encoding).

        Raises:
            - Exception: If the given path is not a file

        Returns:
            - LibTable: Object of the LibTable class initialized with the given KiCad library table
        """
        if not path.isfile(filepath):
            raise Exception("Given path is not a file!")

        with open(filepath, 'r', encoding=encoding) as infile:
            item = cls.from_sexpr(sexpr.parse_sexp(infile.read()))
            item.filePath = filepath
            return item

    @classmethod
    def create_new(cls, type: str = 'sym_lib_table') -> LibTable:
        """Creates a new empty library table with its attributes set as KiCad would create it

        Args:
            - type (str): ``fp_lib_table`` or ``sym_lib_table``. Defaults to the latter.

        Returns:
            - Library: Empty library table of given type
        """
        return cls(type=type)

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

        expression = f'{indents}({self.type}\n'
        for lib in self.libs:
            expression += lib.to_sexpr()
        expression += f'{indents}){endline}'
        return expression