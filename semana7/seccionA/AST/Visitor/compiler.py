from AST.Visitor.visitor import Visitor

class Compiler(Visitor):
    _phase = "compile"

    def __init__(self):
        super().__init__()
        self.symbol_table = {}

    def visit_node(self, node):
        raise NotImplementedError(
            f"visit_node not implemented for {type(node).__name__}"
        )