from ast import AST, Module, dump, parse
from textwrap import dedent

import astunparse
import pytest

from pyoptimizer.ast.scope import Scope, ScopingVisitor
from pyoptimizer.ast.usages import UsagesVisitor
from pyoptimizer.optimizations.constant_resolving import \
    MUTABLE_CONSTANT, fold_constant, resolve_constants, to_immutable_constant

is_const_testdata = [
    pytest.param("1", 1, id="int"),
    pytest.param("1.0", 1.0, id="float"),
    pytest.param("1+1j", 1+1j, id="complex"),
    pytest.param("'abc'", "abc", id="str"),
    pytest.param("(1, (), (1, 23, 3))", (1, (), (1, 23, 3)), id="tuple"),
    pytest.param("1+1", 1+1, id="addition"),
]


@pytest.mark.parametrize("code,expected", is_const_testdata)
def test_is_const(code, expected):
    tree: AST = parse(code, mode="eval")
    assert fold_constant(tree) == expected


is_nonconst_testdata = [
    pytest.param("a"),
    pytest.param("[]"),
    pytest.param("{1: 3}"),
]


@pytest.mark.parametrize("code", is_nonconst_testdata)
def test_is_nonconst(code):
    tree: AST = parse(code, mode="eval")
    assert to_immutable_constant(tree) is MUTABLE_CONSTANT


testdata = [
    pytest.param(
        """
             a = 1
             z = (a + a)
        """,
        """
             a = 1
             z = (1 + 1)
        """,
        id="replace two in module scope",
    ),
    pytest.param(
        """
            ABC = 1
            
            def a():
                b = ABC
        """,
        """
            ABC = 1
            
            def a():
                b = 1
        """,
        id="replace global in function scope",
    ),
    pytest.param(
        """
            ABC = (1,)
            
            def a():
                b = (1,)
        """,
        """
            ABC = (1,)
            
            def a():
                b = (1,)
        """,
        id="replace tuple global in function scope",
    ),
    pytest.param(
        """
            ABC = 42
            DEF = ABC
            x = ABC
        """,
        """
            ABC = 42
            DEF = 42
            x = 42
        """,
        id="replace constant alias",
    ),
    # pytest.param(
    #     """
    #         ABC = 42
    #         DEF = (ABC + 1)
    #         x = DEF
    #     """,
    #     """
    #         ABC = 42
    #         DEF = (42 + 1)
    #         x = 43
    #     """,
    #     id="computed constant",
    # ),
    pytest.param(
        """
            ABC = (True or complex_fn(45, [56]))
            x = ABC
        """,
        """
            ABC = (True or complex_fn(45, [56]))
            x = True
        """,
        id="short circuit constant",
    ),
]


@pytest.mark.parametrize("input,expected", testdata)
def test_resolving(input, expected):
    tree: Module = parse(dedent(input))
    ScopingVisitor().visit(tree)
    UsagesVisitor(tree._pyo_scope).visit(tree)

    result = resolve_constants(tree)

    assert astunparse.unparse(result) == dedent(expected)


negative_testdata = [
    # BAD
    pytest.param(
        """
            ABC = (1,)
            def a():
                b = ABC

            ABC = (2,)
        """,
        id="not replace mutable global",
    ),
    pytest.param(
        """
            ABC = (1,)
            def a():
                global ABC
                ABC = 4
                b = ABC

            ABC = (2,)
        """,
        id="not replace mutable global in function scope",
    ),
    pytest.param(
        """
            def a():
                ABC = 1
                b = ABC
                ABC = 2
        """,
        id="not replace mutable local",
    ),
    pytest.param(
        """
            def a():
                ABC = 4
                x = ABC
                def b():
                    nonlocal ABC
                    ABC = 10
        """,
        id="not replace mutable nonlocal",
    ),
    pytest.param(
        """
            ABC = []
            b = ABC
        """,
        id="not replace mutable value",
    ),
]


@pytest.mark.parametrize("input", negative_testdata)
def test_not_resolving(input):
    tree: Module = parse(dedent(input))
    ScopingVisitor().visit(tree)
    UsagesVisitor(tree._pyo_scope).visit(tree)

    result = resolve_constants(tree)

    assert dump(result) == dump(tree)

