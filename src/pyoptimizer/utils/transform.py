from ast import Module, NodeTransformer

from pyoptimizer.ast.scope import Scope


class PyoModuleTransformer(NodeTransformer):
    module_scope: Scope

    def __init__(self):
        self.module_scope = None

    def transform(self, module: Module) -> Module:
        self.module_scope = module._pyo_scope
        try:
            return super().visit(module)
        finally:
            self.module_scope = None
