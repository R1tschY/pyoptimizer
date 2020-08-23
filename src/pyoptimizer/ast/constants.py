from ast import Add, And, BitAnd, BitOr, BitXor, Div, FloorDiv, Invert, LShift, \
    MatMult, \
    Mod, \
    Mult, Not, Or, \
    Pow, \
    RShift, Sub, UAdd, USub
from operator import __add__, __and__, __floordiv__, __invert__, __lshift__, \
    __matmul__, \
    __mod__, \
    __mul__, __neg__, __not__, __or__, \
    __pow__, \
    __rshift__, \
    __sub__, __truediv__, __xor__

BOOL_OPS = {
    And: all,
    Or: any,
}

BIN_OPS = {
    Add: __add__,
    Sub: __sub__,
    Mult: __mul__,
    MatMult: __matmul__,
    Div: __truediv__,
    Mod: __mod__,
    Pow: __pow__,
    LShift: __lshift__,
    RShift: __rshift__,
    BitOr: __or__,
    BitXor: __xor__,
    BitAnd: __and__,
    FloorDiv: __floordiv__,
}

UNARY_OPS = {
    Invert: __invert__,
    Not: __not__,
    UAdd: lambda x: x,
    USub: __neg__
}
