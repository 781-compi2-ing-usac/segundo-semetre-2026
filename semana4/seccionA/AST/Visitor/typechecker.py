from AST.symtable import SymTable
from AST.nodes import *
from AST.Visitor.visitor import Visitor

class TypeChecker(Visitor):
    def __init__(self):
        self.symbol_table: SymTable = SymTable()
        self.errors = []

    def visit_node(self, node):
        raise NotImplementedError(f"visit_node not implemented for {type(node).__name__}")

    def visit_type(self, node: TypeNode):        
        return node.value

    def visit_primitive(self, node: PrimitiveNode):            
        return node.type

    def visit_variable(self, node: VariableNode):        
        var_type = self.symbol_table.get_symbol(node.name)        
        if var_type is None:
            self.errors.append(f"Undefined variable: {node.name}")
        return var_type

    def visit_binary_op(self, node: BinaryOpNode):                
        print(node.left)
        left_type = node.left.visit(self)
        right_type = node.right.visit(self)

        arthmetic_ops = ['+', '-', '*', '/']
        comparison_ops = ['<', '>', '<=', '>=', '==']

        if node.op in arthmetic_ops:
            if left_type != right_type:
                self.errors.append(f'Type mismatch in binary operation: {left_type} and {right_type}')
            if left_type not in ['int', 'float']:
                self.errors.append(f'Invalid type for arithmetic operation: {left_type}')
            return left_type
        elif node.op in comparison_ops:
            if left_type != right_type:
                self.errors.append(f'Type mismatch in comparison operation: {left_type} and {right_type}')
            if left_type not in ['int', 'float']:
                self.errors.append(f'Invalid type for comparison operation: {left_type}')
            return 'bool'
            
        return left_type

    def visit_declaration(self, node: DeclarationNode):
        var_type = node.var_type.visit(self)
        if node.expression:                        
            expr_type = node.expression.visit(self)
            if var_type != expr_type:
                self.errors.append(f'Type mismatch in declaration: {var_type} and {expr_type}')
        self.symbol_table.add_symbol(node.var_name, var_type)
        return var_type

    def visit_assignment(self, node: AssignmentNode):
        var_type = self.symbol_table.get_symbol(node.var_name)
        if var_type is None:
            self.errors.append(f"Undefined variable: {node.var_name}")
        expr_type = node.expression.visit(self)
        if var_type != expr_type:
            self.errors.append(f'Type mismatch in assignment: {var_type} and {expr_type}')
        self.symbol_table.update_symbol(node.var_name, expr_type)
        return var_type

    def visit_block(self, node: BlockNode):
        prev_table = self.symbol_table
        self.symbol_table = SymTable(parent=prev_table)
        for statement in node.statements:
            statement.visit(self)
        self.symbol_table = prev_table
        return        

    def visit_print(self, node: PrintNode):
        expr_type = node.expression.visit(self)
        if expr_type not in ['int', 'float', 'string', 'bool']:
            self.errors.append(f'Invalid type for print statement: {expr_type}')
        return expr_type 

    def visit_if(self, node: IfNode):
        condition_type = node.condition.visit(self)
        if condition_type != 'bool':
            self.errors.append(f'Condition in if statement must be of type bool, got {condition_type}')
        node.block.visit(self)
        return

    def visit_while(self, node: WhileNode):
        condition_type = node.condition.visit(self)
        if condition_type != 'bool':
            self.errors.append(f'Condition in while statement must be of type bool, got {condition_type}')
        node.block.visit(self)
        return