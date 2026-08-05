from abc import ABC, abstractmethod
class Visitor(ABC):
    @abstractmethod
    def visit_expresion_binaria(self, binaria):
        pass
    
    @abstractmethod
    def visit_expresion_valor(self, valor):
        pass
