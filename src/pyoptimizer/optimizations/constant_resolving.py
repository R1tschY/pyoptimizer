# -*- coding=utf-8 -*-
import ast
from ast import (AST, Add, And, Assign, BinOp, BitAnd, BitOr, BitXor, BoolOp,
                 Bytes, Compare, Constant, Div, Expression, FloorDiv, IfExp,
                 Invert, LShift, Load, MatMult, Mod, Module, Mult, Name,
                 NameConstant, NodeTransformer, NodeVisitor, Not, Num, Or, Pow,
                 RShift, Str, Sub, Tuple as AstTuple, UAdd,
                 USub, UnaryOp, expr)
from operator import (__add__, __and__, __floordiv__, __invert__, __lshift__,
                      __matmul__, __mod__, __mul__, __neg__, __not__, __or__,
                      __pow__, __rshift__, __sub__, __truediv__, __xor__)
from typing import Any, Dict, Optional

from pyoptimizer.ast.constants import BIN_OPS, BOOL_OPS, UNARY_OPS
from pyoptimizer.ast.scope import Scope, search_scope
from pyoptimizer.ast.usages import UsagesVisitor, get_stores

NOT_A_CONSTANT = object()
MUTABLE_CONSTANT = object()


def fold_constant(tree: expr) -> Any:
    # TODO: FormattedValue, JoinedStr, Name on builtin

    if isinstance(tree, BoolOp):
        return BOOL_OPS[type(tree.op)](
            fold_constant(expr) for expr in tree.values)
    elif isinstance(tree, BinOp):
        return BIN_OPS[type(tree.op)](
            fold_constant(tree.left), fold_constant(tree.right))
    elif isinstance(tree, UnaryOp):
        return UNARY_OPS[type(tree.op)](fold_constant(tree.operand))
    elif isinstance(tree, IfExp):
        if fold_constant(tree.test):
            return fold_constant(tree.body)
        else:
            return fold_constant(tree.orelse)
    elif isinstance(tree, Compare):
        pass  # TODO
    elif isinstance(tree, (Constant, NameConstant)):
        return tree.value
    elif isinstance(tree, Num):
        return tree.n
    elif isinstance(tree, (Str, Bytes)):
        return tree.s
    elif isinstance(tree, AstTuple):
        if isinstance(tree.ctx, Load):
            return tuple([fold_constant(expr) for expr in tree.elts])
    elif isinstance(tree, Expression):
        return fold_constant(tree.body)

    raise ValueError


def to_immutable_constant(node: AST):
    try:
        return fold_constant(node)
    except (ValueError, TypeError):
        return MUTABLE_CONSTANT


def value_to_ast(value: object) -> expr:
    # TODO: complex
    try:
        return ast.parse(repr(value), mode="eval").body
    except SyntaxError:
        raise RuntimeError(f"Failed to convert {value!r} to ast")


def get_or_create_constant_info(scope: Scope) -> Dict[str, object]:
    if hasattr(scope, "_pyo_constants"):
        return scope._pyo_constants

    result = {}
    scope._pyo_constants = result
    return result


def resolve_constants(tree: Module) -> AST:
    ConstSearcher(tree._pyo_scope).visit(tree)
    return ConstResolving(tree._pyo_scope).visit(tree)


class ConstSearcher(NodeVisitor):
    DEPENDS_ON = [UsagesVisitor]

    def __init__(self, module_scope: Scope):
        self.module_scope = module_scope

    def visit_Assign(self, node: Assign):
        # TODO: check for Final[int]
        # TODO: support multiple targets
        if len(node.targets) == 1 and isinstance(node.targets[0], Name):
            constant = to_immutable_constant(node.value)
            if constant is not MUTABLE_CONSTANT:
                id = node.targets[0].id
                scope = search_scope(node.targets[0], id, self.module_scope)
                if scope is not None and len(get_stores(scope, id)) == 1:
                    assert node.targets[0] is get_stores(scope, id)[0]
                    cinfo = get_or_create_constant_info(scope)
                    if id not in cinfo:
                        cinfo[id] = constant


class ConstResolving(NodeTransformer):

    def __init__(self, module_scope: Scope):
        self.module_scope = module_scope

    def visit_Name(self, node: Name) -> Optional[AST]:
        if isinstance(node.ctx, Load):
            scope = search_scope(node, node.id, self.module_scope)
            if scope is not None and hasattr(scope, "_pyo_constants") and \
                    node.id in scope._pyo_constants:
                return value_to_ast(scope._pyo_constants[node.id])

        return node


