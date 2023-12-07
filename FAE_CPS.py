from typing import Dict, Callable
from functools import partial
import logging

# create logger
logging.basicConfig()

logger = logging.getLogger("FAE_CPS")
logger.setLevel(logging.DEBUG)

"""
expr ::= n
    |   ( expr + expr)
    |   ( expr - expr)
    |   id
    |   expr ( expr )
    |   { id => expr}         
"""

# values types - root element
class Value():
    pass

# expression hierarchy
class Expression():
    pass

# type of environment
Env = Dict[str, Value]

# types of Expression
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
    def __init__(self, par_name: str, body: Expression):
        self.par_name = par_name
        self.body = body
    def __str__(self) -> str:
        return f"Fun({self.par_name}, {self.body})"

# Value types

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

# continuation value
Cont = Callable[[Value], Value]
IdentityCont = lambda x: x

# execution exception
class InterPreterException(Exception):
    pass

class FreeIdentifierError(InterPreterException):
    pass

class UnknownStatementException(InterPreterException):
    pass
 
class UnknownFunction(InterPreterException):
    pass
 
class NotNumExpression(Exception):
    pass

class ClosureError(Exception):
    pass

# type of num expressions
NumFunc = Callable[[int, int], int]

def interpCps(expr : Expression, env: Env, k:Cont) -> Value:
    if isinstance(expr, Num):
        return k(NumV(expr.n))
    elif isinstance(expr, Add):
        return interpCps(
            expr.left, 
            env, 
            lambda lv : interpCps(expr.right, 
                                env,
                                lambda rv : k(numAddV( lv,  rv ))))
        
        # return numAddV(interp(expr.left, env), interp(expr.right, env))
    elif isinstance(expr, Sub):
        return interpCps(
            expr.left, 
            env, 
            lambda lv : interpCps(expr.right, 
                                env,
                                lambda rv : k(numSubV( lv,  rv ))))
    elif isinstance(expr, Id):
        return k(lookup(expr.name, env))
    elif isinstance(expr, Fun):
        return k(CloV(expr.par_name, expr.body, env))
    elif isinstance(expr, App):
        return interpCps(
                    expr.f_expr, 
                    env,
                    lambda fv: 
                        interpCps(expr.val,
                               env,
                               lambda av:
                                    cps_call_fun(fv, av, k)
                               ))

def cps_call_fun(fv: Expression, av: Expression, k: Cont):
        if isinstance(fv, CloV):
            return interpCps(
                        fv.body, 
                        dict(fv.env, **{fv.param: av}),
                        k)
        else:
            raise ClosureError(f"not a closure {fv}")

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

if __name__ == "__main__":
    # test section
    assert interpCps(Num(10), {}, IdentityCont).n  == 10
    assert interpCps(Add(Num(10), Num(20)), {}, IdentityCont).n == 30
    assert interpCps(Sub(Num(10), Num(20)), {}, IdentityCont).n == -10
    assert interpCps(Add(Num(0), Num(3)), {}, IdentityCont).n == 3

    assert interpCps(App(Fun("x", Add(Id("x"), Num(10))), Num(5)), {}, IdentityCont).n == 15 
