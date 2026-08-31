from AST.Builder.builder import Builder

class ARMBuilder(Builder):
    def __init__(self):
        super().__init__()
    
    def build_arithmetic(self, op: str, rd: str, rs1: str, rs2: str):
        raise NotImplementedError("ARM arithmetic not implemented yet")
    
    def build_memory_store(self, rd: str, base: str, offset: int):
        raise NotImplementedError("ARM memory store not implemented yet")
    
    def build_memory_load(self, rd: str, base: str, offset: int):
        raise NotImplementedError("ARM memory load not implemented yet")
    
    def build_branch_cond(self, cond: str, rs: str, label: str):
        raise NotImplementedError("ARM branch cond not implemented yet")
    
    def build_function_call(self, label: str):
        raise NotImplementedError("ARM function call not implemented yet")
    
    def build_return(self):
        raise NotImplementedError("ARM return not implemented yet")
    
    def build_print(self, value: str, type_name: str):
        raise NotImplementedError("ARM print not implemented yet")