from typing import Dict, Callable, List
from functools import partial
import logging
from collections import deque

# FAE - low level representation - Bruijin indexes

# create logger
logging.basicConfig()

logger = logging.getLogger("FAE-BRUIJIN")
logger.setLevel(logging.DEBUG)

# roots for different types

# expression
class Expression():
    pass

# low level expression
class MExpr():
    pass

# Value
class Value():
    pass

# continuation
class Cont():
    pass

# type of environment
Env = deque[Value]

# translation environment
TEnv = deque[str]

# type of num expressions
NumFunc = Callable[[int, int], int]

# expression (high level language)
# types of expression
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

# new types of expression (numerical types)
class MNum(MExpr):
    def __init__(self, n):
        self.n = n
    def __str__(self) -> str:
        return f"MNum({self.n})"

class MAdd(MExpr):
    def __init__(self, left: MExpr, right: MExpr):
        self.left = left
        self.right = right
    def __str__(self) -> str:
        return f"MAdd({self.left}, {self.right})"
    
class MSub(MExpr):
    def __init__(self, left: MExpr, right: MExpr):
        self.left = left
        self.right = right
    def __str__(self) -> str:
        return f"MSub({self.left}, {self.right})"
    
class MId(MExpr):
    def __init__(self, pos: int):
        self.pos = pos
    def __str__(self) -> str:
        return f"MId({self.pos})"
        
class MApp(MExpr):
    def __init__(self, f_expr: MExpr, val: MExpr):
        self.f_expr = f_expr
        self.val = val
    def __str__(self) -> str:
        return f"MApp({self.f_expr}, {self.val} )"

class MFun(MExpr):
    def __init__(self,body: MExpr):
        self.body = body
    def __str__(self) -> str:
        return f"MFun({self.body})"

# types of values
class NumV(Value):
    def __init__(self, n: int):
        self.n = n
    def __str__(self) -> str:
        return f"NumV({self.n})"

class CloV(Value):
    def __init__(self, body: MExpr, env: Env):
        self.body = body
        self.env = env
    def __str__(self) -> str:
        return f"CloV({self.body}, {self.env})"

class ContV(Value):
    def __init__(self, proc: Cont) -> None:
         self.proc = proc
    def __str__(self):
        return f"ContV({self.proc=!s})"
    
# types of continuation
class AddSecondK(Cont):
    def __init__(self, e2: Expression, env: Env, k: Cont):
        self.e2 = e2
        self.env = env
        self.k = k
    def __str__(self):
        return f"AddSecondK({self.e2!s}, {self.env!s}, {self.k!s})"

class DoAddK(Cont):
    def __init__(self, v1: Value, k: Cont):
        self.v1 = v1
        self.k = k
    def __str__(self):
        return f"DoAddK({self.v1!s}, {self.k!s})"

class SubSecondK(Cont):
    def __init__(self, e2: Expression, env: Env, k: Cont):
        self.e2 = e2
        self.env = env
        self.k = k
    def __str__(self):
        return f"SubSecondK({self.e2!s}, {self.env!s}, {self.k!s})"

class DoSubK(Cont):
    def __init__(self, v1: Value, k: Cont):
        self.v1 = v1
        self.k = k
    def __str__(self):
       return f"DoSubK({self.v1!s}, {self.k!s})"

class AppArgK(Cont):
    def __init__(self, e2: Expression, env: Env, k: Cont):
        self.e2 = e2
        self.env = env
        self.k = k
    def __str__(self):
        return f"AppArgK({self.e2!s}, {self.env!s}, {self.k!s})"

class DoAppK(Cont):
    def __init__(self, v1: Value, k: Cont):
        self.v1 = v1
        self.k = k
    def __str__(self):
        return f"DoAppK({self.v1!s}, {self.k!s})"

class MtK(Cont):
    def __str__(self):
        return f"MtK()"


InitialContinuation = MtK()

# execution exception
class InterPreterException(Exception):
    pass

class FreeIdentifierError(InterPreterException):
    pass

class UnknownStatementException(InterPreterException):
    pass
 
class UnknownFunction(InterPreterException):
    pass
 
class NotNumExpression(InterPreterException):
    pass

class ClosureError(InterPreterException):
    pass

class UnknownContinuation(InterPreterException):
    pass

class UnknownIdentifier(InterPreterException):
    pass

# type of num expressions
NumFunc = Callable[[int, int], int]

def locate(name:str, tenv: TEnv)->int:
    try:
        return tenv.index(name)
    except ValueError:
        raise UnknownIdentifier(f"Identifier {name} not found in {tenv!s}")
    
def translate(expr: Expression, tenv: TEnv)-> MExpr:
    if isinstance(expr, Id):
        return MId(locate(expr.name, tenv))
    elif isinstance(expr, Num):
        return MNum(expr.n)
    elif isinstance(expr, Fun):
        return MFun(translate(expr.body, deque([expr.par_name]) + tenv))
    elif isinstance(expr, Add):
        return MAdd(translate(expr.left, tenv), translate(expr.right, tenv))
    elif isinstance(expr, Sub):
        return MSub(translate(expr.left, tenv), translate(expr.right, tenv))
    elif isinstance(expr, App):
        return MApp(translate(expr.f_expr, tenv), translate(expr.val, tenv))
    else:
        raise UnknownStatementException(f"unknow how to translate {expr}")
    
def continue_cps(k: Cont, v: Value)->Value:
    logger.debug(f"calling continue_cps with {k=!s} {v=!s}")
    if isinstance(k, AddSecondK):
        return interp(k.e2, k.env, DoAddK(v, k.k))
    elif isinstance(k, DoAddK):
        return continue_cps(k.k, MNum(k.v1.n + v.n))
    if isinstance(k, SubSecondK):
        return interp(k.e2, k.env, DoSubK(v, k.k))
    elif isinstance(k, DoSubK):
        return continue_cps(k.k, MNum(k.v1.n - v.n))
    elif isinstance(k, AppArgK):
        return interp(k.e2, k.env, DoAppK(v, k.k))
    elif isinstance(k, DoAppK):
        logger.debug(f"called DoAppk with {k.v1=!s} {k.k=!s}")
        if isinstance(k.v1, CloV):
            logger.debug("CloV detected")
            return interp(k.v1.body, deque([v]) + k.v1.env, k.k)
        elif isinstance(k.v1, ContV):
            logger.debug("ContV detected")
            return continue_cps(k.v1.proc, v)
        else:
            raise UnknownContinuation(f"DoAppK - unknown type {v} ")
    elif isinstance(k, MtK):
        return v
    else:
        raise UnknownContinuation(f"continue_cps: continuation {k} not known")

def interp(expr : MExpr, env: Env, k: Cont) -> Value:
    logger.debug(f"calling interp with {expr=!s} {env=!s} {k=!s}")
    
    if isinstance(expr, MNum):
        return continue_cps(k, expr)
    elif isinstance(expr, MAdd):
        return interp(expr.left, env, AddSecondK(expr.right, env, k))
    elif isinstance(expr, MSub):
        return interp(expr.left, env, SubSecondK(expr.right, env, k))
    elif isinstance(expr, MId):
        return continue_cps(k, env[expr.pos])
    elif isinstance(expr, MFun):
        return continue_cps(k, CloV(expr.body, env))
    elif isinstance(expr, MApp):
        return interp(expr.f_expr, env, AppArgK(expr.val, env, k))
    else:
        raise UnknownStatementException(f"instruction {expr=!s}")
    
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
    assert interp(translate(Num(10), deque()), deque(), InitialContinuation ).n == 10
    assert interp(translate(Add(Num(10), Num(20)), deque()), deque, InitialContinuation).n == 30
    assert interp(translate(Sub(Num(10), Num(20)), deque()), deque(), InitialContinuation).n == -10
    assert interp(translate(Add(Num(0), Num(3)), deque()), deque(), InitialContinuation).n == 3

    assert interp(translate(App(Fun("x", Add(Id("x"),Id("x"))), Num(10)), deque()), deque(), InitialContinuation).n == 20
    assert interp(translate(Add(
        App(Fun("x", Add(Id("x"),Id("x"))), Num(10)),
        Num(3)), deque()),
        deque(), InitialContinuation).n == 23
