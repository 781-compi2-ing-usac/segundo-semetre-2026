class Node:
    def __init__(self, value, lineno=None):
        self.value = value
        self.lineno = lineno

    def __repr__(self):
        return f"Node({self.value})"

    def visit(self, visitor):
        return visitor.visit_node(self)


class TypeNode(Node):
    def __init__(self, value, lineno=None):
        super().__init__(value, lineno)

    def __repr__(self):
        return f"TypeNode({self.value})"

    def visit(self, visitor):
        return visitor.visit_type(self)


class PrimitiveNode(Node):
    def __init__(self, value, p_type, lineno=None):
        super().__init__(value, lineno)
        self.type = p_type

    def __repr__(self):
        return f"PrimitiveNode({self.value}, {self.type})"

    def visit(self, visitor):
        return visitor.visit_primitive(self)


class VariableNode(Node):
    def __init__(self, name, access, lineno=None):
        super().__init__("VARIABLE", lineno)
        self.name = name
        self.access = access

    def __repr__(self):
        return f"VariableNode({self.name})"

    def visit(self, visitor):
        return visitor.visit_variable(self)


class BinaryOpNode(Node):
    def __init__(self, left, op, right, lineno=None):
        super().__init__(op, lineno)
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinaryOpNode({self.left}, {self.value}, {self.right})"

    def visit(self, visitor):
        return visitor.visit_binary_op(self)


class DeclarationNode(Node):
    def __init__(self, var_type, var_name, expression=None, lineno=None):
        super().__init__("DECLARATION", lineno)
        self.var_type = var_type
        self.var_name = var_name
        self.expression = expression

    def __repr__(self):
        return f"DeclarationNode({self.var_type}, {self.var_name}, {self.expression})"

    def visit(self, visitor):
        return visitor.visit_declaration(self)


class AssignmentNode(Node):
    def __init__(self, var_name, access, expression, lineno=None):
        super().__init__("ASSIGNMENT", lineno)
        self.var_name = var_name
        self.access = access
        self.expression = expression

    def __repr__(self):
        return f"AssignmentNode({self.var_name}, {self.expression})"

    def visit(self, visitor):
        return visitor.visit_assignment(self)


class BlockNode(Node):
    def __init__(self, statements, lineno=None):
        super().__init__("BLOCK", lineno)
        self.statements = statements

    def __repr__(self):
        return f"BlockNode({self.statements})"

    def visit(self, visitor):
        return visitor.visit_block(self)


class PrintNode(Node):
    def __init__(self, expression, lineno=None):
        super().__init__("PRINT", lineno)
        self.expression = expression

    def __repr__(self):
        return f"PrintNode({self.expression})"

    def visit(self, visitor):
        return visitor.visit_print(self)


class IfNode(Node):
    def __init__(self, condition, block, lineno=None):
        super().__init__("IF", lineno)
        self.condition = condition
        self.block = block

    def __repr__(self):
        return f"IfNode({self.condition}, {self.block})"

    def visit(self, visitor):
        return visitor.visit_if(self)


class WhileNode(Node):
    def __init__(self, condition, block, lineno=None):
        super().__init__("WHILE", lineno)
        self.condition = condition
        self.block = block

    def __repr__(self):
        return f"WhileNode({self.condition}, {self.block})"

    def visit(self, visitor):
        return visitor.visit_while(self)


class FunctionDeclarationNode(Node):
    def __init__(self, func_name, parameters, return_type, block, lineno=None):
        super().__init__("FUNCTION_DECLARATION", lineno)
        self.func_name = func_name
        self.parameters = parameters
        self.return_type = return_type
        self.block = block

    def __repr__(self):
        return f"FunctionDeclarationNode({self.func_name}, {self.parameters}, {self.return_type}, {self.block})"

    def visit(self, visitor):
        return visitor.visit_function_declaration(self)


class FunctionCallNode(Node):
    def __init__(self, func_name, arguments, lineno=None):
        super().__init__("FUNCTION_CALL", lineno)
        self.func_name = func_name
        self.arguments = arguments

    def __repr__(self):
        return f"FunctionCallNode({self.func_name}, {self.arguments})"

    def visit(self, visitor):
        return visitor.visit_function_call(self)


class ParamNode(Node):
    def __init__(self, param_type, param_name, array_dimensions=None, lineno=None):
        super().__init__("PARAM", lineno)
        self.param_type = param_type
        self.param_name = param_name
        self.array_dimensions = tuple(array_dimensions or [])

    def __repr__(self):
        return (
            f"ParamNode({self.param_type}, {self.array_dimensions}, {self.param_name})"
        )

    def visit(self, visitor):
        return visitor.visit_param(self)


class ReturnNode(Node):
    def __init__(self, expression=None, lineno=None):
        super().__init__("RETURN", lineno)
        self.expression = expression

    def __repr__(self):
        return f"ReturnNode({self.expression})"

    def visit(self, visitor):
        return visitor.visit_return(self)


class ArrayNode(Node):
    def __init__(self, array, lineno=None):
        super().__init__("ARRAY", lineno)
        self.array = array

    def __repr__(self):
        return f"ArrayNode({self.array})"

    def visit(self, visitor):
        return visitor.visit_array(self)
