from AST.symtable import SymTable
from AST.nodes import *

class TypeChecker:
    def __init__(self):
        self.symbol_table: SymTable = SymTable()

    def visit_node(self, node):
        raise NotImplementedError(f"visit_node not implemented for {type(node).__name__}")

    def visit_type(self, node: TypeNode):
        return node.value

    def visit_primitive(self, node: PrimitiveNode):
        return node.type

    def visit_variable(self, node: VariableNode):
        var_type = self.symbol_table.get_symbol(node.name)
        if var_type is None:
            raise Exception(f'Undefined variable: {node.name}')
        return var_type

    def visit_binary_op(self, node: BinaryOpNode):
        left_type = node.left.visit(self)
        right_type = node.right.visit(self)

        if left_type != right_type:
            raise Exception(f'Type mismatch: {left_type} and {right_type}')

        return left_type

    def visit_assignment(self, node: AssignmentNode):
        var_type = node.var_type.visit(self)
        self.symbol_table.add_symbol(node.var_name, var_type)
        return var_type

    def visit_block(self, node: BlockNode):
        types = []
        for statement in node.statements:
            types.append(statement.visit(self))
        return types