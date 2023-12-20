from typing import Dict, Callable
from functools import partial
import logging

"""
abstract syntax
e ::=   n
    |   e + e
    |   x
    |   lx:t.e
    |   e e
    |   if0 e1 e2 e3
    |   def x(x:t):t = e; e

t ::=   num
    |   t -> t


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

# type of environment
Env = Dict[str, Value]
EmptyEnv = {}

# type of num expressions
NumFunc = Callable[[int, int], int]

# Values
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


# types
class Type():
    pass

class NumT(Type):
    pass

class ArrowT(Type):
    def __init__(self, param: Type, result: Type) -> None:
        self.param = param
        self.result = result
        
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

class If0(Expression):
    def __init__(self, condE: Expression, trueE: Expression, falseE: Expression):
        self.condE = condE
        self.trueE = trueE
        self.falseE = falseE
    def __str__(self) -> str:
        return f"If0({self.condE}, {self.trueE}, {self.falseE})"
    
class Rec(Expression):
    def __init__(self, 
                 f_name: str,
                 p_name: str,
                 pty: Type,
                 rty: Type,
                 fbody: Expression,
                 expr: Expression):
        self.f_name = f_name
        self.p_name = p_name
        self.pty = pty
        self.fbody = fbody
        self.expr = expr
    def __str__(self) -> str:
        return f"Rec({self.f_name}, {self.p_name}, {self.pty}, 
                    {self.fbody}, {self.expr})"


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
    elif isinstance(expr, If0):
        mustSame(typeCheck(expr.condE, tyEnv), NumT)
        mustSame(
            typeCheck(expr.trueE, tyEnv),
            typeCheck(expr.falseE, tyEnv))
    elif isinstance(expr, Rec):
        ftype = ArrowT(expr.pty, expr.rty)
        new_TyEnv = dict(tyEnv, **{expr.f_name: ftype})
        mustSame(expr.rty, 
                 typeCheck(expr.fbody, dict(new_TyEnv, **{expr.p_name: expr.pty})))
        return typeCheck(expr.expr, new_TyEnv)
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
    elif isinstance(expr, If0):
        tval = interp(expr.condE, env)
        if isinstance(tval, NumV) and tval.n == 0:
            return interp(expr.trueE, env)
        else:
            return interp(expr.falseE, env)
    elif isinstance(expr, Rec):
        cloV = CloV(expr.f_name, expr.fbody, env)
        new_env = dict(env, **{expr.f_name: CloV})
        cloV.env = new_env
        interp(expr.expr, new_env)


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

