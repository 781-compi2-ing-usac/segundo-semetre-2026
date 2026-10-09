from .visitante import *
from .expr_compilador import *
from .instr_compilador import *
from .tabla_simbolos import *
from .utils_compilador import *


# Genera ARM64 con modelo de pila: cada expresion deja UN valor de 8 B
# en la pila (int en x / double en d) y cada instruccion lo consume.
# Los registros scratch salen del pool round-robin de Utils (x9-x15,
# d8-d13); solo x0/w1/d0 son fijos porque los exige printf (AAPCS64).
class Compilador(Visitor):
    # Tiling de cada operador a su instruccion ARM64. Es decir una tabla de
    # equivalncias para simplificar la llamada de instrucciones para los diferentes
    # tipos de datos
    _OP_INT = {"+": "add", "-": "sub", "*": "mul"}
    _OP_FLOAT = {"+": "fadd", "-": "fsub", "*": "fmul"}
    # Codigo de condicion ARM para cada comparacion (tras cmp/fcmp).
    _COND = {"==": "eq", "!=": "ne"}

    def __init__(self, utils):
        self.utils = utils
        # Tabla de simbolos del compilador: guarda el tipo de cada variable
        # (nombre -> 'int' | 'float') para elegir ldr/str entero o double.
        # Se almacena como insertar(nombre, tipo, tipo) y se lee con buscar().
        self.tablaSimbolos = TablaSimbolo()
        # Pila de bucles activos: cada entrada es (etiqueta_continue, etiqueta_break).
        # Permite que break/continue anidados salten al while que los contiene.
        self._bucles = []
        # Pila de fines de funcion: return salta al epilogo de la def activa.
        # _funcion_nombres corre en paralelo para el tipo de retorno inferido.
        self._funcion_fin = []
        self._funcion_nombres = []
        # Tipo de retorno inferido por funcion (nombre -> 'int' | 'float').
        # Sin entrada = void (dummy 0). Se llena con inferir_retornos(arbol).
        self._ret_tipo = {}

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

    def _tipo_ret_sintactico(self, nodo):
        # Clasifica el tipo de un valor de retorno sin emitir codigo.
        # Espeja la regla de _pop_as_float/binaria: float si hay hoja float.
        if nodo is None:
            return None
        tipo = getattr(nodo, "tipo", None)
        if tipo in ("int", "float"):
            return tipo  # literal; 'identificador' -> int (tipo aun no inferido)
        if isinstance(nodo, ExpresionBinaria):
            if nodo.operador in ("==", "!="):
                return "int"  # las comparaciones producen 0/1
            l = self._tipo_ret_sintactico(nodo.exp1)
            r = self._tipo_ret_sintactico(nodo.exp2)
            if l == "float" or r == "float":
                return "float"
            return "int"
        if isinstance(nodo, Funcion_exec):
            # return foo(); : hereda lo ya inferido (forward refs -> int).
            return self._ret_tipo.get(nodo.identificador, "int")
        return "int"

    def _ret_en_cuerpo(self, instrucciones):
        # Primer Return con valor dentro de un cuerpo (recurre en if/while).
        for instr in instrucciones:
            if isinstance(instr, Return):
                return instr
            for attr in ("instrucciones",):
                cuerpo = getattr(instr, attr, None)
                if isinstance(cuerpo, list):
                    hallado = self._ret_en_cuerpo(cuerpo)
                    if hallado is not None:
                        return hallado
        return None

    def inferir_retornos(self, arbol):
        # Pre-barrido (opcion B): como los calls se compilan antes que los
        # cuerpos, el tipo de retorno debe conocerse de antemano. Primer
        # return con valor manda; sin el, la funcion es void (dummy 0).
        for rama in arbol:
            if isinstance(rama, Funcion_paramless):
                ret = self._ret_en_cuerpo(rama.instrucciones)
                if ret is not None and ret.value is not None:
                    self._ret_tipo[rama.identificador] = self._tipo_ret_sintactico(ret.value)
        return self._ret_tipo

    def _saltar_si_falso(self, res_tipo, etiqueta_fin):
        # Saca la condicion de la pila y salta a etiqueta_fin si es falsa (0).
        # Int: cbz (0 = falso). Float: fcmp contra 0.0 + b.eq.
        if res_tipo == "float":
            fd = self.utils.pop_auto_d()
            self.utils.emit(f"    fcmp {fd}, #0.0 // IF/WHILE: {fd} == 0.0?")
            self.utils.emit(f"    b.eq {etiqueta_fin} // salta si falso (0.0)")
        else:
            rx = self.utils.pop_auto_x()
            self.utils.emit(f"    cbz {rx}, {etiqueta_fin} // salta si falso (0)")

    def _bloque(self, instrucciones):
        # Compila una lista de instrucciones con un ambito hijo de tipos.
        # Las variables siguen en .data global; el hijo solo aisla el
        # sombreado de tipos y se descarta al cerrar el bloque.
        anterior = self.tablaSimbolos
        self.tablaSimbolos = TablaSimbolo(anterior)
        for instr in instrucciones:
            res = instr.accept(self)
            if isinstance(instr, Expresion):
                self.discard_result(res)
        self.tablaSimbolos = anterior

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
        if binaria.operador in ("==", "!="):
            # Comparacion: produce int 0/1 via (f)cmp + cset (guia 03).
            cond = self._COND[binaria.operador]
            rd = self.utils.assign_register()
            wd = rd.replace("x", "w")  # cset escribe 32 bits (extiende a 64)
            if t1.tipo == "float" or t2.tipo == "float":
                f2 = self._pop_as_float(t2.tipo, "e2")  # tope = e2
                f1 = self._pop_as_float(t1.tipo, "e1")  # tope = e1
                self.utils.emit(
                    f"    fcmp {f1}, {f2} // CMP {binaria.operador} (float)"
                )
                self.utils.emit(
                    f"    cset {wd}, {cond} // {wd} = (e1 {binaria.operador} e2)"
                )
            else:
                r2 = self.utils.pop_auto_x()  # tope = e2
                r1 = self.utils.pop_auto_x()  # tope = e1
                self.utils.emit(f"    cmp {r1}, {r2} // CMP {binaria.operador} (int)")
                self.utils.emit(
                    f"    cset {wd}, {cond} // {wd} = (e1 {binaria.operador} e2)"
                )
            self.utils.push_x(rd)  # el resultado es int 0/1
            return ExpresionValor(None, "int")
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
            self.utils.call("printf")  # PRINT float (d0), sp alineado
        else:
            rx = self.utils.pop_auto_x()
            wx = rx.replace("x", "w")  # %d espera 32 bits
            self.utils.emit('    ldr x0, =fmt // PRINT: x0 = "%d\\n"')
            self.utils.emit(f"    mov w1, {wx} // PRINT: w1 = valor int")
            self.utils.call("printf")  # PRINT int (w1), sp alineado
        return None

    def visit_condicional(self, condicional):
        # if cond { bloque }: evalua, salta al fin si es falso, si no ejecuta.
        self.utils.section("if cond {...}")
        res = condicional.exp.accept(self)  # apila la condicion
        fin = self.utils.new_label("L_if_fin")
        self._saltar_si_falso(res.tipo, fin)  # cbz / fcmp+b.eq
        self._bloque(condicional.instrucciones)  # cuerpo solo si cond != 0
        self.utils.emit_label(fin)  # fin del if

    def visit_bucle(self, valor):
        # while cond { bloque }: inicio -> cond -> cuerpo -> inicio; fin al salir.
        self.utils.section("while cond {...}")
        inicio = self.utils.new_label("L_while")
        fin = self.utils.new_label("L_while_fin")
        self.utils.emit_label(inicio)  # continue salta aqui (re-evalua)
        res = valor.exp.accept(self)  # apila la condicion
        self._saltar_si_falso(res.tipo, fin)  # cond falsa -> salir
        self._bucles.append((inicio, fin))  # marco para break/continue
        self._bloque(valor.instrucciones)  # cuerpo del bucle
        self._bucles.pop()  # cierra el marco del bucle actual
        self.utils.emit(f"    b {inicio} // WHILE: repetir")
        self.utils.emit_label(fin)  # break salta aqui

    def visit_break(self, valor):
        # break: sale del while mas interno. Fuera de bucle se ignora.
        if not self._bucles:
            self.utils.emit("    // BREAK fuera de bucle (ignorado)")
            return None
        _, fin = self._bucles[-1]
        self.utils.emit(f"    b {fin} // BREAK -> fin del while")
        return None

    def visit_continue(self, valor):
        # continue: re-evalua la condicion del while mas interno.
        if not self._bucles:
            self.utils.emit("    // CONTINUE fuera de bucle (ignorado)")
            return None
        inicio, _ = self._bucles[-1]
        self.utils.emit(f"    b {inicio} // CONTINUE -> re-evaluar while")
        return None

    def visit_funcion_dcl(self, funcion):
        # def id() { bloque }: subrutina tras el ret de main (opcion B).
        # parse() emite las declaraciones en segunda pasada, asi el cuerpo
        # solo es alcanzable via bl. Sin branch-over ni reorden interno.
        self.utils.section(f"def {funcion.identificador}()")
        self.tablaSimbolos.insertar(funcion.identificador, "funcion", "funcion")
        self.utils.emit_label(f"_fn_{funcion.identificador}")
        self.utils.emit("    stp x29, x30, [sp, #-16]! // FN: push {fp, lr}")
        self.utils.emit("    mov x29, sp // FN: nuevo frame pointer")
        fin = self.utils.new_label("L_fn_fin")
        self._funcion_fin.append(fin)  # return salta aqui (soporta def anidado)
        self._funcion_nombres.append(funcion.identificador)  # tipo en _ret_tipo
        self._bloque(funcion.instrucciones)  # cuerpo con ambito hijo
        self._funcion_fin.pop()  # cierra el marco de la funcion actual
        self._funcion_nombres.pop()  # idem para el nombre
        self.utils.emit_label(fin)  # cae aqui al terminar o por return
        self.utils.emit("    ldp x29, x30, [sp], #16 // FN: pop {fp, lr}")
        self.utils.emit("    ret // FN: vuelta al bl")
        return None

    def visit_funcion_exec(self, funcion):
        # id(): bl alineado + apila el retorno (x0 int / d0 float) o dummy 0
        # si es void. Asi foo(); (la limpia discard_result) y let x = foo();
        # balancean la pila en los tres casos.
        self.utils.section(f"call {funcion.identificador}()")
        self.utils.call(f"_fn_{funcion.identificador}")
        if self._ret_tipo.get(funcion.identificador) == "float":
            self.utils.push_d("d0")  # retorno float (d0 AAPCS64) -> pila
            return ExpresionValor(None, "float")
        if funcion.identificador in self._ret_tipo:
            rx = self.utils.assign_register()
            self.utils.emit(f"    mov {rx}, x0 // CALL: retorno int (x0) -> pila")
            self.utils.push_x(rx)
            return ExpresionValor(None, "int")
        self._push_int(0)  # void -> dummy 0 int
        return ExpresionValor(None, "int")

    def visit_return(self, retorno):
        # return [expr]; : deja el valor en x0/d0 (AAPCS64) y salta al fin.
        # Fuera de funcion se evalua+descarta (pila balanceada) y se ignora,
        # igual que break/continue fuera de bucle.
        self.utils.section("return ...")
        if not self._funcion_fin:
            if retorno.value is not None:
                res = retorno.value.accept(self)  # apila (solo por balance)
                self.discard_result(res)  # ... y lo descarta enseguida
            self.utils.emit("    // RETURN fuera de funcion (ignorado)")
            return None
        if retorno.value is None:
            # return; sin valor -> cero del tipo inferido (void -> x0 = 0).
            if self._ret_tipo.get(self._funcion_actual()) == "float":
                self.utils.emit("    mov x0, #0 // RETURN: cero int")
                self.utils.emit("    scvtf d0, x0 // RETURN: cero -> double")
            else:
                self.utils.emit("    mov x0, #0 // RETURN: cero int")
        elif self._ret_tipo.get(self._funcion_actual()) == "float":
            res = retorno.value.accept(self)  # apila el valor
            fd = self._pop_as_float(res.tipo, "return")  # a double
            self.utils.emit(f"    fmov d0, {fd} // RETURN: d0 = valor float")
        else:
            res = retorno.value.accept(self)  # apila el valor
            if res.tipo == "float":
                fd = self.utils.pop_auto_d()
                rx = self.utils.assign_register()
                self.utils.emit(f"    fcvtzs {rx}, {fd} // RETURN: double -> int")
            else:
                rx = self.utils.pop_auto_x()
            self.utils.emit(f"    mov x0, {rx} // RETURN: x0 = valor int")
        self.utils.emit(f"    b {self._funcion_fin[-1]} // RETURN -> fin")
        return None

    def _funcion_actual(self):
        # Nombre de la def en compilacion (None si no hay).
        if not self._funcion_nombres:
            return None
        return self._funcion_nombres[-1]

    ####### AUN NO ###################

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
