from ast import AST, And, BinOp, BoolOp, Bytes, Call, Compare, Constant, \
    Dict, Expression, IfExp, \
    Load, Name, \
    NameConstant, \
    Num, Or, Str, expr, UnaryOp, Tuple as AstTuple, List as AstList, \
    Set as AstSet
from typing import Any, Optional
import builtins

from pyoptimizer.ast.constants import BIN_OPS, BOOL_OPS, UNARY_OPS
from pyoptimizer.ast.scope import Scope, search_name_scope, search_scope
from pyoptimizer.optimizations.constant_resolving import value_to_ast
from pyoptimizer.utils.transform import PyoModuleTransformer


# Const Args -> Const Return
CONSTFN_BUILTINS = {
    "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
    "callable", "chr", "complex", "dict", "dir", "divmod", "enumerate",
    "filter", "float", "format", "frozenset", "hasattr", "getattr", "hash",
    "hex", "int", "isinstance", "issubclass", "len", "list", "map", "max",
    "min", "oct", "ord", "pow", "repr", "reversed", "round", "set", "slice",
    "sorted", "str", "sum", "tuple", "vars"
}

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
    elif isinstance(tree, AstList):
        if isinstance(tree.ctx, Load):
            return [fold_constant(expr) for expr in tree.elts]
    elif isinstance(tree, Dict):
        return {
            fold_constant(key): fold_constant(value)
            for key, value in zip(tree.keys, tree.values)
        }
    elif isinstance(tree, AstSet):
        return {fold_constant(value) for value in tree.elts}
    elif isinstance(tree, Call):
        pass
    elif isinstance(tree, Expression):
        return fold_constant(tree.body)
    # TODO:
    raise ValueError



class ConstFnRegistry:

    def __init__(self):
        self.registry = {}

    def load_builtins(self):
        for name in CONSTFN_BUILTINS:
            self.registry[name] = getattr(builtins, name)


class ConstFolding(PyoModuleTransformer):

    def visit_Call(self, node: Call) -> Optional[AST]:
        if isinstance(node.func, Name) and node.func.id in CONSTFN_BUILTINS:
            # maybe a builtin
            scope = search_name_scope(node.func, module_scope=self.module_scope)
            if scope is None:
                # is a builtin
                try:
                    args = [fold_constant(arg) for arg in node.args]
                    keywords = [
                        (keyword.arg, fold_constant(keyword.value))
                        for keyword in node.keywords
                    ]
                except ValueError:
                    pass
                else:
                    # foldable args
                    kwargs = {}
                    for id, arg in keywords:
                        if id is None:
                            # **kwargs
                            kwargs.update(arg)
                        else:
                            # kwarg=arg
                            kwargs[id] = arg

                    const = getattr(builtins, node.func.id)(*args, **kwargs)
                    return value_to_ast(const)

        return self.generic_visit(node)

    # TODO:
    # def visit_If(self, node: If) -> Any:
    #     pass
