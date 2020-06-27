# -*- coding=utf-8 -*-
import ast
from textwrap import dedent

from pyoptimizer.ast.scope import Scope, ScopingVisitor


def test_func_scope():
    code = """
        def fn():
            a = 1
    """

    tree: ast.Module = ast.parse(dedent(code))

    ScopingVisitor().visit(tree)

    assert isinstance(tree.body[0]._pyo_scope, Scope)
    assert tree.body[0]._pyo_scope.names == ["a"]


def test_func_scope_reset():
    code = """
        def fn():
            a = 1
            
        b = 1
    """

    tree: ast.Module = ast.parse(dedent(code))

    ScopingVisitor().visit(tree)

    assert tree.body[0]._pyo_scope.names == ["a"]
    assert tree._pyo_scope.names == ["b"]
