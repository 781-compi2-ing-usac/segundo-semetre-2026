from abc import ABC, abstractmethod
from AST.nodes import *

class Visitor(ABC):
    @abstractmethod
    def visit_node(self, node):
        pass

    @abstractmethod
    def visit_type(self, node: TypeNode):
        pass

    @abstractmethod
    def visit_primitive(self, node: PrimitiveNode):
        pass

    @abstractmethod
    def visit_variable(self, node: VariableNode):
        pass

    @abstractmethod
    def visit_binary_op(self, node: BinaryOpNode):
        pass

    @abstractmethod
    def visit_declaration(self, node: DeclarationNode):
        pass

    @abstractmethod
    def visit_assignment(self, node: AssignmentNode):
        pass

    @abstractmethod
    def visit_block(self, node: BlockNode):
        pass

    @abstractmethod
    def visit_print(self, node: PrintNode):
        pass
    
    @abstractmethod
    def visit_if(self, node: IfNode):
        pass

    @abstractmethod
    def visit_while(self, node: WhileNode):
        pass

    # Iremos agregando más métodos de visita según sea necesario para otros tipos 
    # de nodos en el futuro.