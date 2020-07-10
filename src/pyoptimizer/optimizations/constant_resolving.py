# -*- coding=utf-8 -*-
import ast
from ast import AST, Assign, Constant, Del, Load, Module, Name, Store
from copy import deepcopy
from typing import Any, Dict, Optional

from pyoptimizer.ast.scope import Scope, search_scope
from pyoptimizer.ast.usages import UsagesVisitor, get_loads, get_stores

NOT_A_CONSTANT = object()


def is_immutable_value(value: object):
    if value is None:
        return True
    elif isinstance(value, (bool, int, complex, str, bytes, float)):
        return True
    elif isinstance(value, tuple):
        return all(map(is_immutable_value, value))
    else:
        return False


def is_immutable_constant(node: AST):
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError):
        return False

    return is_immutable_value(value)


def get_or_create_constant_info(scope: Scope) -> Dict[str, AST]:
    if hasattr(scope, "_pyo_constants"):
        return scope._pyo_constants

    result = {}
    scope._pyo_constants = result
    return result


def resolve_constants(tree: Module) -> AST:
    ConstSearcher(tree._pyo_scope).visit(tree)
    return ConstResolving(tree._pyo_scope).visit(tree)


class ConstSearcher(ast.NodeVisitor):
    DEPENDS_ON = [UsagesVisitor]

    def __init__(self, module_scope: Scope):
        self.module_scope = module_scope

    def visit_Assign(self, node: Assign):
        # TODO: check for Final[int]
        # TODO: support multiple targets
        if len(node.targets) == 1 and is_immutable_constant(node.value) \
                and isinstance(node.targets[0], Name):
            id = node.targets[0].id
            scope = search_scope(node.targets[0], id)
            if scope is None:
                scope = self.module_scope
            if len(get_stores(scope, id)) == 1:
                assert node.targets[0] is get_stores(scope, id)[0]
                cinfo = get_or_create_constant_info(scope)
                if id not in cinfo:
                    cinfo[id] = node.value


class ConstResolving(ast.NodeTransformer):

    def __init__(self, module_scope: Scope):
        self.module_scope = module_scope

    def visit_Name(self, node: Name) -> Optional[AST]:
        if isinstance(node.ctx, Load):
            scope = search_scope(node, node.id)
            if scope is None:
                scope = self.module_scope

            if hasattr(scope, "_pyo_constants") and \
                    node.id in scope._pyo_constants:
                return deepcopy(scope._pyo_constants[node.id])

        return node


