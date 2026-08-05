from abc import ABC, abstractmethod
class Expresion(ABC):
    @abstractmethod
    def accept(self, visitor):
        pass

class ExpresionValor(Expresion):
    def __init__(self, val, tipo='INT'):
        self.val = val
        self.tipo = tipo

    def accept(self, visitor):
        return visitor.visit_expresion_valor(self)

class ExpresionBinaria(Expresion):
    def __init__(self, exp1, exp2, operador):
        self.exp1 = exp1
        self.exp2 = exp2
        self.operador = operador
    
    def accept(self, visitor):
        return visitor.visit_expresion_binaria(self)