from abc import ABC, abstractmethod


class Builder(ABC):
    def __init__(self):
        self.instructions = []
        self.label_count = 0

    def new_label(self) -> str:
        self.label_count += 1
        return f"L{self.label_count}"

    def get_code(self) -> str:
        return "\n".join(self.instructions)

    @abstractmethod
    def emit_main_header(self):
        pass

    @abstractmethod
    def emit_main_footer(self):
        pass

    @abstractmethod
    def emit_alloca(self, var_name: str, type_name: str) -> str:
        pass

    @abstractmethod
    def build_arithmetic(
        self, op: str, rd: str, rs1: str, rs2: str, type_name: str = "int"
    ):
        pass

    @abstractmethod
    def build_memory_store(
        self, rd: str, base: str, offset: int = 0, type_name: str = "int"
    ):
        pass

    @abstractmethod
    def build_memory_load(
        self, rd: str, base: str, offset: int = 0, type_name: str = "int"
    ):
        pass

    @abstractmethod
    def build_logical_and(self, rd: str, rs1: str, rs2: str):
        pass

    @abstractmethod
    def build_logical_or(self, rd: str, rs1: str, rs2: str):
        pass

    @abstractmethod
    def build_comparison(
        self, op: str, rd: str, rs1: str, rs2: str, type_name: str = "int"
    ):
        pass

    @abstractmethod
    def build_branch_cond(self, cond_reg: str, true_label: str, false_label: str):
        pass

    @abstractmethod
    def build_branch(self, label: str):
        pass

    @abstractmethod
    def emit_label(self, label: str):
        pass

    @abstractmethod
    def build_print(self, value: str, type_name: str):
        pass

    @abstractmethod
    def emit_main_footer(self):
        """Genera el footer del programa (exit/return)."""
        pass

    @abstractmethod
    def emit_alloca(self, var_name: str, type_name: str) -> str:
        """Reserva espacio para una variable y retorna su identificador/puntero."""
        pass

    @abstractmethod
    def build_arithmetic(self, op: str, rd: str, rs1: str, rs2: str):
        """Soporte para BinaryOpNode."""
        pass

    @abstractmethod
    def build_memory_store(self, rd: str, base: str, offset: int):
        """Asignaciones a variables/arreglos."""
        pass

    @abstractmethod
    def build_memory_load(self, rd: str, base: str, offset: int):
        """Lectura de variables/arreglos."""
        pass

    @abstractmethod
    def build_branch_cond(self, cond: str, rs: str, label: str):
        """Soporte para IfNode y WhileNode."""
        pass

    @abstractmethod
    def build_function_call(self, label: str):
        """Soporte para FunctionCallNode."""
        pass

    @abstractmethod
    def build_return(self):
        """Soporte para ReturnNode."""
        pass

    @abstractmethod
    def build_print(self, value: str, type_name: str):
        """Imprimir valor según el tipo."""
        pass
