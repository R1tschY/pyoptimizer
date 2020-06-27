# -*- coding=utf-8 -*-
import ast
from ast import AST, AsyncFunctionDef, ClassDef, FunctionDef, Global, ListComp, \
    Module, Name, \
    Nonlocal, \
    Store
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Scope:
    local: bool
    names: List[str] = field(default_factory=list)
    globals_: List[str] = field(default_factory=list)
    nonlocals_: List[str] = field(default_factory=list)
    item: Optional[AST] = None
    parent: Optional["Scope"] = None # TODO

    @classmethod
    def new_global(cls, item: Optional[AST] = None):
        return Scope(local=False, item=item)

    @classmethod
    def new_local(cls, item: Optional[AST] = None, locals: List[str] = None):
        return Scope(local=True, item=item, names=locals or [])


class ScopingVisitor(ast.NodeVisitor):
    current_scope: Scope

    def __init__(self):
        self.current_scope = Scope.new_global()

    def visit_Name(self, node: Name) -> Any:
        node._pyo_scope = self.current_scope

        if isinstance(node.ctx, Store):
            if node.id not in self.current_scope.globals_ and \
                    node.id not in self.current_scope.nonlocals_:
                if node.id not in self.current_scope.names:
                    self.current_scope.names.append(node.id)
                node._pyo_is_local = True
                return

        node._pyo_is_local = node.id in self.current_scope.names

    def visit_Global(self, node: Global) -> Any:
        self.current_scope.globals_.extend(node.names)

    def visit_Nonlocal(self, node: Nonlocal) -> Any:
        self.current_scope.nonlocals_.extend(node.names)

    def visit_FunctionDef(self, node: FunctionDef) -> Any:
        self.current_scope.names.append(node.name)

        node_args = node.args
        args = [arg.arg for arg in node_args.args]
        if node_args.vararg:
            args.append(node_args.vararg.arg)
        args.extend([arg.arg for arg in node_args.kwonlyargs])
        if node_args.kwarg:
            args.append(node_args.kwarg.arg)

        self.visit_scope(node, args)

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> Any:
        self.current_scope.names.append(node.name)
        self.visit_scope(node)

    def visit_ClassDef(self, node: ClassDef) -> Any:
        self.current_scope.names.append(node.name)
        self.visit_scope(node)

    def visit_scope(self, node: AST, locals: List[str] = None):
        outer_scope = self.current_scope
        self.current_scope = Scope.new_local(node, locals)
        node._pyo_scope = self.current_scope
        self.generic_visit(node)
        self.current_scope = outer_scope

    visit_Module = visit_scope
    visit_ListComp = visit_scope
    visit_DictComp = visit_scope
    visit_SetComp = visit_scope
    visit_GeneratorExp = visit_scope
