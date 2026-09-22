from abc import ABC, abstractmethod
from AST.nodes import *
from AST.errors import CompilerError


class Visitor(ABC):
    def __init__(self):
        self.errors = []
        self._visit_stack = []

    def dispatch(self, node):
        self._visit_stack.append(node)
        try:
            return node.visit(self)
        except CompilerError as e:
            if not e.trace:
                e.trace = list(self._visit_stack[:-1])
            self.errors.append(e)
            return None
        except Exception as e:
            err = CompilerError(
                str(e), node=node, phase=getattr(self, "_phase", "unknown")
            )
            err.trace = list(self._visit_stack[:-1])
            self.errors.append(err)
            return None
        finally:
            self._visit_stack.pop()

    def error(self, message, node=None):
        err = CompilerError(
            message, node=node, phase=getattr(self, "_phase", "unknown")
        )
        err.trace = list(self._visit_stack)
        self.errors.append(err)
        return None

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
    def visit_arith_op(self, node: ArithOpNode):
        pass

    @abstractmethod
    def visit_rel_op(self, node: RelOpNode):
        pass

    @abstractmethod
    def visit_logic_op(self, node: LogicOpNode):
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

    @abstractmethod
    def visit_function_declaration(self, node: FunctionDeclarationNode):
        pass

    @abstractmethod
    def visit_function_call(self, node: FunctionCallNode):
        pass

    @abstractmethod
    def visit_param(self, node: ParamNode):
        pass

    @abstractmethod
    def visit_return(self, node: ReturnNode):
        pass

    @abstractmethod
    def visit_array(self, node: ArrayNode):
        pass
