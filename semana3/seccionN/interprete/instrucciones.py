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