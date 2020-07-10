# -*- coding=utf-8 -*-
from ast import Global, Load, Name, NodeVisitor, Nonlocal, Store
from typing import Any, List

from pyoptimizer.ast.scope import Scope, ScopingVisitor, search_scope


def get_loads(scope: Scope, id: str) -> List[Name]:
    return [
        u for u in scope.locals_[id]
        if isinstance(u, Name) and isinstance(u.ctx, Load)
    ]


def get_stores(scope: Scope, id: str) -> List[Name]:
    return [
        u for u in scope.locals_[id]
        if isinstance(u, Name) and isinstance(u.ctx, Store)
    ]


class UsagesVisitor(NodeVisitor):

    DEPENDS_ON = [ScopingVisitor]

    def __init__(self, module_scope: Scope):
        self.module_scope = module_scope

    def visit_Name(self, node: Name) -> Any:
        scope = search_scope(node, node.id)
        if scope is None:
            scope = self.module_scope
        scope.locals_[node.id].append(node)

    def visit_Global(self, node: Global) -> Any:
        for name in node.names:
            self.module_scope.locals_[name].append(node)

    def visit_Nonlocal(self, node: Nonlocal) -> Any:
        for name in node.names:
            scope = search_scope(node, name)
            scope.locals_[name].append(node)


