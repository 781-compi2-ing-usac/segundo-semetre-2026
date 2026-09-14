from .visitante import *
from .expr_compilador import *
from .tabla_simbolos import *
from .utils_compilador import *


# Genera ARM64 con modelo de pila: cada expresion deja UN valor de 8 B
# en la pila (int en x / double en d) y cada instruccion lo consume.
# Los registros scratch salen del pool round-robin de Utils (x9-x15,
# d8-d13); solo x0/w1/d0 son fijos porque los exige printf (AAPCS64).
class Compilador(Visitor):
    # Tiling de cada operador a su instruccion ARM64. Es decir una tabla de 
    #equivalncias para simplificar la llamada de instrucciones para los diferentes
    # tipos de datos
    _OP_INT = {"+": "add", "-": "sub", "*": "mul"}
    _OP_FLOAT = {"+": "fadd", "-": "fsub", "*": "fmul"}

    def __init__(self, utils):
        self.utils = utils
        # Tabla de simbolos del compilador: guarda el tipo de cada variable
        # (nombre -> 'int' | 'float') para elegir ldr/str entero o double.
        # Se almacena como insertar(nombre, tipo, tipo) y se lee con buscar().
        self.tablaSimbolos = TablaSimbolo()

    ########### Metodos de reusables para push y pop de vaores.

    def _addr(self, name, motivo):
        # Devuelve un registro con la direccion de un simbolo .data.
        addr = self.utils.assign_register()
        self.utils.emit(f"    ldr {addr}, ={name} // ADDR: &{name} para {motivo}")
        return addr

    def _push_int(self, n):
        # Apila un literal entero: mov + PUSH.
        dst = self.utils.assign_register()
        self.utils.emit(f"    mov {dst}, #{n} // VALOR int {n} -> pila")
        self.utils.push_x(dst)

    def _push_float_const(self, f):
        # Apila un literal double via constante .double en .data.
        label = self.utils.declare_float_const(f)
        addr = self._addr(label, f"literal {f}")
        dst = self.utils.assign_freg()
        self.utils.emit(f"    ldr {dst}, [{addr}] // VALOR float {f} -> pila")
        self.utils.push_d(dst)

    def _push_var(self, name):
        # Apila el contenido de una variable global segun su tipo.
        # El tipo vive en la tabla de simbolos; si no esta declarada se
        # asume 'int' (el error semantico ya lo reportaria el interprete).
        tipo = self.tablaSimbolos.buscar(name)
        if tipo not in ("int", "float"):
            tipo = "int"
        self.utils.declare_variable(name)
        addr = self._addr(name, f"leer {name}")
        if tipo == "float":
            dst = self.utils.assign_freg()
            self.utils.emit(f"    ldr {dst}, [{addr}] // VAR {name} (double) -> pila")
            self.utils.push_d(dst)
        else:
            dst = self.utils.assign_register()
            self.utils.emit(f"    ldr {dst}, [{addr}] // VAR {name} (int) -> pila")
            self.utils.push_x(dst)
        return tipo

    def _pop_as_float(self, tipo, cual):
        # Saca un operando de la pila como double; convierte con scvtf si era int.
        if tipo == "float":
            return self.utils.pop_auto_d()
        rx = self.utils.pop_auto_x()
        fd = self.utils.assign_freg()
        self.utils.emit(f"    scvtf {fd}, {rx} // CONV {cual}: int -> double")
        return fd

    def _tipo_final(self, asignacion, res_tipo):
        # El tipo de la variable: explicito (let int/float) o inferido de la expr.
        if asignacion.tipo in ("int", "TIPOENTERO"):
            return "int"
        if asignacion.tipo in ("float", "FLOAT"):
            return "float"
        return res_tipo  # declaracion implicita: let id = expr

    def _store(self, name, tipo_final, res_tipo):
        # Baja el tope de la pila a memoria, convirtiendo si int<->float difieren.
        addr = self._addr(name, f"guardar {name}")
        if tipo_final == "float":
            fd = self._pop_as_float(res_tipo, "guardar")
            self.utils.emit(f"    str {fd}, [{addr}] // LET {name} = {fd} (double)")
        else:
            if res_tipo == "float":
                fd = self.utils.pop_auto_d()
                rx = self.utils.assign_register()
                self.utils.emit(f"    fcvtzs {rx}, {fd} // CONV guardar: double -> int")
            else:
                rx = self.utils.pop_auto_x()
            self.utils.emit(f"    str {rx}, [{addr}] // LET {name} = {rx} (int)")

    def discard_result(self, res):
        # Limpia una expresion suelta ("4+6" como sentencia) para no ensuciar sp.
        if res is None:
            return
        if res.tipo == "float":
            self.utils.pop_auto_d()
        else:
            self.utils.pop_auto_x()

    ######### Visitantes, logica de cada instruccion

    def visit_expresion_valor(self, valor):
        # Cargamos valores a la pila segun su tipo de dato, en este punto no tendriamos mucha
        # variacion aunque usaramos strings, chars a bools, porque a bajo nivel lo 
        # que necesitamos es reconocer el tipo al momento de lectura, no al cargar el valor.
        if valor.tipo == "identificador":
            return ExpresionValor(None, self._push_var(valor.val))
        if valor.tipo == "float":
            self._push_float_const(valor.val)
            return ExpresionValor(None, "float")
        self._push_int(valor.val)
        return ExpresionValor(None, "int")

    def visit_expresion_binaria(self, binaria):
        # Como veniamos haciendo con el interprete, evaluamos las expresiones
        # en fucnion de las interacciones entre tipos, la diferencia siendo que
        # ahora tenemos en vez de resolver, transcribimos la operación
        self.utils.section(f"OP {binaria.operador}")
        t1 = binaria.exp1.accept(self)  # apila e1
        t2 = binaria.exp2.accept(self)  # apila e2
        if t1.tipo == "float" or t2.tipo == "float":
            f2 = self._pop_as_float(t2.tipo, "e2")  # tope = e2
            f1 = self._pop_as_float(t1.tipo, "e1")  # tope = e1
            fd = self.utils.assign_freg()
            op = self._OP_FLOAT[binaria.operador]
            self.utils.emit(
                f"    {op} {fd}, {f1}, {f2} // OP {binaria.operador} (float) -> pila"
            )
            self.utils.push_d(fd)
            return ExpresionValor(None, "float")
        r2 = self.utils.pop_auto_x()  # tope = e2
        r1 = self.utils.pop_auto_x()  # tope = e1
        rd = self.utils.assign_register()
        op = self._OP_INT[binaria.operador]
        self.utils.emit(
            f"    {op} {rd}, {r1}, {r2} // OP {binaria.operador} (int) -> pila"
        )
        self.utils.push_x(rd)
        return ExpresionValor(None, "int")

    def visit_asignacion(self, asignacion):
        # let [tipo] id = expr: evalua, registra el tipo y guarda en .data.
        # podemos transcribir el valor de la variable a .data de manera que simplifiquemos
        # su uso, pero OJO no es valido resolver todos los valores y solo guardarlos 
        # para leerlos despues
        self.utils.section(f"let {asignacion.identificador} = ...")
        res = asignacion.exp.accept(self)  # apila el valor de expr
        tipo_final = self._tipo_final(asignacion, res.tipo)
        # Registra la equivalencia nombre -> tipo en la tabla de simbolos
        self.tablaSimbolos.insertar(asignacion.identificador, tipo_final, tipo_final)
        self.utils.declare_variable(asignacion.identificador)
        self._store(asignacion.identificador, tipo_final, res.tipo)
        return None

    def visit_imprimir(self, valor):
        # println!(expr): evalua, pasa el tope a printf y llama (sp alineado).
        # en este caso usamos el enlace a printf de libc, asi que se simplifica
        # la impresion a que solo tenemos que reconocer el tipo de dato + su str de formato.
        self.utils.section("println!(...)")
        res = valor.exp.accept(self)  # apila el valor a imprimir
        if res.tipo == "float":
            self.utils.pop_d("d0")  # d0 fijo: 1er arg flotante de printf
            self.utils.emit('    ldr x0, =fmtf // PRINT: x0 = "%f\\n"')
            self.utils.emit("    bl printf // PRINT float (d0)")
        else:
            rx = self.utils.pop_auto_x()
            wx = rx.replace("x", "w")  # %d espera 32 bits
            self.utils.emit('    ldr x0, =fmt // PRINT: x0 = "%d\\n"')
            self.utils.emit(f"    mov w1, {wx} // PRINT: w1 = valor int")
            self.utils.emit("    bl printf // PRINT int (w1)")
        return None

    ####### AUN NO ###################
    def visit_condicional(self, condicional):
        pass

    def visit_bucle(self, valor):
        pass

    def visit_funcion_dcl(self, funcion):
        pass

    def visit_funcion_exec(self, funcion):
        pass

    def visit_struct_dcl(self, struct):
        pass

    def visit_campo_struct(self, struct):
        pass

    def visit_init_struct(self, init_struct):
        pass

    def visit_valor_struct(self, valor):
        pass

    def visit_get_sub_value(self, valor):
        pass
