# -*- coding=utf-8 -*-

from ast import Module, parse
from textwrap import dedent

import astunparse
import pytest

from pyoptimizer.ast.scope import Scope, ScopingVisitor
from pyoptimizer.ast.usages import UsagesVisitor
from pyoptimizer.optimizations.unused import remove_unused_locals

tests = [
    pytest.param(
        """
            def fn():
                x = 123
        """,
        """
        
            def fn():
                pass
        """,
        id="simple unused var",
    ),

    pytest.param(
        """
            def fn():
                x = do_something()
        """,
        """
    
            def fn():
                do_something()
        """,
        id="unused assign with side effect",
    ),

    pytest.param(
        """
            def fn():
                x, y = do_something()
        """,
        """
    
            def fn():
                do_something()
        """,
        id="unused tuple assign with side effect",
    ),

    pytest.param(
        """
            def fn():
                x = 123
                y = 123
        """,
        """
    
            def fn():
                pass
        """,
        id="two unused vars",
    ),

    pytest.param(
        """
            def fn():
                if True:
                    do_something()
        """,
        """
    
            def fn():
                do_something()
        """,
        id="if True",
    ),

    pytest.param(
        """
            def fn():
                while False:
                    do_something()
        """,
        """
    
            def fn():
                pass
        """,
        id="while False",
    ),

    pytest.param(
        """
            def fn():
                while False:
                    do_something()
                else:
                    do_something_else()
        """,
        """
    
            def fn():
                pass
        """,
        id="while False else",
    ),

    pytest.param(
        """
            def fn():
                if False:
                    do_something()
        """,
        """
    
            def fn():
                pass
        """,
        id="if False",
    ),

    pytest.param(
        """
            def fn():
                if True:
                    do_something()
                else:
                    do_something_else()
        """,
        """
    
            def fn():
                do_something()
        """,
        id="if True else",
    ),

    pytest.param(
        """
            def fn():
                if False:
                    do_something()
                elif cond:
                    do_something_elif()
                else:
                    do_something_else()
        """,
        """
    
            def fn():
                if cond:
                    do_something_elif()
                else:
                    do_something_else()
        """,
        id="elif False else",
    ),

    pytest.param(
        """
            def fn():
                if False:
                    do_something()
                else:
                    do_something_else()
        """,
        """
    
            def fn():
                do_something_else()
        """,
        id="if False else",
    ),

    pytest.param(
        """
            def fn():
                return 3 if False else 42
        """,
        """
    
            def fn():
                return 42
        """,
        id="inline-if False",
    ),

    pytest.param(
        """
            def fn():
                return 3 if True else 42
        """,
        """
    
            def fn():
                return 3
        """,
        id="inline-if True",
    ),

    pytest.param(
        """
            def fn():
                pass
                pass
                do_something()
                pass
        """,
        """
    
            def fn():
                do_something()
        """,
        id="remove passes",
    ),
]


@pytest.mark.parametrize("input,expected", tests)
def test_resolving(input, expected):
    tree: Module = parse(dedent(input))
    ScopingVisitor().visit(tree)
    UsagesVisitor(tree._pyo_scope).visit(tree)

    remove_unused_locals(tree)

    assert astunparse.unparse(tree) == dedent(expected)


# Bad
"""
    def fn():
        x, y = do_something()
        return x
"""
