from typing import Dict, Callable
from functools import partial
import logging

# create logger
logging.basicConfig()

logger = logging.getLogger("KVAE")
logger.setLevel(logging.DEBUG)


# expression hierarchy
class Expression():
    pass

# expression types
Cont = Callable[[Expression], Expression]

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

class Vcc(Expression):
    def __init__(self, cont_name, body) -> None:
        self.cont_name = cont_name
        self.body = body
    def __str__(self) -> str:
        return f"Vcc({self.par_name}, {self.body})"

# Value
class Value():
    pass

# type of environment
Env = Dict[str, Value]

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

class ContV(Value):
    def __init__(self, proc: Cont) -> None:
        self.proc = proc


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

# initial continuation
IdentityCont = lambda x: x

def interp(expr : Expression, env: Env, k: Cont) -> Value:
    logger.debug(f"calling interp with {expr=!s} {env=!s} {k=!s}")
    if isinstance(expr, Num):
        return k(NumV(expr.n))
    elif isinstance(expr, Add):
        return interp(
            expr.left, 
            env, 
            lambda lv : interp(expr.right, 
                                env,
                                lambda rv : k(numAddV( lv,  rv ))))        
    elif isinstance(expr, Sub):
        return interp(
            expr.left, 
            env, 
            lambda lv : interp(expr.right, 
                                env,
                                lambda rv : k(numSubV( lv,  rv ))))
    elif isinstance(expr, Id):
        return k(lookup(expr.name, env))
    elif isinstance(expr, Fun):
        return k(CloV(expr.par_name, expr.body, env))
    elif isinstance(expr, App):
        return interp(
                    expr.f_expr, 
                    env,
                    lambda fv: 
                        interp(expr.val,
                               env,
                               lambda av:
                                    cps_call_fun(fv, av, k)
                               ))
    elif isinstance(expr, Vcc):
        return interp(expr.body, dict(env, **{expr.cont_name: ContV(k)}), k)
    else:
        raise UnknownStatementException(f"instruction {expr=!s}")

# lambda expressions don't allow statement inside, only expressions
# so I have to call an external function (calling is considered an expression)
# to implemente the check type case against CloV value

def cps_call_fun(fv: Expression, av: Expression, k: Cont):
        if isinstance(fv, CloV):
            return interp(
                        fv.body, 
                        dict(fv.env, **{fv.param: av}),
                        k)
        elif isinstance(fv, ContV):
            return fv.proc(av)
        else:
            raise ClosureError(f"not a closure {fv}")


def lookup(var_name:str, env: Env):
    logger.debug(f"lookup called with {var_name=!s} {env=!s}")
    try:
        return env[var_name]
    except KeyError:
        raise FreeIdentifierError(f"free identifier {var_name}")
    
def numOp(op: NumFunc, lexpr: Value, rexpr: Value)-> Value:
    logger.debug(f"numOp called with {op=!s} {lexpr=!s} {rexpr=!s}")
    logger.debug(f"{type(lexpr)=}, {type(rexpr)}")
    if isinstance(lexpr, NumV) and isinstance (rexpr, NumV):
        return NumV(op(lexpr.n, rexpr.n))
    else:
        raise NotNumExpression(f"not both numbers: {lexpr} {rexpr}")

numAddV = partial(numOp, lambda x,y: x + y)
numSubV = partial(numOp, lambda x,y: x - y)

if __name__ == "__main__": 
    assert interp(Num(10), {}, IdentityCont ).n == 10
    assert interp(Add(Num(10), Num(20)), {}, IdentityCont).n == 30
    assert interp(Sub(Num(10), Num(20)), {}, IdentityCont).n == -10
    assert interp(Add(Num(0), Num(3)), {}, IdentityCont).n == 3

    assert interp(App(Fun("x", Add(Id("x"),Id("x"))), Num(10)), {}, IdentityCont).n == 20
    assert interp(Add(
        App(Fun("x", Add(Id("x"),Id("x"))), Num(10)),
        Num(3)),
        {}, IdentityCont).n == 23
