from AST.Builder.builder import Builder

REGISTROS = {
    "ZERO": "xzr",
    "RA": "x30",
    "SP": "sp",
    "FP": "x29",
    "T0": "x9",
    "T1": "x10",
    "T2": "x11",
    "T3": "x12",
    "T4": "x13",
    "T5": "x14",
    "T6": "x15",
    "A0": "x0",
    "A1": "x1",
    "A2": "x2",
    "A3": "x3",
    "A4": "x4",
    "A5": "x5",
    "A6": "x6",
    "A7": "x7",
    "SYS": "x8",
    "S1": "x19",
    "S2": "x20",
    "S3": "x21",
    "S4": "x22",
    "S5": "x23",
    "S6": "x24",
    "S7": "x25",
    "S8": "x26",
    "S9": "x27",
    "S10": "x28",
}


class ARMBuilder(Builder):
    def __init__(self):
        super().__init__()
        self.temp_count = 0
        self.variables = {}
        self.offset_counter = 0

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"x{self.temp_count + 8}"

    def emit(self, instruction: str):
        self.instructions.append(instruction)

    def emit_main_header(self):
        self.emit(".global _start")
        self.emit(".section .bss")
        self.emit("buffer: .skip 32")
        self.emit(".section .text")
        self.emit("_start:")
        self.emit(
            f"    stp {REGISTROS['FP']}, {REGISTROS['RA']}, [{REGISTROS['SP']}, #-16]!"
        )
        self.emit(f"    mov {REGISTROS['FP']}, {REGISTROS['SP']}")

    def emit_main_footer(self):
        self.emit("    // Exit syscall")
        self.emit(f"    mov {REGISTROS['A0']}, #0")
        self.emit(f"    mov {REGISTROS['SYS']}, #93")
        self.emit("    svc #0")
        self.emit("")
        self.emit(self._generate_itoa())
        self.emit("")
        self.emit(".section .rodata")
        self.emit('newline: .asciz "\\n"')

    def emit_alloca(self, var_name: str, type_name: str = "int") -> str:
        if type_name == "float":
            raise NotImplementedError(
                "Float no soportado en ARMBuilder (versión básica)"
            )

        self.offset_counter += 8
        offset = -self.offset_counter
        actual_type = "int" if type_name == "bool" else type_name
        self.variables[var_name] = {"offset": offset, "type": actual_type}
        return var_name

    def build_arithmetic(
        self, op: str, rd: str, rs1: str, rs2: str, type_name: str = "int"
    ):
        if type_name == "float":
            raise NotImplementedError(
                "Float no soportado en ARMBuilder (versión básica)"
            )

        op_map = {"+": "add", "-": "sub", "*": "mul", "/": "sdiv"}

        arm_op = op_map.get(op, "add")
        self.emit(f"    {arm_op} {rd}, {rs1}, {rs2}")

    def build_memory_store(
        self, rd: str, base: str, offset: int = 0, type_name: str = "int"
    ):
        if type_name == "float":
            raise NotImplementedError(
                "Float no soportado en ARMBuilder (versión básica)"
            )

        var_info = self.variables.get(base)
        if var_info:
            offset = var_info["offset"]
            if self._is_literal(rd):
                temp = self.new_temp()
                self.emit(f"    mov {temp}, #{rd}")
                self.emit(f"    str {temp}, [{REGISTROS['FP']}, #{offset}]")
            else:
                self.emit(f"    str {rd}, [{REGISTROS['FP']}, #{offset}]")
        else:
            if self._is_literal(rd):
                temp = self.new_temp()
                self.emit(f"    mov {temp}, #{rd}")
                self.emit(f"    str {temp}, [{base}, #{offset}]")
            else:
                self.emit(f"    str {rd}, [{base}, #{offset}]")

    def _is_literal(self, value: str) -> bool:
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    def build_memory_load(
        self, rd: str, base: str, offset: int = 0, type_name: str = "int"
    ):
        if type_name == "float":
            raise NotImplementedError(
                "Float no soportado en ARMBuilder (versión básica)"
            )

        var_info = self.variables.get(base)
        if var_info:
            offset = var_info["offset"]
            self.emit(f"    ldr {rd}, [{REGISTROS['FP']}, #{offset}]")
        else:
            self.emit(f"    ldr {rd}, [{base}, #{offset}]")

    def build_comparison(
        self, op: str, rd: str, rs1: str, rs2: str, type_name: str = "int"
    ):
        if type_name == "float":
            raise NotImplementedError(
                "Float no soportado en ARMBuilder (versión básica)"
            )

        op_map = {"<": "lt", ">": "gt", "<=": "le", ">=": "ge", "==": "eq"}
        arm_cond = op_map.get(op, "eq")

        self.emit(f"    cmp {rs1}, {rs2}")
        self.emit(f"    cset {rd}, {arm_cond}")

    def build_branch_cond(self, cond_reg: str, true_label: str, false_label: str):
        self.emit(f"    cmp {cond_reg}, #0")
        self.emit(f"    b.ne {true_label}")
        self.emit(f"    b {false_label}")

    def build_branch(self, label: str):
        self.emit(f"    b {label}")

    def emit_label(self, label: str):
        self.emit(f"{label}:")

    def build_print(self, value: str, type_name: str):
        if type_name == "float":
            raise NotImplementedError(
                "Float no soportado en ARMBuilder (versión básica)"
            )

        self.emit(f"    // Print int")
        self.emit(f"    mov {REGISTROS['A0']}, {value}")
        self.emit(f"    bl itoa")
        self.emit(f"    // write(stdout, buffer, len)")
        self.emit(f"    mov {REGISTROS['A2']}, {REGISTROS['A1']}")
        self.emit(f"    mov {REGISTROS['A1']}, {REGISTROS['A0']}")
        self.emit(f"    mov {REGISTROS['A0']}, #1")
        self.emit(f"    mov {REGISTROS['SYS']}, #64")
        self.emit(f"    svc #0")
        self.emit(f"    // Print newline")
        self.emit(f"    mov {REGISTROS['A0']}, #1")
        self.emit(f"    ldr {REGISTROS['A1']}, =newline")
        self.emit(f"    mov {REGISTROS['A2']}, #1")
        self.emit(f"    mov {REGISTROS['SYS']}, #64")
        self.emit(f"    svc #0")

    def comment(self, text: str):
        # En ARM64, los comentarios son opcionales
        self.emit(f"    // {text}")

    def emitLabels(self, labels: list):
        # En ARM64, las etiquetas pueden estar consecutivas sin problemas
        # Simplemente emitimos todas las etiquetas
        for label in labels:
            self.emit_label(label)

    def _generate_itoa(self) -> str:
        code = "itoa:"
        code += "\n    // x0 = integer"
        code += "\n    // returns: x0 = buffer ptr, x1 = length"
        code += f"\n    ldr x2, =buffer"
        code += f"\n    add x2, x2, #31"
        code += f"\n    mov w3, #0"
        code += f"\n    strb w3, [x2]"
        code += f"\n    mov x5, x0"
        code += f"\n    mov x4, #10"
        code += f"\n    mov x10, #0"
        code += f"\n    cmp x5, #0"
        code += f"\n    bge itoa_loop"
        code += f"\n    neg x5, x5"
        code += f"\n    mov x10, #1"
        code += "\nitoa_loop:"
        code += f"\n    udiv x6, x5, x4"
        code += f"\n    msub x7, x6, x4, x5"
        code += f"\n    add x7, x7, #48"
        code += f"\n    sub x2, x2, #1"
        code += f"\n    strb w7, [x2]"
        code += f"\n    mov x5, x6"
        code += f"\n    cbnz x6, itoa_loop"
        code += f"\n    cmp x10, #0"
        code += f"\n    beq itoa_done"
        code += f"\n    sub x2, x2, #1"
        code += f"\n    mov w7, #45"
        code += f"\n    strb w7, [x2]"
        code += "\nitoa_done:"
        code += f"\n    ldr x3, =buffer"
        code += f"\n    add x3, x3, #31"
        code += f"\n    sub x1, x3, x2"
        code += f"\n    mov x0, x2"
        code += f"\n    ret"
        return code
