# -*- coding=utf-8 -*-
import ast
from ast import AST, Global, Module, Name, Nonlocal, Store
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class Scope:
    local: bool
    names: List[str] = field(default_factory=list)
    global_: List[str] = field(default_factory=list)
    nonlocal_: List[str] = field(default_factory=list)
    item: Optional[AST] = None
    parent: Optional["Scope"] = None # TODO

    @classmethod
    def new_global(cls, item: Optional[AST] = None):
        return Scope(local=False, item=item)

    @classmethod
    def new_local(cls, item: Optional[AST] = None):
        return Scope(local=True, item=item)


class ScopingVisitor(ast.NodeVisitor):
    current_scope: Scope

    def __init__(self):
        self.current_scope = Scope.new_global()

    def visit_Name(self, node: Name) -> Any:
        if isinstance(node.ctx, Store):
            self.current_scope.names.append(node.id)

    def visit_Global(self, node: Global) -> Any:
        self.current_scope.global_.extend(node.names)

    def visit_Nonlocal(self, node: Nonlocal) -> Any:
        self.current_scope.nonlocal_.extend(node.names)

    def visit_Module(self, node: Module) -> Any:
        outer_scope = self.current_scope
        self.current_scope = Scope.new_global(node)
        node._pyo_scope = self.current_scope
        self.generic_visit(node)
        self.current_scope = outer_scope

    def visit_FunctionDef(self, node: Module) -> Any:
        outer_scope = self.current_scope
        self.current_scope = Scope.new_local(node)
        node._pyo_scope = self.current_scope
        self.generic_visit(node)
        self.current_scope = outer_scope

    def visit_ClassDef(self, node: Module) -> Any:
        outer_scope = self.current_scope
        self.current_scope = Scope.new_local(node)
        node._pyo_scope = self.current_scope
        self.generic_visit(node)
        self.current_scope = outer_scope
