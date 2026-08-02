from AST.symtable import SymTable
from AST.nodes import *
from AST.Visitor.visitor import Visitor

class Interpreter(Visitor):
    def __init__(self):
        self.symbol_table: SymTable = SymTable()

    def visit_node(self, node):
        raise NotImplementedError(f"visit_node not implemented for {type(node).__name__}")

    def visit_type(self, node: TypeNode):
        return node.value

    def visit_primitive(self, node: PrimitiveNode):
        return node.value

    def visit_variable(self, node: VariableNode):
        value = self.symbol_table.get_symbol(node.name)
        if value is None:
            raise Exception(f'Undefined variable: {node.name}')
        return value

    def visit_binary_op(self, node: BinaryOpNode):
        left_value = node.left.visit(self)
        right_value = node.right.visit(self)        
        if node.op == '+':
            return left_value + right_value
        elif node.op == '-':
            return left_value - right_value
        elif node.op == '*':
            return left_value * right_value
        elif node.op == '/':
            return left_value / right_value
        else:
            raise Exception(f'Unknown binary operator: {node.op}')

    def visit_declaration(self, node: DeclarationNode):
        # No necesitamos verificar el tipo aquí, ya que el TypeChecker se encarga de eso.
        var_type = node.var_type.visit(self)
        if node.expression:
            expr_value = node.expression.visit(self)
            self.symbol_table.add_symbol(node.var_name, expr_value)
        else:
            self.symbol_table.add_symbol(node.var_name, None)
        return

    def visit_assignment(self, node: AssignmentNode):
        expr_value = node.expression.visit(self)
        self.symbol_table.update_symbol(node.var_name, expr_value)
        return

    def visit_block(self, node: BlockNode):
        prev_table = self.symbol_table
        self.symbol_table = SymTable(parent=prev_table)
        for statement in node.statements:
            statement.visit(self)
        self.symbol_table = prev_table
        return

    def visit_print(self, node: PrintNode):
        expr_value = node.expression.visit(self)
        print(expr_value)
        return

    def visit_if(self, node: IfNode):
        condition_value = node.condition.visit(self)
        if condition_value:
            node.block.visit(self)
        return

    def visit_while(self, node: WhileNode):
        while node.condition.visit(self):
            node.block.visit(self)
        return