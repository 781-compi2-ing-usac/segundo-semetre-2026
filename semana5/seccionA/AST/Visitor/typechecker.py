from AST.symtable import SymTable
from AST.nodes import *
from AST.Visitor.visitor import Visitor
from AST.Structures.array import ArrayType


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
            return None

        accessed_type = var_type
        for access in node.access:
            index_type = access.visit(self)
            if index_type != 'int':
                self.errors.append(
                    f"Array index for '{node.name}' must be int, got {index_type}"
                )
                return None
            if not isinstance(accessed_type, ArrayType):
                self.errors.append(
                    f"Variable '{node.name}' does not have another array dimension"
                )
                return None
            accessed_type = accessed_type.accessed_type(1)

        return accessed_type

    def visit_binary_op(self, node: BinaryOpNode):
        left_type = node.left.visit(self)
        right_type = node.right.visit(self)

        arithmetic_ops = ['+', '-', '*', '/']
        comparison_ops = ['<', '>', '<=', '>=', '==']

        if node.op in arithmetic_ops:
            if left_type != right_type:
                self.errors.append(
                    f'Type mismatch in binary operation: {left_type} and {right_type}'
                )
            if left_type not in ['int', 'float']:
                self.errors.append(
                    f'Invalid type for arithmetic operation: {left_type}'
                )
            return left_type
        if node.op in comparison_ops:
            if left_type != right_type:
                self.errors.append(
                    f'Type mismatch in comparison operation: {left_type} and {right_type}'
                )
            if left_type not in ['int', 'float']:
                self.errors.append(
                    f'Invalid type for comparison operation: {left_type}'
                )
            return 'bool'

        return left_type

    def visit_declaration(self, node: DeclarationNode):
        var_type = node.var_type.visit(self)
        if node.expression:
            expr_type = node.expression.visit(self)
            if isinstance(expr_type, ArrayType):
                if expr_type.element_type != var_type:
                    self.errors.append(
                        f"Type mismatch in declaration: {var_type} and {expr_type}"
                    )
                var_type = expr_type
            elif var_type != expr_type:
                self.errors.append(
                    f"Type mismatch in declaration: {var_type} and {expr_type}"
                )
        self.symbol_table.add_symbol(node.var_name, var_type)
        return var_type

    def visit_assignment(self, node: AssignmentNode):
        declared_type = self.symbol_table.get_symbol(node.var_name)
        if declared_type is None:
            self.errors.append(f"Undefined variable: {node.var_name}")

        target_type = declared_type
        if declared_type is not None:
            for access in node.access:
                index_type = access.visit(self)
                if index_type != 'int':
                    self.errors.append(
                        f"Array index for '{node.var_name}' must be int, got {index_type}"
                    )
                    target_type = None
                    break
                if not isinstance(target_type, ArrayType):
                    self.errors.append(
                        f"Variable '{node.var_name}' does not have another array dimension"
                    )
                    target_type = None
                    break
                target_type = target_type.accessed_type(1)

        expr_type = node.expression.visit(self)
        if isinstance(target_type, ArrayType):
            compatible = target_type.is_compatible_with(expr_type)
        else:
            compatible = target_type == expr_type
        if declared_type is not None and not compatible:
            self.errors.append(
                f'Type mismatch in assignment: {target_type} and {expr_type}'
            )
        return target_type

    def visit_block(self, node: BlockNode):
        prev_table = self.symbol_table
        self.symbol_table = SymTable(parent=prev_table)
        for statement in node.statements:
            statement.visit(self)
        self.symbol_table = prev_table

    def visit_print(self, node: PrintNode):
        expr_type = node.expression.visit(self)
        if (
            expr_type is not None
            and expr_type not in ['int', 'float', 'string', 'bool', 'void']
            and not isinstance(expr_type, ArrayType)
        ):
            self.errors.append(f'Invalid type for print statement: {expr_type}')
        return expr_type

    def visit_if(self, node: IfNode):
        condition_type = node.condition.visit(self)
        if condition_type != 'bool':
            self.errors.append(
                f'Condition in if statement must be of type bool, got {condition_type}'
            )
        node.block.visit(self)

    def visit_while(self, node: WhileNode):
        condition_type = node.condition.visit(self)
        if condition_type != 'bool':
            self.errors.append(
                f'Condition in while statement must be of type bool, got {condition_type}'
            )
        node.block.visit(self)

    def visit_function_declaration(self, node: FunctionDeclarationNode):
        params_types = [param.visit(self) for param in node.parameters]
        func_type = node.return_type.visit(self)
        self.symbol_table.add_symbol(node.func_name, (params_types, func_type))
        for statement in node.block.statements:
            statement_type = statement.visit(self)
            if isinstance(statement, ReturnNode) and statement_type != func_type:
                self.errors.append(
                    f'Return type mismatch in function {node.func_name}: '
                    f'expected {func_type}, got {statement_type}'
                )

    def visit_function_call(self, node: FunctionCallNode):
        func_info = self.symbol_table.get_symbol(node.func_name)
        if func_info is None:
            self.errors.append(f"Undefined function: {node.func_name}")
            return None

        params_types, return_type = func_info
        if len(params_types) != len(node.arguments):
            self.errors.append(
                f"Argument count mismatch in function call: expected "
                f"{len(params_types)}, got {len(node.arguments)}"
            )
            return return_type

        for i, arg in enumerate(node.arguments):
            arg_type = arg.visit(self)
            expected_type = params_types[i]
            if isinstance(expected_type, ArrayType):
                compatible = expected_type.is_compatible_with(arg_type)
            else:
                compatible = arg_type == expected_type
            if not compatible:
                self.errors.append(
                    f"Argument type mismatch in function call: expected "
                    f"{expected_type}, got {arg_type}"
                )
        return return_type

    def visit_param(self, node: ParamNode):
        base_type = node.param_type.visit(self)
        if node.array_dimensions:
            param_type = ArrayType(
                base_type,
                (None,) * len(node.array_dimensions)
            )
        else:
            param_type = base_type
        self.symbol_table.add_symbol(node.param_name, param_type)
        return param_type

    def visit_return(self, node: ReturnNode):
        if node.expression:
            return node.expression.visit(self)
        return 'void'

    def visit_array(self, node: ArrayNode):
        element_types = [element.visit(self) for element in node.array]
        if not element_types:
            self.errors.append('Array cannot be empty')
            return None

        first_type = element_types[0]
        if isinstance(first_type, ArrayType):
            if any(
                not isinstance(element_type, ArrayType)
                or element_type.element_type != first_type.element_type
                for element_type in element_types[1:]
            ):
                self.errors.append(
                    f'Array elements must have the same type, got {element_types}'
                )
            if any(
                not isinstance(element_type, ArrayType)
                or element_type.shape != first_type.shape
                for element_type in element_types[1:]
            ):
                self.errors.append('Matrix rows must have the same type and length')
            return ArrayType(
                first_type.element_type,
                (len(node.array),) + first_type.shape
            )

        if any(element_type != first_type for element_type in element_types[1:]):
            self.errors.append(
                f'Array elements must have the same type, got {element_types}'
            )
        return ArrayType(first_type, (len(node.array),))
