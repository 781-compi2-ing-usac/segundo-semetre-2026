from abc import ABC, abstractmethod
class Instruccion(ABC):
    @abstractmethod
    def accept(self, visitor):
        pass

class Asignacion(Instruccion):
    def __init__(self, identificador, exp, tipo):
        self.identificador = identificador
        self.exp = exp
        self.tipo = tipo

    def accept(self, visitor):
        return visitor.visit_asignacion(self)

class Condicional(Instruccion):
    def __init__(self, exp, instrucciones):
        self.exp = exp
        self.instrucciones = instrucciones

    def accept(self, visitor):
        return visitor.visit_condicional(self)

class Imprimir(Instruccion):
    def __init__(self, exp):
        self.exp = exp

    def accept(self, visitor):
        return visitor.visit_imprimir(self)

class Funcion_paramless(Instruccion):
    def __init__(self, identificador, instrucciones):
        self.identificador = identificador
        self.instrucciones = instrucciones

    def accept(self, visitor):
        return visitor.visit_funcion_dcl(self)