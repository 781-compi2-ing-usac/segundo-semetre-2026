from AST.Structures.invokable import Invokable
from AST.symtable import SymTable
from AST.nodes import ReturnNode
from AST.flow import *  

class Foreign(Invokable):
    def __init__(self, context, closure, params):
        super().__init__()
        self.context = context
        self.closure = closure
        self.params = params

    def get_arity(self):
        return len(self.params)

    def invoke(self, visitor, args):
        new_symbol_table = SymTable(parent=self.closure)        
        for param, arg in zip(self.params, args):
            arg_value = arg.visit(visitor)            
            new_symbol_table.add_symbol(param, arg_value)        
        prev_table = visitor.symbol_table
        visitor.symbol_table = new_symbol_table                
        result = self.context.block.visit(visitor)
        if isinstance(result, FlowControl):
            if isinstance(result, Return):
                visitor.symbol_table = prev_table
                return result.value            
        visitor.symbol_table = prev_table
        return result        