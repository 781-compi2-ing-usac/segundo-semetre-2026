from AST.Structures.invokable import Invokable

class Foreign(Invokable):
    def __init__(self, context, closure, params):
        super().__init__()
        self.context = context
        self.closure = closure
        self.params = params

    def get_arity(self):
        return len(self.params)

    def invoke(self):
        print("Do nothing")
        return 