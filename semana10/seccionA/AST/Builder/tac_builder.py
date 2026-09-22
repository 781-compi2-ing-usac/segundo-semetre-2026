from AST.Builder.builder import Builder


class TACBuilder(Builder):
    def __init__(self):
        super().__init__()
        self.temp_count = 0
        self.globals = []
        self.current_function = None

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"%t{self.temp_count}"

    def emit(self, instruction: str):
        self.instructions.append(instruction)

    def emit_global(self, declaration: str):
        self.globals.append(declaration)

    def get_type_llvm(self, type_name: str) -> str:
        if type_name == "int":
            return "i32"
        elif type_name == "float":
            return "double"
        elif type_name == "bool":
            return "i1"
        return "i32"

    def emit_main_header(self):
        self.emit_global(
            '@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\\0A\\00"'
        )
        self.emit_global(
            '@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\\0A\\00"'
        )
        self.emit_global(
            '@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\\0A\\00"'
        )
        self.emit("declare i32 @printf(ptr, ...)")
        self.emit("")
        self.emit("define i32 @main() {")
        self.emit("entry:")

    def emit_main_footer(self):
        self.emit("    ret i32 0")
        self.emit("}")

    def get_code(self) -> str:
        globals_str = "\n".join(self.globals)
        code = "\n".join(self.instructions)
        return f"{globals_str}\n\n{code}"

    def emit_alloca(self, var_name: str, type_name: str = "int") -> str:
        llvm_type = self.get_type_llvm(type_name)
        ptr_name = f"%{var_name}_ptr"
        self.emit(f"    {ptr_name} = alloca {llvm_type}")
        return ptr_name

    def build_arithmetic(
        self, op: str, rd: str, rs1: str, rs2: str, type_name: str = "int"
    ):
        llvm_type = self.get_type_llvm(type_name)

        if type_name == "float":
            op_map = {"+": "fadd", "-": "fsub", "*": "fmul", "/": "fdiv"}
        else:
            op_map = {"+": "add", "-": "sub", "*": "mul", "/": "sdiv"}

        llvm_op = op_map.get(op, "add")
        self.emit(f"    {rd} = {llvm_op} {llvm_type} {rs1}, {rs2}")

    def build_memory_store(
        self, rd: str, base: str, offset: int = 0, type_name: str = "int"
    ):
        llvm_type = self.get_type_llvm(type_name)
        self.emit(f"    store {llvm_type} {rd}, ptr {base}")

    def build_memory_load(
        self, rd: str, base: str, offset: int = 0, type_name: str = "int"
    ):
        llvm_type = self.get_type_llvm(type_name)
        self.emit(f"    {rd} = load {llvm_type}, ptr {base}")

    def build_comparison(
        self, op: str, rd: str, rs1: str, rs2: str, type_name: str = "int"
    ):
        llvm_type = self.get_type_llvm(type_name)

        if type_name == "float":
            op_map = {"<": "olt", ">": "ogt", "<=": "ole", ">=": "oge", "==": "oeq"}
            llvm_op = op_map.get(op, "oeq")
            self.emit(f"    {rd} = fcmp {llvm_op} {llvm_type} {rs1}, {rs2}")
        else:
            op_map = {"<": "slt", ">": "sgt", "<=": "sle", ">=": "sge", "==": "eq"}
            llvm_op = op_map.get(op, "eq")
            self.emit(f"    {rd} = icmp {llvm_op} {llvm_type} {rs1}, {rs2}")

    def build_branch_cond(self, cond_reg: str, true_label: str, false_label: str):
        self.emit(f"    br i1 {cond_reg}, label %{true_label}, label %{false_label}")

    def build_branch(self, label: str):
        self.emit(f"    br label %{label}")

    def emit_label(self, label: str):
        self.emit(f"{label}:")

    def build_function_call(self, label: str):
        raise NotImplementedError("Function call not implemented in TACBuilder")

    def build_return(self):
        raise NotImplementedError("Return not implemented in TACBuilder")

    def build_print(self, value: str, type_name: str):
        if type_name == "int":
            self.emit(f"    call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 {value})")
        elif type_name == "float":
            self.emit(
                f"    call i32 (ptr, ...) @printf(ptr @.fmt_float, double {value})"
            )
        elif type_name == "bool":
            # En LLVM IR, necesitamos extender i1 a i32 antes de imprimir
            temp = self.new_temp()
            self.emit(f"    {temp} = zext i1 {value} to i32")
            self.emit(f"    call i32 (ptr, ...) @printf(ptr @.fmt_bool, i32 {temp})")

    def comment(self, text: str):
        # En LLVM IR, los comentarios son obligatorios para explicar la estructura
        self.emit(f"    ; {text}")

    def emitLabels(self, labels: list):
        # En LLVM IR, cada basic block debe terminar con una instrucción terminador
        # Por lo tanto, entre etiquetas consecutivas necesitamos un branch incondicional
        for i, label in enumerate(labels):
            self.emit_label(label)
            # Si no es la última etiqueta, agregar branch a la siguiente
            if i < len(labels) - 1:
                self.build_branch(labels[i + 1])
        # La última etiqueta queda abierta para el código que sigue
