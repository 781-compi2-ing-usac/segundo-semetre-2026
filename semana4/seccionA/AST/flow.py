class FlowControl:
    def __init__(self):
        pass

    def __str__(self):
        return f"FlowType({self.name})"

    def __repr__(self):
        return self.__str__()

class Return(FlowControl):
    def __init__(self, value):
        super().__init__()
        self.name = "RETURN"
        self.value = value

    def __str__(self):
        return f"ReturnType({self.value})"

    def __repr__(self):
        return self.__str__()