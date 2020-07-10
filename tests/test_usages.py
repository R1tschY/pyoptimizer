from ast import Load, Module, Name, Store, parse
from textwrap import dedent

from pyoptimizer.ast.scope import Scope, ScopingVisitor
from pyoptimizer.ast.usages import UsagesVisitor, get_loads, get_stores


def test_name_usages():
    tree: Module = parse(dedent("""
         a = 1
         z = a + a
    """))

    ScopingVisitor().visit(tree)

    module_scope: Scope = tree._pyo_scope
    UsagesVisitor(module_scope).visit(tree)

    assert len(get_loads(module_scope, "a")) == 2
    assert len(get_stores(module_scope, "a")) == 1
