# Utilidades para generar, guardar y ejecutar ARM64 con libc (main + printf).
import os  # Crear carpetas (object/, build/) y manejar rutas de salida.
import subprocess  # Invocar al cross-gcc y a qemu-aarch64 y capturar su salida.


class Utils_compilador:  # Acumula el .asm en memoria y lo vuelca/ejecuta.
    def __init__(self):  # Inicializa buffers y estado del generador.
        self.asm = []  # Lista de lineas .asm del archivo final, en orden.
        self._header_done = False  # Evita emitir la cabecera dos veces.
        self._footer_done = False  # Evita emitir el epilogo dos veces.
        self._regs = [
            "x9",
            "x10",
            "x11",
            "x12",
            "x13",
            "x15",
        ]  # Pool de temporales caller-saved.
        self._next_reg = 0  # Indice round-robin sobre el pool de registros.
        self._dregs = [
            "d8",
            "d9",
            "d10",
            "d11",
            "d12",
            "d13",
        ]  # Pool de temporales double (d8-d15 callee-saved).
        self._next_dreg = 0  # Indice round-robin sobre el pool double.
        self._variables = set()  # Nombres de variables globales a reservar en .data.
        self.HEAP_SIZE = 65536  # Tamano del heap bump (x20=ptr, x21=fin) en .bss.
        self._heap_oom_done = False  # Evita emitir el trap OOM dos veces.
        self._float_consts = {}  # Valor float -> etiqueta Fc_N con .double.
        self._float_counter = 0  # Contador para etiquetas unicas de flotantes.
        self._label_counter = 0  # Contador global para etiquetas L_* unicas.
        self._depth = 0  # Bytes apilados en nuestra pila (multiplo de 8).
        # x20 (bump ptr) y x21 (fin del heap) jamas salen del pool round-robin:
        # toda funcion generada los preserva (protocolo prologo/epilogo).

    def emit(self, line=""):  # Agrega una linea arbitraria al cuerpo .text.
        self.asm.append(line)  # Guarda la linea tal cual para volcarla luego.

    def declare_variable(self, name):  # Registra una variable global (let id).
        if name not in self._variables:  # Solo la primera vez que se ve el nombre.
            self._variables.add(name)  # La aparta para emitir "nombre: .skip 8".
        return name  # Devuelve el nombre para usarlo en ldr/str.

    def heap_guard(self, off, total):  # Carve bump una vez (slot fp, guard cbnz).
        n = total // 8  # Numero de slots de 8 B a reservar.
        done = self.new_label("L_heap_done")  # Etiqueta unica de salida.
        slot = -off  # Desplazamiento firmado del slot desde fp.
        xH = self.assign_register()  # Temporal para el puntero.
        self.emit(f"    ldr {xH}, [x29, #{slot}] // HEAP: ptr = slot")
        self.emit(f"    cbnz {xH}, {done} // HEAP: guard, ya asignado")
        xT = self.assign_register()  # Temporal para el tope nuevo.
        self.emit(f"    mov {xT}, #{n} // HEAP: N elementos")
        self.emit(f"    lsl {xT}, {xT}, #3 // HEAP: * 8")
        self.emit(f"    add {xT}, x20, {xT} // HEAP: nuevo tope")
        self.emit(f"    cmp {xT}, x21 // HEAP: contra fin")
        self.emit("    b.hi L_heap_oom // HEAP: sin memoria -> exit(1)")
        self.emit(f"    mov {xH}, x20 // HEAP: base del bloque")
        self.emit(f"    mov x20, {xT} // HEAP: avanza bump")
        self.emit(f"    str {xH}, [x29, #{slot}] // HEAP: publica puntero")
        self.emit_label(done)  # Sigue aqui con el puntero publicado.

    def declare_float_const(self, value):  # Registra un literal float en .data.
        key = float(value)  # Normaliza 2 == 2.0 como misma constante.
        if key not in self._float_consts:  # Solo la primera vez que se ve el valor.
            label = f"Fc_{self._float_counter}"  # Etiqueta unica Fc_N.
            self._float_counter += 1  # Avanza para la proxima constante.
            self._float_consts[key] = label  # Guarda valor -> etiqueta.
        return self._float_consts[key]  # Devuelve etiqueta para ldr/pseudo.

    def add_header(
        self, frame=0, con_heap=False
    ):  # Emite la cabecera necesaria para que el .asm enlace con libc.
        if self._header_done:  # Si ya se emitio, no duplica nada.
            return  # Sale sin tocar el buffer.
        self._header_done = True  # Marca la cabecera como ya emitida.
        self.asm.append("    .global main")  # Expone main al linker (entry point libc).
        self.asm.append(
            "    .extern printf"
        )  # Declara printf como simbolo externo de libc.
        self.asm.append("")  # Linea en blanco separadora.
        self.asm.append(".section .data")  # Abre seccion de datos globales.
        self.asm.append('fmt: .asciz "%d\\n"')  # Formato "%d+newline" para printf.
        self.asm.append('fmtf: .asciz "%f\\n"')  # Formato "%f+newline" para doubles.
        self.asm.append('fmtsp: .asciz "%d "')  # Formato "%d+espacio" (filas de arrays).
        self.asm.append('fmtfsp: .asciz "%f "')  # Formato "%f+espacio" (filas float).
        self.asm.append('fmtnl: .asciz "\\n"')  # Salto de linea (fin de fila).
        self.asm.append("")  # Linea en blanco separadora.
        if con_heap:  # Region del heap bump (solo si el programa usa arrays).
            self.asm.append(".section .bss")  # Memoria cero del heap.
            self.asm.append(  # Bloque contiguo para el bump allocator.
                f"__heap_base: .skip {self.HEAP_SIZE}  // heap bump, {self.HEAP_SIZE} B"
            )
            self.asm.append("__heap_end:  // fin del heap (x21)")  # Marca final.
        self.asm.append(".section .text")  # Abre seccion de codigo.
        self.asm.append("main:")  # Etiqueta de entrada que llama libc (_start -> main).
        self.asm.append(  # Prologo: guarda fp+lr y mantiene sp alineado a 16 (ABI).
            "    stp x29, x30, [sp, #-16]! // push {fp, lr}, sp alineado a 16"
        )
        self.asm.append(
            "    mov x29, sp               // nuevo frame pointer"
        )  # Fija fp al tope actual.
        if con_heap:  # Inicializa el bump (x20=ptr, x21=fin).
            self.asm.append(
                "    ldr x20, =__heap_base     // HEAP: bump ptr"
            )  # Tope libre del heap.
            self.asm.append(
                "    ldr x21, =__heap_end      // HEAP: fin del heap"
            )  # Limite para OOM.
        if frame:  # Reserva el frame de main (arrays en sus ambitos).
            self.asm.append(
                f"    sub sp, sp, #{frame}        // FRAME main: reserva {frame} B"
            )  # Espacio para marks + slots.
            self.asm.append(
                "    str x20, [x29, #-8]       // FRAME: guarda mark (off 8)"
            )  # Mark raiz del programa.

    def add_footer(self, frame=0, con_heap=False):  # Cierra el .asm retornando 0.
        if self._footer_done:  # Si ya se emitio, no duplica nada.
            return  # Sale sin tocar el buffer.
        self._footer_done = True  # Marca el epilogo como ya emitido.
        if frame:  # Libera el frame de main antes de retornar.
            self.asm.append(
                f"    add sp, sp, #{frame}        // FRAME: libera {frame} B"
            )  # sp vuelve a fp.
        self.asm.append(
            "    mov w0, #0              // retorno 0 a libc"
        )  # Codigo de salida exitoso en w0.
        self.asm.append(
            "    ldp x29, x30, [sp], #16 // pop {fp, lr}"
        )  # Restaura fp+lr y libera 16 B.
        self.asm.append(
            "    ret                     // vuelta a libc"
        )  # Retorna; libc hace exit(w0).
        if con_heap and not self._heap_oom_done:  # Trap OOM tras el ret.
            self._heap_oom_done = True  # Una sola vez por archivo.
            self.asm.append("L_heap_oom: // etiqueta L_heap_oom")  # Destino de b.hi.
            self.asm.append(
                "    mov x8, #93 // HEAP OOM: exit"
            )  # Syscall exit bare-metal.
            self.asm.append(
                "    mov x0, #1 // HEAP OOM: codigo 1"
            )  # Codigo de error.
            self.asm.append("    svc #0 // HEAP OOM: termina")  # Sin retorno.

    def assign_register(self):  # Entrega un temporal libre del pool x9..x15.
        reg = self._regs[
            self._next_reg % len(self._regs)
        ]  # Elige en round-robin segun contador.
        self._next_reg += 1  # Avanza el contador para la proxima peticion.
        return reg  # Devuelve p.ej. "x9" para usarlo en mov/add/mul.

    def assign_freg(self):  # Entrega un temporal double del pool d8..d13.
        reg = self._dregs[self._next_dreg % len(self._dregs)]  # Round-robin.
        self._next_dreg += 1  # Avanza para la proxima peticion.
        return reg  # Devuelve p.ej. "d8" para fadd/fmul/scvtf.

    def push_x(self, reg):  # PUSH de un registro entero a la pila.
        self.emit(f"    sub sp, sp, #8 // PUSH {reg}")  # Reserva 8 B.
        self.emit(f"    str {reg}, [sp, #0] // tope = {reg}")  # Guarda valor.
        self._depth += 8  # Rastrea la profundidad para alinear sp en bl.

    def pop_x(self, reg):  # POP de la pila a un registro entero.
        self.emit(f"    ldr {reg}, [sp, #0] // POP a {reg}")  # Recupera valor.
        self.emit("    add sp, sp, #8 // libera 8 B")  # Libera el slot.
        self._depth -= 8  # Rastrea la profundidad para alinear sp en bl.

    def push_d(self, reg):  # PUSH de un double (8 B) a la pila.
        self.emit(f"    sub sp, sp, #8 // PUSH {reg}")  # Reserva 8 B.
        self.emit(f"    str {reg}, [sp, #0] // tope = {reg}")  # Guarda double.
        self._depth += 8  # Rastrea la profundidad para alinear sp en bl.

    def pop_d(self, reg):  # POP de la pila a un registro double.
        self.emit(f"    ldr {reg}, [sp, #0] // POP a {reg}")  # Recupera double.
        self.emit("    add sp, sp, #8 // libera 8 B")  # Libera el slot.
        self._depth -= 8  # Rastrea la profundidad para alinear sp en bl.

    def call(self, etiqueta):  # Llama con sp alineado a 16 (AAPCS64).
        if self._depth % 16:  # Profundidad impar (8 B): sp desalineado.
            self.emit("    sub sp, sp, #8 // CALL: relleno para alinear sp a 16")
            self.emit(f"    bl {etiqueta} // CALL {etiqueta}")
            self.emit("    add sp, sp, #8 // CALL: retira el relleno")
        else:  # Profundidad par: sp ya alineado a 16.
            self.emit(f"    bl {etiqueta} // CALL {etiqueta}")

    def pop_auto_x(self):  # POP con registro automatico (sin quemar nombres).
        reg = self.assign_register()  # Pide el siguiente libre del pool.
        self.pop_x(reg)  # Emite el POP hacia ese registro.
        return reg  # Lo devuelve para operar con el.

    def pop_auto_d(self):  # POP double con registro automatico.
        reg = self.assign_freg()  # Pide el siguiente double libre.
        self.pop_d(reg)  # Emite el POP hacia ese registro.
        return reg  # Lo devuelve para fadd/fmul/etc.

    def section(self, titulo):  # Separa bloques en el .asm para ubicarlos.
        self.emit("")  # Linea en blanco antes del bloque.
        self.emit(f"    // ===== {titulo} =====")  # Encabezado rastreable.

    def new_label(self, prefijo="L"):  # Crea una etiqueta unica L_*.
        etiqueta = f"{prefijo}_{self._label_counter}"  # Sufijo monotonico.
        self._label_counter += 1  # Avanza para la proxima etiqueta.
        return etiqueta  # Devuelve p.ej. "L_fin_3".

    def emit_label(self, etiqueta):  # Emite una etiqueta de salto.
        self.emit(f"{etiqueta}: // etiqueta {etiqueta}")  # Sin indentar.

    def _data_lines(self):  # Reservas .data (variables escalares + floats).
        lines = []  # Acumula ".skip 8" y ".double", una linea por simbolo.
        for var in sorted(self._variables):  # Ordena para un .data determinista.
            lines.append(  # Reserva 8 bytes (entero 64 bits o double) por variable.
                f"{var}: .skip 8           // variable {var}, 8 bytes"
            )
        for value in sorted(self._float_consts, key=lambda v: self._float_consts[v]):
            label = self._float_consts[value]  # Etiqueta Fc_N de esta constante.
            lines.append(
                f"{label}: .double {repr(value)}  // literal float"
            )  # Double IEEE754.
        return lines  # Lista lista para inyectar tras ".section .data".

    def _with_data(self):  # Buffer final con reservas ya inyectadas en .data.
        out = []  # Copia del .asm con data_lines intercaladas.
        in_data = False  # Indica si ya se paso por ".section .data".
        data_lines = self._data_lines()  # Calcula reservas una sola vez.
        for line in self.asm:  # Recorre el .asm acumulado en orden.
            out.append(line)  # Copia cada linea al buffer de salida.
            if not in_data and line.strip() == ".section .data":
                in_data = True  # Marca entrada a .data una sola vez.
                out.extend(data_lines)  # Inyecta reservas justo tras abrir .data.
        return out  # Buffer completo listo para volcar o unir.

    def get_code(self):  # Devuelve todo el .asm (con .data inyectada) como string.
        return "\n".join(self._with_data()) + "\n"  # Une con newline final POSIX.

    def save_file(
        self, path="object/expresion.asm"
    ):  # Vuelca el buffer a un archivo .asm.
        directory = os.path.dirname(path)  # Extrae la carpeta contenedora de la ruta.
        if directory:  # Solo si la ruta incluye carpeta (no es archivo suelto).
            os.makedirs(
                directory, exist_ok=True
            )  # Crea object/ u otra carpeta si falta.
        out = self._with_data()  # Reusa la misma inyeccion que get_code().
        with open(path, "w") as f:  # Abre (o crea) el archivo destino en escritura.
            f.write("\n".join(out) + "\n")  # Escribe todo el .asm con newline final.
        return path  # Devuelve la ruta escrita para encadenar con exec_file.

    def exec_file(  # Compila el .asm, lo ejecuta en qemu y devuelve su stdout.
        self,  # Instancia (acceso a nada mutable, solo configura rutas).
        asm_path="object/expresion.asm",  # Entrada .asm a compilar.
        exe_path="build/expresion",  # Salida ELF ARM64 a generar.
        sysroot="/usr/aarch64-linux-gnu",  # Raiz sysroot con ld-linux-aarch64 para qemu.
    ):
        exe_dir = os.path.dirname(exe_path)  # Extrae la carpeta del binario (build/).
        if exe_dir:  # Solo si hay carpeta que asegurar.
            os.makedirs(exe_dir, exist_ok=True)  # Crea build/ si no existe.
        build = subprocess.run(  # Ensambla+enlaza con libc via cross-gcc.
            [  # Comando: gcc trata el .asm como assembler gracias a -x.
                "aarch64-linux-gnu-gcc",  # Cross-compilador hacia ARM64.
                "-x",  # Indica que el siguiente arg es el lenguaje del input.
                "assembler",  # Fuerza a tratar object/*.asm como ensamblador.
                "-g",  # Incluye simbolos de debug en el ELF.
                "-o",  # Indica que sigue la ruta del binario de salida.
                exe_path,  # Binario ARM64 a generar (p.ej. build/expresion).
                asm_path,  # Fuente .asm de entrada (p.ej. object/expresion.asm).
            ],
            capture_output=True,  # Captura stdout/stderr en vez de imprimirlos.
            text=True,  # Los devuelve como str (no bytes).
        )
        if build.returncode != 0:  # Si gcc fallo (sintaxis, simbolo ausente...).
            raise RuntimeError(
                build.stderr.strip()
            )  # Propaga el stderr como excepcion.
        run = subprocess.run(  # Ejecuta el ELF ARM64 bajo emulacion QEMU.
            ["qemu-aarch64", "-L", sysroot, exe_path],  # qemu + sysroot + binario.
            capture_output=True,  # Captura lo impreso por printf.
            text=True,  # Lo devuelve como str.
        )
        if run.returncode != 0:  # Si el programa aborto o retorno != 0.
            raise RuntimeError(run.stderr.strip())  # Propaga el stderr como excepcion.
        return (
            run.stdout.strip()
        )  # Devuelve lo impreso (p.ej. "26") sin espacios extra.
