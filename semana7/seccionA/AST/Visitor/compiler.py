from AST.Visitor.visitor import Visitor
from AST.Builder.builder import Builder
from AST.nodes import *
from AST.errors import CompilerError


class Compiler(Visitor):
    _phase = "compile"

    def __init__(self, builder: Builder):
        super().__init__()
        self.builder = builder
        self.symbol_table = {}
        self.builder.emit_main_header()

    def get_code(self) -> str:
        self.builder.emit_main_footer()
        return self.builder.get_code()

    def visit_node(self, node):
        raise NotImplementedError(
            f"visit_node not implemented for {type(node).__name__}"
        )

    def visit_type(self, node: TypeNode):
        return node.value

    def visit_primitive(self, node: PrimitiveNode):
        return node.value

    def visit_variable(self, node: VariableNode):
        if node.name not in self.symbol_table:
            raise CompilerError(
                f"Undefined variable: {node.name}",
                node=node,
                phase=self._phase
            )
        var_info = self.symbol_table[node.name]
        base = var_info["base"]
        type_name = var_info["type"]
        temp = self.builder.new_temp()
        self.builder.build_memory_load(temp, base, type_name=type_name)
        return temp

    def visit_binary_op(self, node: BinaryOpNode):
        left = self.dispatch(node.left)
        right = self.dispatch(node.right)
        
        left_type = self._get_expr_type(node.left)
        
        temp = self.builder.new_temp()
        self.builder.build_arithmetic(node.op, temp, left, right, type_name=left_type)
        return temp

    def visit_declaration(self, node: DeclarationNode):
        type_name = self.dispatch(node.var_type)
        base = self.builder.emit_alloca(node.var_name, type_name)
        self.symbol_table[node.var_name] = {"base": base, "type": type_name}
        
        if node.expression:
            value = self.dispatch(node.expression)
            self.builder.build_memory_store(value, base, type_name=type_name)
        return None

    def visit_assignment(self, node: AssignmentNode):
        if node.var_name not in self.symbol_table:
            raise CompilerError(
                f"Undefined variable: {node.var_name}",
                node=node,
                phase=self._phase
            )
        value = self.dispatch(node.expression)
        var_info = self.symbol_table[node.var_name]
        self.builder.build_memory_store(value, var_info["base"], type_name=var_info["type"])
        return None

    def visit_block(self, node: BlockNode):
        for statement in node.statements:
            self.dispatch(statement)
        return None

    def visit_print(self, node: PrintNode):
        value = self.dispatch(node.expression)
        expr_type = self._get_expr_type(node.expression)
        self.builder.build_print(value, expr_type)
        return None

    def visit_if(self, node: IfNode):
        raise NotImplementedError("If statement not implemented in basic version")

    def visit_while(self, node: WhileNode):
        raise NotImplementedError("While statement not implemented in basic version")

    def visit_function_declaration(self, node: FunctionDeclarationNode):
        raise NotImplementedError("Function declaration not implemented in basic version")

    def visit_function_call(self, node: FunctionCallNode):
        raise NotImplementedError("Function call not implemented in basic version")

    def visit_param(self, node: ParamNode):
        raise NotImplementedError("Param not implemented in basic version")

    def visit_return(self, node: ReturnNode):
        raise NotImplementedError("Return not implemented in basic version")

    def visit_array(self, node: ArrayNode):
        raise NotImplementedError("Array not implemented in basic version")

    def _get_expr_type(self, node) -> str:
        if isinstance(node, PrimitiveNode):
            return node.type
        elif isinstance(node, VariableNode):
            if node.name in self.symbol_table:
                return self.symbol_table[node.name]["type"]
            return "int"
        elif isinstance(node, BinaryOpNode):
            return self._get_expr_type(node.left)
        return "int"