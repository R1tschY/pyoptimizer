# -*- coding=utf-8 -*-
from ast import AST, Assign, BoolOp, Expr, FunctionDef, Global, Load, Name, \
    NodeTransformer, \
    Nonlocal, \
    Pass, Store, expr, stmt
from typing import Any, List, Optional

from pyoptimizer.ast.scope import Scope
from pyoptimizer.ast.usages import get_loads, get_stores
from pyoptimizer.optimizations.constant_resolving import MUTABLE_CONSTANT, \
    fold_constant, \
    to_immutable_constant

_PYO_UNUSED = "_pyo_unused"


def remove_unused_locals(tree: AST):
    Cleanup(tree._pyo_scope).visit(tree)


def has_side_effects(tree: expr):
    constant = to_immutable_constant(tree)
    if constant is not MUTABLE_CONSTANT:
        return False

    # TODO: List, set, dict

    if isinstance(tree, Name):
        return False

    return True


def remove_passes(stmts: List[stmt]) -> List[stmt]:
    stmts = [
        stmt for stmt in stmts if not isinstance(stmt, Pass)
    ]
    return stmts if stmts else [Pass()]


class Cleanup(NodeTransformer):

    def __init__(self, module_scope: Scope):
        self.module_scope = module_scope

    def visit_FunctionDef(self, node: FunctionDef) -> Optional[AST]:
        scope = node._pyo_scope

        # find unused vars
        for name in scope.locals_:
            if len(get_loads(scope, name)) == 0:
                for usage in scope.locals_[name]:
                    if isinstance(usage, Name):
                        # usage.id = _PYO_UNUSED
                        usage._pyo_unused = True
                    elif isinstance(usage, (Nonlocal, Global)):
                        usage.names.remove(name)
                    # TODO: elif IMport

        node = self.generic_visit(node)

        # remove passes
        node.body = [
            stmt for stmt in node.body if not isinstance(stmt, Pass)
        ]
        if not node.body:
            node.body = [Pass()]
        return node

    def visit_Global(self, node: Global) -> Any:
        # remove empty global
        if not node.names:
            return Pass()
        return node

    def visit_Nonlocal(self, node: Global) -> Any:
        # remove empty nonlocal
        if not node.names:
            return Pass()
        return node

    def visit_Assign(self, node: Assign) -> Any:
        unused = all(
            n for n in node.targets
            if isinstance(n, Name) and hasattr(n, "_pyo_unused"))
        if unused:
            if has_side_effects(node.value):
                return Expr(node.value)
            else:
                return Pass()
        return node

    # def visit_Name(self, node: Name) -> Optional[AST]:
    #     if isinstance(node.ctx, Load):
    #         scope = search_scope(node, node.id, self.module_scope)
    #         if scope is not None and hasattr(scope, "_pyo_constants") and \
    #                 node.id in scope._pyo_constants:
    #             return constant_to_ast(scope._pyo_constants[node.id])
    #
    #     return node
