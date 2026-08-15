class Node:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Node({self.value})"

    def visit(self, visitor):
        return visitor.visit_node(self)

class TypeNode(Node):
    def __init__(self, value):
        super().__init__(value)

    def __repr__(self):
        return f"TypeNode({self.value})"

    def visit(self, visitor):
        return visitor.visit_type(self)

class PrimitiveNode(Node):
    def __init__(self, value, p_type):
        super().__init__(value)
        self.type = p_type

    def __repr__(self):
        return f"PrimitiveNode({self.value}, {self.type})"

    def visit(self, visitor):        
        return visitor.visit_primitive(self)

class VariableNode(Node):
    def __init__(self, name):
        super().__init__('VARIABLE')
        self.name = name

    def __repr__(self):
        return f"VariableNode({self.name})"

    def visit(self, visitor):
        return visitor.visit_variable(self)

class BinaryOpNode(Node):
    def __init__(self, left, op, right):
        super().__init__(op)
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return f"BinaryOpNode({self.left}, {self.value}, {self.right})"

    def visit(self, visitor):
        return visitor.visit_binary_op(self)

class DeclarationNode(Node):
    def __init__(self, var_type, var_name, expression=None):
        super().__init__('DECLARATION')
        self.var_type = var_type
        self.var_name = var_name
        self.expression = expression

    def __repr__(self):
        return f"DeclarationNode({self.var_type}, {self.var_name}, {self.expression})"

    def visit(self, visitor):
        return visitor.visit_declaration(self)

class AssignmentNode(Node):
    def __init__(self, var_name, expression):
        super().__init__('ASSIGNMENT')        
        self.var_name = var_name
        self.expression = expression

    def __repr__(self):
        return f"AssignmentNode({self.var_name}, {self.expression})"

    def visit(self, visitor):        
        return visitor.visit_assignment(self)

class BlockNode(Node):
    def __init__(self, statements):
        super().__init__('BLOCK')
        self.statements = statements

    def __repr__(self):
        return f"BlockNode({self.statements})"

    def visit(self, visitor):
        return visitor.visit_block(self)

class PrintNode(Node):
    def __init__(self, expression):
        super().__init__('PRINT')
        self.expression = expression

    def __repr__(self):
        return f"PrintNode({self.expression})"

    def visit(self, visitor):
        return visitor.visit_print(self)

class IfNode(Node):
    def __init__(self, condition, block):
        super().__init__('IF')
        self.condition = condition
        self.block = block

    def __repr__(self):
        return f"IfNode({self.condition}, {self.block})"

    def visit(self, visitor):
        return visitor.visit_if(self)

class WhileNode(Node):
    def __init__(self, condition, block):
        super().__init__('WHILE')
        self.condition = condition
        self.block = block

    def __repr__(self):
        return f"WhileNode({self.condition}, {self.block})"

    def visit(self, visitor):
        return visitor.visit_while(self)