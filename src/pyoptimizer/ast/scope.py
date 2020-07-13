# -*- coding=utf-8 -*-
import weakref
from weakref import ReferenceType
from ast import AST, AsyncFunctionDef, ClassDef, Del, FunctionDef, Global, \
    Name, \
    NodeVisitor, Nonlocal, \
    Store
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Iterator, List, Optional


@dataclass
class Scope:
    fn_scope: bool
    item: Optional[AST]
    parent: Optional["Scope"]
    locals_: Dict[str, List[AST]] = field(default_factory=list)
    globals_: List[str] = field(default_factory=list)
    nonlocals_: List[str] = field(default_factory=list)
    children: List[ReferenceType] = field(default_factory=list)

    @classmethod
    def new_global(cls, item: Optional[AST] = None):
        return Scope(fn_scope=False, item=item, parent=None)

    @classmethod
    def new_local(
            cls, item: Optional[AST], parent: Optional["Scope"],
            locals: Iterable[str] = ()):
        return Scope(fn_scope=True, parent=parent, item=item,
                     locals_=dict.fromkeys(locals))

    def is_class_scope(self):
        return isinstance(self.item, ClassDef)

    def is_function_scope(self):
        return isinstance(self.item, (FunctionDef, AsyncFunctionDef))


class ScopingVisitor(NodeVisitor):
    current_scope: Scope

    def __init__(self):
        self.current_scope = Scope.new_global()

    def visit_Name(self, node: Name) -> Any:
        node._pyo_scope = self.current_scope

        if isinstance(node.ctx, (Store, Del)):
            if node.id not in self.current_scope.globals_ and \
                    node.id not in self.current_scope.nonlocals_:
                self.current_scope.locals_[node.id] = []
                return

    def visit_Global(self, node: Global) -> Any:
        node._pyo_scope = self.current_scope
        self.current_scope.globals_.extend(node.names)

    def visit_Nonlocal(self, node: Nonlocal) -> Any:
        node._pyo_scope = self.current_scope
        self.current_scope.nonlocals_.extend(node.names)

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_scope.locals_[node.name] = []

        node_args = node.args
        args = [arg.arg for arg in node_args.args]
        if node_args.vararg:
            args.append(node_args.vararg.arg)
        args.extend([arg.arg for arg in node_args.kwonlyargs])
        if node_args.kwarg:
            args.append(node_args.kwarg.arg)

        self.visit_scope(node, True, args)

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> Any:
        self.current_scope.locals_[node.name] = []
        self.visit_scope(node, fn_scope=True)

    def visit_ClassDef(self, node: ClassDef) -> Any:
        self.current_scope.locals_[node.name] = []
        self.visit_scope(node)

    def visit_scope(self, node: AST, fn_scope: bool = False,
                    locals_: List[str] = ()):
        outer_scope = self.current_scope
        self.current_scope = Scope(
            item=node, locals_=dict.fromkeys(locals_),
            fn_scope=fn_scope,
            parent=outer_scope if outer_scope.fn_scope else outer_scope.parent)
        node._pyo_scope = self.current_scope
        self.generic_visit(node)
        self.current_scope = outer_scope

    visit_Module = visit_scope
    visit_ListComp = visit_scope
    visit_DictComp = visit_scope
    visit_SetComp = visit_scope
    visit_GeneratorExp = visit_scope


def iter_scopes(node: AST) -> Iterator[Scope]:
    scope: Scope = node._pyo_scope
    while scope is not None:
        yield scope
        scope = scope.parent


def search_scope(node: AST, name: str,
                 module_scope: Optional[Scope] = None,
                 builtin_scope: Optional[Scope] = None) -> Optional[Scope]:
    scope: Scope = node._pyo_scope
    if name in scope.locals_:
        return scope
    elif name in scope.nonlocals_:
        while scope is not None:
            if name in scope.locals_:
                return scope
            scope = scope.parent
        else:
            raise RuntimeError(f"no binding for nonlocal '{name}' found", node)

    # elif name in scope.globals_ or name not in scope.names:
    if module_scope is None:
        return None

    if name in module_scope.locals_:
        return module_scope

    if builtin_scope is None:
        return None

    if name in builtin_scope.locals_:
        return builtin_scope
