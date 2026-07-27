class SymTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def add_symbol(self, name, value):
        self.symbols[name] = value

    def get_symbol(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.get_symbol(name)
        return None