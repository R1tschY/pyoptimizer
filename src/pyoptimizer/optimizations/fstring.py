# -*- coding=utf-8 -*-
import re
from ast import AST, BinOp, Mod, Name, NodeTransformer, Str, Tuple
from dataclasses import dataclass
from typing import Iterator, List, NamedTuple, Optional, Union

import pytest

from pyoptimizer.ast.scope import Scope


OLD_FORMAT = re.compile(
    r"%(%|(?:\((\w+)\))?([#\-+ 0]*(\d*)(?:\.\d+)?[diouxXeEfFgGcrsa])|(?P<invalid>))")


class Format(NamedTuple):
    literal_text: str
    field_name: Optional[str]
    format_spec: Optional[str]
    conversion: Optional[str] = None





def parse_old_format(format_str: str) -> Iterator[Format]:
    pos = 0
    for match in OLD_FORMAT.finditer(format_str):
        if match.group(1) == "%":
            literal = format_str[pos:match.start(0) + 1]
            id = None
            format = None
            convertion = None
        elif match.group("invalid") is not None:
            raise ValueError
        else:
            literal = format_str[pos:match.start(0)]
            id = match.group(2) or ""
            format = match.group(3)
            type = format[-1]
            convertion = None
            if type in ("r", "s") and match.group(4) and "-" not in format:
                format = ">" + format

            format = format.replace("-", "")
            if type == "r":
                convertion = "r"
                format = format[:-1]

        yield Format(literal, id, format, convertion)

        pos = match.end(0)

    if pos != len(format_str):
        yield Format(format_str[pos:len(format_str)], None, None, None)





# class FStringReplacer(NodeTransformer):
#
#     def __init__(self, module_scope: Scope):
#         self.module_scope = module_scope
#
#     def visit_BinOp(self, node: BinOp) -> Optional[AST]:
#         if isinstance(node.op, Mod) and isinstance(node.left, Str) \
#             and isinstance(node.right, (Tuple, ))
#
#         return node
