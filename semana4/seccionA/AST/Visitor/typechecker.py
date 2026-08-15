from AST.symtable import SymTable
from AST.nodes import *
from AST.Visitor.visitor import Visitor
from AST.Structures.foreign import Foreign

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
        if expr_type not in ['int', 'float', 'string', 'bool', 'void']:
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

    def visit_function_declaration(self, node: FunctionDeclarationNode):              
        params_types = [param.visit(self) for param in node.parameters]
        func_type = node.return_type.visit(self)
        self.symbol_table.add_symbol(node.func_name, (params_types, func_type))
        for stmt in node.block.statements:
            stmt_type = stmt.visit(self)
            if isinstance(stmt, ReturnNode):
                if stmt_type != func_type:
                    self.errors.append(f'Return type mismatch in function {node.func_name}: expected {func_type}, got {stmt_type}')
        return 

    def visit_function_call(self, node: FunctionCallNode):
        func_info = self.symbol_table.get_symbol(node.func_name)
        if func_info is None:
            self.errors.append(f"Undefined function: {node.func_name}")
            return None
        params_types, return_type = func_info
        if len(params_types) != len(node.arguments):
            self.errors.append(f"Argument count mismatch in function call: expected {len(params_types)}, got {len(node.arguments)}")
            return return_type
        for i, arg in enumerate(node.arguments):
            arg_type = arg.visit(self)
            if arg_type != params_types[i]:
                self.errors.append(f"Argument type mismatch in function call: expected {params_types[i]}, got {arg_type}")
        return return_type

    def visit_param(self, node: ParamNode):
        return node.param_type.visit(self)

    def visit_return(self, node: ReturnNode):
        if node.expression:
            return_type = node.expression.visit(self)
            return return_type
        return 'void'