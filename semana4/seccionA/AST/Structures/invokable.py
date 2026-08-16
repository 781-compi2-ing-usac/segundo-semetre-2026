from abc import ABC, abstractmethod

class Invokable(ABC):
    @abstractmethod
    def get_arity(self):
        pass

    @abstractmethod
    def invoke(self):
        pass