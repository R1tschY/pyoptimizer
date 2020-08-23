# -*- coding=utf-8 -*-
from ast import Module, dump, parse
from textwrap import dedent

import astunparse
import pytest

from pyoptimizer.ast.scope import ScopingVisitor
from pyoptimizer.ast.usages import UsagesVisitor
from pyoptimizer.optimizations.constant_folding import ConstFolding
from pyoptimizer.optimizations.constant_resolving import resolve_constants

testdata = [
    # pytest.param(
    #     """
    #          a = [1, 2, 3][0]
    #     """,
    #     """
    #          a = 1
    #     """,
    #     id="fold list element",
    # ),
    pytest.param(
        """
             a = len([1, 2, 3])
        """,
        """
             a = 3
        """,
        id="fold len list",
    ),
    pytest.param(
        """
             a = len("abc")
        """,
        """
             a = 3
        """,
        id="fold len str",
    ),
    pytest.param(
        """
             a = len(b"")
        """,
        """
             a = 0
        """,
        id="fold len bytes",
    ),
    pytest.param(
        """
             a = int("5")
        """,
        """
             a = 5
        """,
        id="fold type convert",
    ),
    pytest.param(
        """
             a = [1, 2, 3][:-1]
        """,
        """
             a = [1, 2]
        """,
        id="fold slicing",
    ),
    pytest.param(
        """
             a = list((1, 2, 3))
        """,
        """
             a = [1, 2, 3]
        """,
        id="fold list",
    ),
    pytest.param(
        """
             a = sum((1, 2, 3))
        """,
        """
             a = 6
        """,
        id="fold sum",
    ),
    pytest.param(
        """
             a = str(object=b"", **{"encoding": "utf-8", "errors": "strict"})
        """,
        """
             a = ''
        """,
        id="fold function kwargs",
    ),
    pytest.param(
        """
             a = str(b"", **dict(encoding="utf-8", errors="strict"))
        """,
        """
             a = ''
        """,
        id="fold function kwargs",
    ),
    pytest.param(
        """
             a = min(max(1, 2), 3)
        """,
        """
             a = 2
        """,
        id="fold recursive",
    ),
    pytest.param(
        """
             a = min(max(1, 2), b)
        """,
        """
             a = min(2, b)
        """,
        id="fold part",
    ),
]


@pytest.mark.parametrize("input,expected", testdata)
def test_resolving(input, expected):
    tree: Module = parse(dedent(input))
    ScopingVisitor().visit(tree)
    UsagesVisitor(tree._pyo_scope).visit(tree)

    result = ConstFolding().transform(tree)

    assert astunparse.unparse(result) == dedent(expected)
