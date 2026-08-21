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


#### INSTRUCCIONES RELACIONADAS AL STRUCT
class Struct_dcl(Instruccion):
    def __init__(self, identificador, campos):
        self.identificador = identificador
        self.campos = campos


    def accept(self, visitor):
        return visitor.visit_struct_dcl(self)


class Struct_campo(Instruccion):
    def __init__(self, identificador, tipo):
        self.identificador = identificador
        self.tipo = tipo


    
    def accept(self, visitor):
        return visitor.visit_campo_struct(self)