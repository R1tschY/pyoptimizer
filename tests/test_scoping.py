# -*- coding=utf-8 -*-
import ast
from textwrap import dedent
from types import CodeType, FunctionType
from typing import Dict, List, Tuple

import pytest

from pyoptimizer.ast.scope import Scope, ScopingVisitor

testdata = [
    pytest.param(
        """
            def fn():
                a = 1
        """,
        id="func scope"
    ),
    pytest.param(
        """
            def fn():
                a = 1
                
            b = 1
        """,
        id="func_scope_reset"
    ),
    pytest.param(
        """
            def fn():
                a = 1
                a = 1
                a = 1
        """,
        id="func no dups"
    ),

    pytest.param(
        """
            def fn(a, b, c):
                pass
        """,
        id="func args"
    ),
    pytest.param(
        """
            def fn(a, *args, **kwargs):
                pass
        """,
        id="func *args"
    ),
    pytest.param(
        """
            def fn(abc=None, **kwargs):
                pass
        """,
        id="func kwargs"
    ),

    pytest.param(
        """
            def fn():
                for i in range(10000):
                    pass
        """,
        id="func_scope_for"
    ),
    pytest.param(
        """
            def fn():
                for i in range(10000):
                    for j in range(10000):
                        pass
        """,
        id="func_scope_for_for"
    ),

    # Comp
    pytest.param(
        """
            def fn():
                return [i for i in range(10000)]
        """,
        id="func listcomp"
    ),
    pytest.param(
        """
            def fn():
                return {i: None for i in range(10000)}
        """,
        id="func dictcomp"
    ),
    pytest.param(
        """
            def fn():
                return {i for i in range(10000)}
        """,
        id="func setcomp"
    ),
    pytest.param(
        """
            def fn():
                return (i for i in range(10000))
        """,
        id="func generator"
    ),

    # Closures
    pytest.param(
        """
            def fn():
                return lambda x: x
        """,
        id="func lambda"
    ),
    pytest.param(
        """
            def fn():
                def closure():
                    x = 1
        """,
        id="func closure"
    ),
    pytest.param(
        """
            def fn():
                class A:
                    x = 1
        """,
        id="func closure"
    ),

    # global/nonlocal
    pytest.param(
        """
            def fn():
                global x, y
                x = 1
        """,
        id="func global"
    ),
    # pytest.param(
    #     """
    #         x = 1
    #
    #         def fn():
    #             nonlocal x
    #             x = 1
    #     """,
    #     id="func nonlocal"
    # ),
]


@pytest.mark.parametrize("code", testdata)
def test_func_scope(code):
    code = dedent(code)
    tree: ast.Module = ast.parse(code)

    ScopingVisitor().visit(tree)

    _, locals_ = scoped_exec(code)
    assert tuple(tree.body[0]._pyo_scope.names) == local_vars(locals_["fn"])


def scoped_exec(code: str) -> Tuple[Dict, Dict]:
    globals_ = {}
    locals_ = {}
    exec(code, globals_, locals_)
    return globals_, locals_


def local_vars(fn: FunctionType) -> Tuple[str]:
    return fn.__code__.co_varnames
