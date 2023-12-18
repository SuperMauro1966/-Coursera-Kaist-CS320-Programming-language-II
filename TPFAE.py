from typing import Dict, Callable
from functools import partial
import logging

# typed FAE with pairs

"""
abstract syntax
e ::=   n
    |   e + e
    |   x
    |   lx:t.e
    |   e e
    |   (e , e)     Pair(f, s)
    |   e.1         First(p)
    |   e.2         Second(p)

t ::=   num
    |   t -> t
    |   t x t 

Note:
    l = for lambda letter
    t = for tau letter

"""

# create logger
logging.basicConfig()

logger = logging.getLogger("KVAE-FORC")
logger.setLevel(logging.DEBUG)

# roots for different types

# expression
class Expression():
    pass

# Value
class Value():
    pass

# continuation
Cont = Callable[[Value], Value]

# type of environment
Env = Dict[str, Value]
EmptyEnv = {}

# type of num expressions
NumFunc = Callable[[int, int], int]

class NumV(Value):
    def __init__(self, n: int):
        self.n = n
    def __str__(self) -> str:
        return f"NumV({self.n})"

class CloV(Value):
    def __init__(self, param: str, body: Expression, env: Env):
        self.param = param
        self.body = body
        self.env = env
    def __str__(self) -> str:
        return f"CloV({self.param}, {self.body}, {self.env})"

class PairV(Value):
    def __init__(self, first: Value, second: Value) -> None:
        self.first = first
        self.second = second

# types
class Type():
    pass

class NumT(Type):
    pass

class ArrowT(Type):
    def __init__(self, param: Type, result: Type) -> None:
        self.param = param
        self.result = result
        
class PairT(Type):
    def __init__(self, left: Type, right: Type)-> None:
        self.left = left
        self.right = right

# type environment
TypeEnv = Dict[str, Type]
EmptyTypeEnv = {}

# types of expressions
class Num(Expression):
    def __init__(self, n):
        self.n = n
    def __str__(self) -> str:
        return f"Num({self.n})"

class Add(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __str__(self) -> str:
        return f"Add({self.left}, {self.right})"
    
class Sub(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __str__(self) -> str:
        return f"Sub({self.left}, {self.right})"
    
class Id(Expression):
    def __init__(self, name: str):
        self.name = name
    def __str__(self) -> str:
        return f"Id({self.name})"
    
class App(Expression):
    def __init__(self, f_expr: Expression, val: Expression):
        self.f_expr = f_expr
        self.val = val
    def __str__(self) -> str:
        return f"App({self.f_expr}, {self.val} )"

class Fun(Expression):
    def __init__(self, par_name: str, ty: Type, body: Expression):
        self.par_name = par_name
        self.body = body
    def __str__(self) -> str:
        return f"Fun({self.par_name}, {self.body})"

class Pair(Expression):
    def __init__(self, first: Expression, second: Expression):
        self.first = first
        self.second = second
    def __str__(self) -> str:
        return f"Pair({self.first}, {self.second})"

class First(Expression):
    def __init__(self, p: Pair):
        self.p = p
    def __str__(self) -> str:
        return f"First({self.p})"

class Second(Expression):
    def __init__(self, p: Pair):
        self.p = p
    def __str__(self) -> str:
        return f"Second({self.p})"
    
# exceptions
# execution exception
class InterPreterException(Exception):
    pass

class FreeIdentifierError(InterPreterException):
    pass

class UnknownFunction(InterPreterException):
    pass
 
class NotNumExpression(InterPreterException):
    pass

class ClosureError(InterPreterException):
    pass

class PairError(InterPreterException):
    pass

# type exception
class TypeException(Exception):
    pass

class WrongTypeException(TypeException):
    pass

# isSame
def isSame(left: Type, right: Type)->bool:
    if isinstance(left, NumT) and isinstance(right, NumT):
        return True
    elif isinstance(left, ArrowT) and isinstance(right, ArrowT):
        return isSame(left.param, right.param) and \
                isSame(left.result, right.result)
    else:
        return False

def notype(msg: str)->None:
    raise WrongTypeException(msg)
    
# mustSame
def mustSame(left: Type, right: Type)->Type:
    if not isSame(left, right):
        return notype(f"{left!s} is not of type {right!s}")

# typeCheck
def typeCheck(expr: Expression, tyEnv: TypeEnv)->Type:
    if isinstance(expr, Num):
        return NumT()
    elif isinstance(expr, Add):
        mustSame(typeCheck(expr.left, tyEnv), NumT)
        mustSame(typeCheck(expr.right, tyEnv), NumT)
        return NumT()
    elif isinstance(expr, Id):
        try:
            return tyEnv[expr.name]
        except KeyError:
            return notype(f"{expr.name} is a free identifier")
    elif isinstance(expr, Fun):
        return ArrowT(
            expr.ty,
            typeCheck(expr.body, dict(tyEnv, **{expr.par_name: expr.ty})))
    elif isinstance(expr, App):
        funT=  typeCheck(expr.f_expr, tyEnv),
        argT = typeCheck(expr.val)
        if isinstance(funT, ArrowT):
            if isSame(funT, argT):
                return funT.result
        else:
            notype(f"apply {argT!s} to {funT!s}")
    elif isinstance(expr, Pair):
        return PairT(
            typeCheck(expr, tyEnv),
            typeCheck(expr.right, tyEnv))
    elif isinstance(expr, First):
        p_type = typeCheck(expr.p, tyEnv)
        if isSame(p_type, PairT):
            return p_type.first
        else:
            notype(f"{p_type!s} is not a PairT")
    elif isinstance(expr, Second):
        p_type = typeCheck(expr.p, tyEnv)
        if isSame(p_type, PairT):
            return p_type.second
        else:
            notype(f"{p_type!s} is not a PairT")

# eval
def eval(expr: Expression)->Value:
    typeCheck(expr, EmptyTypeEnv)
    interp(expr, EmptyEnv)

def interp(expr : Expression, env: Env) -> Value:
    if isinstance(expr, Num):
        return NumV(expr.n)
    elif isinstance(expr, Add):
        return numAddV(interp(expr.left, env), interp(expr.right, env))
    elif isinstance(expr, Sub):
        return numSubV(interp(expr.left, env), interp(expr.right, env))
    elif isinstance(expr, Id):
        return lookup(expr.name, env)
    elif isinstance(expr, Fun):
        return CloV(expr.par_name, expr.body, env)
    elif isinstance(expr, App):
        f = interp(expr.f_expr, env)
        if isinstance(f, CloV):
            # env = dynamic scop
            # f.env = static scope
            return interp(f.body, dict(f.env, **{f.param: interp(expr.val, env)}))
        else:
            raise ClosureError(f"not a closure {f}")
    elif isinstance(expr, Pair):
        return PairV(interp(expr.first, env), interp(expr.second, env))
    elif isinstance(expr, First):
        p_temp = interp(expr.p.first, env)
        if isinstance(p_temp, PairV):
            return p_temp.first
        raise PairError(f"not a pair {p_temp!s}") 
    elif isinstance(expr, Second):
        p_temp = interp(expr.p.second, env)
        if isinstance(p_temp, PairV):
            return p_temp.second
        raise PairError(f"not a pair {p_temp!s}") 

"""
Note that 
Val is syntactic sugar for CloV

CloV
    interp(f.body, dict(f.env, **{f.param: interp(expr.val, env)}))

Val
    interp(expr.body, dict(env, **{expr.name : res}))

    { val x = 10; x} è quivalente a ( x => x )(10)
"""

def lookup(var_name:str, env: Env):
    try:
        return env[var_name]
    except KeyError:
        raise FreeIdentifierError(f"free identifier {var_name}")
    
def numOp(op: NumFunc, lexpr: Value, rexpr: Value)-> Value:
    if isinstance(lexpr, NumV) and isinstance (rexpr, NumV):
        return NumV(op(lexpr.n, rexpr.n))
    else:
        raise NotNumExpression(f"not both numbers: {lexpr} {rexpr}")

numAddV = partial(numOp, lambda x,y: x + y)
numSubV = partial(numOp, lambda x,y: x - y)

# test section
if __name__ == "__main__":
    assert interp(Num(10), {}).n  == 10
    assert interp(Add(Num(10), Num(20)), {}).n == 30
    assert interp(Sub(Num(10), Num(20)), {}).n == -10
    assert interp(Add(Num(0), Num(3)), {}).n == 3

