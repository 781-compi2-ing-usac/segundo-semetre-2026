from abc import ABC, abstractmethod
class Visitor(ABC):
    @abstractmethod
    def visit_expresion_binaria(self, binaria):
        pass
    
    @abstractmethod
    def visit_expresion_valor(self, valor):
        pass
    @abstractmethod
    def visit_asignacion(self, asignacion):
        pass
    @abstractmethod
    def visit_condicional(self, condicional):
        pass
    @abstractmethod
    def visit_imprimir(self, valor):
        pass
    @abstractmethod
    def visit_funcion_dcl(self, funcion):
        pass
    @abstractmethod
    def visit_funcion_exec(self, funcion):
        pass
    @abstractmethod
    def visit_struct_dcl(self, struct):
        pass
    @abstractmethod
    def visit_campo_struct(self, struct):
        pass
    @abstractmethod
    def visit_init_struct(self, init_struct):
        pass
    @abstractmethod
    def visit_valor_struct(self, valor):
        pass
    @abstractmethod
    def visit_get_sub_value(self, valor):
        pass
    @abstractmethod
    def visit_bucle(self, valor):
        pass