from AST.symtable import SymTable
from AST.nodes import *
from AST.Visitor.visitor import Visitor
from AST.Structures.foreign import Foreign
from AST.Structures.array import ArrayAccessError, ArrayValue
from AST.flow import *
from AST.errors import RuntimeError_


class Interpreter(Visitor):
    _phase = "runtime"

    def __init__(self):
        super().__init__()
        self.symbol_table: SymTable = SymTable()

    def visit_node(self, node):
        raise NotImplementedError(
            f"visit_node not implemented for {type(node).__name__}"
        )

    def visit_type(self, node: TypeNode):
        return node.value

    def visit_primitive(self, node: PrimitiveNode):
        return node.value

    def visit_variable(self, node: VariableNode):
        value = self.symbol_table.get_symbol(node.name)
        if not node.access:
            return value

        if not isinstance(value, ArrayValue):
            raise RuntimeError_(f"Variable '{node.name}' is not an array", node=node)

        indexes = [self.dispatch(access) for access in node.access]
        try:
            return value.get(indexes)
        except ArrayAccessError as e:
            raise RuntimeError_(str(e), node=node)

    def visit_arith_op(self, node: ArithOpNode):
        left_value = self.dispatch(node.left)
        right_value = self.dispatch(node.right)
        if node.op == "+":
            return left_value + right_value
        elif node.op == "-":
            return left_value - right_value
        elif node.op == "*":
            return left_value * right_value
        elif node.op == "/":
            return left_value / right_value
        else:
            raise RuntimeError_(f"Unknown arithmetic operator: {node.op}", node=node)

    def visit_rel_op(self, node: RelOpNode):
        left_value = self.dispatch(node.left)
        right_value = self.dispatch(node.right)
        if node.op == "<":
            return left_value < right_value
        elif node.op == ">":
            return left_value > right_value
        elif node.op == "<=":
            return left_value <= right_value
        elif node.op == ">=":
            return left_value >= right_value
        elif node.op == "==":
            return left_value == right_value
        else:
            raise RuntimeError_(f"Unknown relational operator: {node.op}", node=node)

    def visit_logic_op(self, node: LogicOpNode):
        left_value = self.dispatch(node.left)
        right_value = self.dispatch(node.right)
        if node.op == "&":
            return left_value and right_value
        elif node.op == "|":
            return left_value or right_value
        else:
            raise RuntimeError_(f"Unknown logic operator: {node.op}", node=node)

    def visit_declaration(self, node: DeclarationNode):
        if node.expression:
            expr_value = self.dispatch(node.expression)
            self.symbol_table.add_symbol(node.var_name, expr_value)
        else:
            self.symbol_table.add_symbol(node.var_name, None)
        return

    def visit_assignment(self, node: AssignmentNode):
        expr_value = self.dispatch(node.expression)
        if not node.access:
            self.symbol_table.update_symbol(node.var_name, expr_value)
            return

        array_value = self.symbol_table.get_symbol(node.var_name)
        if not isinstance(array_value, ArrayValue):
            raise RuntimeError_(
                f"Variable '{node.var_name}' is not an array", node=node
            )

        indexes = [self.dispatch(access) for access in node.access]
        try:
            array_value.set(indexes, expr_value)
        except ArrayAccessError as e:
            raise RuntimeError_(str(e), node=node)
        return

    def visit_block(self, node: BlockNode):
        prev_table = self.symbol_table
        self.symbol_table = SymTable(parent=prev_table)
        for statement in node.statements:
            result = self.dispatch(statement)
            if isinstance(result, FlowControl):
                self.symbol_table = prev_table
                return result
        self.symbol_table = prev_table
        return

    def visit_print(self, node: PrintNode):
        expr_value = self.dispatch(node.expression)
        print(expr_value)
        return

    def visit_if(self, node: IfNode):
        condition_value = self.dispatch(node.condition)
        if condition_value:
            result = self.dispatch(node.block)
            if isinstance(result, FlowControl):
                return result
        return None

    def visit_while(self, node: WhileNode):
        while self.dispatch(node.condition):
            result = self.dispatch(node.block)
            if isinstance(result, FlowControl):
                return result
        return None

    def visit_function_declaration(self, node: FunctionDeclarationNode):
        params = [self.dispatch(param) for param in node.parameters]
        function = Foreign(node, self.symbol_table, params)
        self.symbol_table.add_symbol(node.func_name, function)
        return

    def visit_function_call(self, node: FunctionCallNode):
        function = self.symbol_table.get_symbol(node.func_name)
        if function is None:
            raise RuntimeError_(f"Undefined function: {node.func_name}", node=node)
        if not isinstance(function, Foreign):
            raise RuntimeError_(f"{node.func_name} is not a function", node=node)
        return function.invoke(self, node.arguments)

    def visit_param(self, node: ParamNode):
        return node.param_name

    def visit_return(self, node: ReturnNode):
        if node.expression:
            value = self.dispatch(node.expression)
            return Return(value)
        return Return(None)

    def visit_array(self, node: ArrayNode):
        return ArrayValue([self.dispatch(element) for element in node.array])
