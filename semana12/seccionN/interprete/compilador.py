from .visitante import *
from .expr_compilador import *
from .instr_compilador import *
from .tabla_simbolos import *
from .utils_compilador import *
from .contexto import *


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
        # Contexto de control del generador: una sola pila de marcos
        # (bucle o funcion) con las etiquetas ASM. El tipo de retorno inferido
        # vive como atributo del simbolo funcion en la tabla (retorno_de).
        self.control = ContextoControl()
        # Layouts de frames fp por funcion (disponer_frames): fn -> {'usado',
        # 'p', 'scopes': {sid: {'mark': off|None, 'slots': {nombre: (elem,
        # dims, off)}}}}. mark None = nivel cuerpo-fn/raiz (usa el save del
        # prologo, convencion off 8). Los slots mueren con su ambito.
        self._layout = {}
        self._scope_padre = {}
        self._scope_fn = {}
        self._ambito_seq = 0
        self._fn_actual = "main"
        self._pila_ambitos = []
        self._base_amb = 0
        self.hay_arrays = False

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
        if tipo == "array":
            self.utils.emit(f"    // IDX ERROR: {name} es array, usa {name}[i]")
            self._push_int(0)
            return "int"
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

    def _pop_como(self, res_tipo, elem, motivo):
        # Baja el tope de la pila como elem ('int'|'float'), convirtiendo si difiere.
        if elem == "float":
            return self._pop_as_float(res_tipo, motivo)
        if res_tipo == "float":
            fd = self.utils.pop_auto_d()
            rx = self.utils.assign_register()
            self.utils.emit(f"    fcvtzs {rx}, {fd} // CONV {motivo}: double -> int")
            return rx
        return self.utils.pop_auto_x()

    def _store(self, name, tipo_final, res_tipo):
        # Baja el tope de la pila a memoria, convirtiendo si int<->float difieren.
        addr = self._addr(name, f"guardar {name}")
        if tipo_final == "float":
            fd = self._pop_como(res_tipo, "float", "guardar")
            self.utils.emit(f"    str {fd}, [{addr}] // LET {name} = {fd} (double)")
        else:
            rx = self._pop_como(res_tipo, "int", "guardar")
            self.utils.emit(f"    str {rx}, [{addr}] // LET {name} = {rx} (int)")

    def _aplana_indices(self, base):
        # Desanida ExpresionIndice: devuelve (raiz, [indices en orden fuente]).
        indices = []
        while isinstance(base, ExpresionIndice):
            indices.append(base.indice)
            base = base.base
        indices.reverse()
        return base, indices

    def _push_indice(self, nodo):
        # Evalua un indice y lo deja en la pila como int (convierte si es float).
        res = nodo.accept(self)
        if res.tipo == "float":
            fd = self.utils.pop_auto_d()
            rx = self.utils.assign_register()
            self.utils.emit(f"    fcvtzs {rx}, {fd} // IDX: double -> int")
            self.utils.push_x(rx)

    def _addr_idx(self, name, dims, n, off):
        # Los n indices ya estan apilados en orden fuente (tope = i_{n-1}).
        # Row-major por strides estaticos: lineal = i0*s0 + ... + in-1*s{n-1}
        # con s_k = prod(dims tras k). Se baja del tope (k = n-1..0) y se
        # acumula; el conjunto vivo nunca pasa de 5 registros, asi el pool
        # round-robin de 6 jamas pisa un valor vivo (vale para cualquier n).
        # Escala *8 y suma la base; devuelve la direccion final.
        strides = []
        s = 1
        for d in reversed(dims):
            strides.append(s)
            s *= d
        strides.reverse()
        rLin = None
        for k in range(n - 1, -1, -1):
            rI = self.utils.pop_auto_x()  # i_k, el tope
            if strides[k] == 1:
                rTerm = rI  # ultimo eje: stride 1, sin mul
            else:
                rS = self.utils.assign_register()
                self.utils.emit(f"    mov {rS}, #{strides[k]} // IDX: stride[{k}]={strides[k]}")
                rTerm = self.utils.assign_register()
                self.utils.emit(f"    mul {rTerm}, {rI}, {rS} // IDX: i{k}*stride")
            if rLin is None:
                rLin = rTerm
            else:
                rN = self.utils.assign_register()
                self.utils.emit(f"    add {rN}, {rLin}, {rTerm} // IDX: acum + i{k}*s")
                rLin = rN
        self.utils.emit(f"    lsl {rLin}, {rLin}, #3 // IDX: lineal * 8")
        xH = self.utils.assign_register()
        self.utils.emit(f"    ldr {xH}, [x29, #{-off}] // IDX: base heap ({name})")
        self.utils.emit(f"    add {xH}, {xH}, {rLin} // IDX: &{name}[...]")
        return xH

    def _array_info(self, nombre, heuristico=False):
        # (elem, dims, off-fp) en la cadena lexica de la funcion activa.
        # heuristico (solo inferencia sin ambitos) rastrea todos los layouts.
        lay = self._layout.get(self._fn_actual, {})
        scopes = lay.get("scopes", {})
        for sid in reversed(self._pila_ambitos[self._base_amb:]):
            if self._scope_fn.get(sid) != self._fn_actual:
                continue
            slots = scopes.get(sid, {}).get("slots", {})
            if nombre in slots:
                return slots[nombre]
        if heuristico:
            for _, l2 in self._layout.items():
                for sc in l2.get("scopes", {}).values():
                    if nombre in sc.get("slots", {}):
                        return sc["slots"][nombre]
        return None

    def _info_idx(self, base, n_indices):
        # Resuelve (nombre, elem, dims, off) o None si base/aridad es invalida.
        if not (isinstance(base, ExpresionValor) and base.tipo == "identificador"):
            return None
        info = self._array_info(base.val)
        if info is None or len(info[1]) != n_indices:
            return None
        return base.val, info[0], info[1], info[2]

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
            rt = self.tablaSimbolos.retorno_de(nodo.identificador)
            return rt if rt in ("int", "float") else "int"
        if isinstance(nodo, ExpresionIndice):
            # return a[i]; : tipo del elemento (desconocido -> int).
            base, _ = self._aplana_indices(nodo)
            if isinstance(base, ExpresionValor) and base.tipo == "identificador":
                info = self._array_info(base.val, heuristico=True)
                if info is not None:
                    return info[0]
            return "int"
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
        inferidos = {}
        for rama in arbol:
            if isinstance(rama, Funcion_paramless):
                ret = self._ret_en_cuerpo(rama.instrucciones)
                if ret is not None and ret.value is not None:
                    tipo = self._tipo_ret_sintactico(ret.value)
                    self.tablaSimbolos.declarar_retorno(rama.identificador, tipo)
                    inferidos[rama.identificador] = tipo
        return inferidos

    def _nuevo_ambito(self, fn, padre):
        # Crea un nivel de ambito con su id y lo registra bajo su funcion.
        self._ambito_seq += 1
        sid = self._ambito_seq
        self._scope_padre[sid] = padre
        self._scope_fn[sid] = fn
        self._layout[fn]["scopes"][sid] = {"mark": None, "slots": {}}
        return sid

    def _off_nuevo(self, fn):
        # Reserva 8 B en el frame (off 8 = mark del prologo, intocable).
        lay = self._layout[fn]
        lay["usado"] += 8
        return lay["usado"]

    def _mide_bloque(self, fn, instrucciones, sid):
        # Pre-barrido: cuenta DeclArray directos y crea niveles if/while/def.
        for instr in instrucciones:
            if isinstance(instr, DeclArray):
                if instr.tipo in ("float", "FLOAT"):
                    elem = "float"
                else:
                    elem = "int"
                off = self._off_nuevo(fn)
                self._layout[fn]["scopes"][sid]["slots"][instr.identificador] = (elem, list(instr.dims), off)
                self.hay_arrays = True
            elif isinstance(instr, (Condicional, Bucle)):
                nsid = self._nuevo_ambito(fn, sid)
                instr._ambito = nsid
                moff = self._off_nuevo(fn)
                self._layout[fn]["scopes"][nsid]["mark"] = moff
                self._mide_bloque(fn, instr.instrucciones, nsid)
            elif isinstance(instr, Funcion_paramless):
                self._layout[instr.identificador] = {"usado": 8, "scopes": {}}
                nsid = self._nuevo_ambito(instr.identificador, None)
                instr._ambito = nsid
                self._mide_bloque(instr.identificador, instr.instrucciones, nsid)

    def disponer_frames(self, arbol):
        # Pre-barrido (con inferir_retornos): frames fp por funcion (main
        # incluido). La raiz de main es siempre sid 0. Devuelve fn -> P.
        self._layout = {"main": {"usado": 8, "scopes": {}}}
        self._scope_padre = {0: None}
        self._scope_fn = {0: "main"}
        self._layout["main"]["scopes"][0] = {"mark": None, "slots": {}}
        self._ambito_seq = 0
        self.hay_arrays = False
        resto = [r for r in arbol if not isinstance(r, Funcion_paramless)]
        self._mide_bloque("main", resto, 0)
        for rama in arbol:
            if isinstance(rama, Funcion_paramless):
                self._layout[rama.identificador] = {"usado": 8, "scopes": {}}
                nsid = self._nuevo_ambito(rama.identificador, None)
                rama._ambito = nsid
                self._mide_bloque(rama.identificador, rama.instrucciones, nsid)
        frames = {}
        for fn, lay in self._layout.items():
            p = lay["usado"]
            if p % 16:
                p += 16 - (p % 16)
            lay["p"] = p
            frames[fn] = p
        return frames

    def bloque_raiz(self, instrucciones):
        # Nivel raiz de main (sid 0): sin hijo de tipos, con entry/exit.
        return self._bloque(instrucciones, 0, con_ambito=False)

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

    def _bloque(self, instrucciones, sid=None, con_ambito=True):
        # Compila con ambito hijo de tipos + entry/exit del nivel (mark del
        # heap y zero de slots). sid None (sin disponer previo) = solo tipos.
        if con_ambito:
            self.tablaSimbolos = self.tablaSimbolos.entrar()
        marco = None
        if sid is not None:
            lay = self._layout.get(self._fn_actual, {})
            marco = lay.get("scopes", {}).get(sid)
        if marco is not None:
            self._pila_ambitos.append(sid)
            if marco["mark"] is not None:
                self.utils.emit(f"    str x20, [x29, #{-marco['mark']}] // AMBITO: guarda mark")
            for nombre, (_, _, off) in marco["slots"].items():
                self.utils.emit(f"    str xzr, [x29, #{-off}] // AMBITO: slot {nombre} = 0")
        for instr in instrucciones:
            res = instr.accept(self)
            if isinstance(instr, Expresion):
                self.discard_result(res)
        if marco is not None:
            self._pila_ambitos.pop()
            if marco["mark"] is not None:
                self.utils.emit(f"    ldr x20, [x29, #{-marco['mark']}] // AMBITO: restaura mark")
        if con_ambito:
            self.tablaSimbolos = self.tablaSimbolos.salir()

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

    def _aplana_init(self, init):
        # Aplana literales anidados en orden row-major: [[1,2],[3,4]] -> [1,2,3,4].
        planos = []

        def rec(x):
            if isinstance(x, list):
                for e in x:
                    rec(e)
            else:
                planos.append(x)

        rec(init)
        return planos

    def visit_decl_array(self, decl):
        # let id : [[elem; d1]; d0] = [[...], [...]] con lifetime del ambito:
        # guard cbnz + carve bump, base recargada del slot-frame por elemento.
        # Literal corto -> zero-fill; largo -> se trunca (comentario ERROR).
        if decl.tipo in ("float", "FLOAT"):
            elem = "float"
        else:
            elem = "int"
        dims = decl.dims
        info = self._array_info(decl.identificador)
        self.utils.section(f"array {decl.identificador}{dims} = ...")
        if info is None:
            self.utils.emit("    // ARRAY ERROR: sin layout (falta disponer_frames)")
            return None
        off = info[2]
        slot = -off
        planos = self._aplana_init(decl.init)
        total = 1
        for d in dims:
            total *= d
        if len(planos) != total:
            self.utils.emit(f"    // ARRAY ERROR: {len(planos)} valores para {total} slots (fill 0 / trunc)")
        self.tablaSimbolos.insertar(decl.identificador, "array", "array")
        self.utils.heap_guard(off, total * 8)
        for k in range(total):
            if k < len(planos):
                res_tipo = planos[k].accept(self).tipo  # apila el elemento k
            elif elem == "float":
                self._push_float_const(0.0)  # zero-fill double
                res_tipo = "float"
            else:
                self._push_int(0)  # zero-fill int
                res_tipo = "int"
            xB = self.utils.assign_register()
            self.utils.emit(f"    ldr {xB}, [x29, #{slot}] // ARRAY: base heap")
            rv = self._pop_como(res_tipo, elem, f"array[{k}]")
            if elem == "float":
                self.utils.emit(f"    str {rv}, [{xB}, #{k * 8}] // ARRAY [{k}] (double)")
            else:
                self.utils.emit(f"    str {rv}, [{xB}, #{k * 8}] // ARRAY [{k}] (int)")
        return None

    def visit_expresion_indice(self, acceso):
        # a[i][j] como rvalue: evalua indices, Horner row-major, ldr + push.
        base, indices = self._aplana_indices(acceso)
        resuelto = self._info_idx(base, len(indices))
        if resuelto is None:
            self.utils.section("idx (invalido)")
            self.utils.emit("    // IDX ERROR: base o aridad invalida, dummy 0")
            self._push_int(0)
            return ExpresionValor(None, "int")
        name, elem, dims, off = resuelto
        self.utils.section(f"idx {name}[...]")
        for ix in indices:
            self._push_indice(ix)
        addr = self._addr_idx(name, dims, len(indices), off)
        if elem == "float":
            dst = self.utils.assign_freg()
            self.utils.emit(f"    ldr {dst}, [{addr}] // IDX {name}[...] (double) -> pila")
            self.utils.push_d(dst)
        else:
            dst = self.utils.assign_register()
            self.utils.emit(f"    ldr {dst}, [{addr}] // IDX {name}[...] (int) -> pila")
            self.utils.push_x(dst)
        return ExpresionValor(None, elem)

    def visit_store_indice(self, store):
        # a[i][j] = v: evalua el valor PRIMERO (queda al fondo de la pila, a
        # salvo en memoria) y luego los indices; Horner, baja el valor y str.
        base, indices = self._aplana_indices(store.base)
        indices.append(store.indice)
        resuelto = self._info_idx(base, len(indices))
        if resuelto is None:
            self.utils.section("idx store (invalido)")
            self.utils.emit("    // IDX ERROR: base o aridad invalida (ignorado)")
            return None
        name, elem, dims, off = resuelto
        self.utils.section(f"idx {name}[...] = ...")
        res = store.valor.accept(self)  # apila el valor (fondo)
        for ix in indices:
            self._push_indice(ix)
        addr = self._addr_idx(name, dims, len(indices), off)
        rv = self._pop_como(res.tipo, elem, "array-store")
        if elem == "float":
            self.utils.emit(f"    str {rv}, [{addr}] // IDX {name}[...] = {rv} (double)")
        else:
            self.utils.emit(f"    str {rv}, [{addr}] // IDX {name}[...] = {rv} (int)")
        return None

    def _emit_print(self, tipo, etiqueta):
        # Baja el tope de la pila a printf con el formato dado (d0 / w1 fijos).
        if tipo == "float":
            self.utils.pop_d("d0")  # d0 fijo: 1er arg flotante de printf
            self.utils.emit(f"    ldr x0, ={etiqueta} // PRINT: formato")
            self.utils.call("printf")  # PRINT float (d0), sp alineado
        else:
            rx = self.utils.pop_auto_x()
            wx = rx.replace("x", "w")  # %d espera 32 bits
            self.utils.emit(f"    ldr x0, ={etiqueta} // PRINT: formato")
            self.utils.emit(f"    mov w1, {wx} // PRINT: w1 = valor int")
            self.utils.call("printf")  # PRINT int (w1), sp alineado

    def _print_array(self, nombre, info):
        # println!(matriz): elementos separados por espacio, fila por linea.
        # Desenrollado (N estatica): base + k*8 en orden row-major == memoria.
        elem, dims, off = info
        slot = -off
        total = 1
        for d in dims:
            total *= d
        fila = dims[-1]
        fmt = "fmtfsp" if elem == "float" else "fmtsp"
        for k in range(total):
            xB = self.utils.assign_register()
            self.utils.emit(f"    ldr {xB}, [x29, #{slot}] // PRINT-ARR: base heap ({nombre})")
            if elem == "float":
                fd = self.utils.assign_freg()
                self.utils.emit(f"    ldr {fd}, [{xB}, #{k * 8}] // PRINT-ARR [{k}] (double)")
                self.utils.push_d(fd)
            else:
                rd = self.utils.assign_register()
                self.utils.emit(f"    ldr {rd}, [{xB}, #{k * 8}] // PRINT-ARR [{k}] (int)")
                self.utils.push_x(rd)
            self._emit_print(elem, fmt)
            if (k + 1) % fila == 0:
                self.utils.emit("    ldr x0, =fmtnl // PRINT-ARR: fin de fila")
                self.utils.call("printf")

    def visit_imprimir(self, valor):
        # println!(expr): evalua, pasa el tope a printf y llama (sp alineado).
        # en este caso usamos el enlace a printf de libc, asi que se simplifica
        # la impresion a que solo tenemos que reconocer el tipo de dato + su str de formato.
        # println!(matriz) con el id pelado imprime filas (ver _print_array).
        self.utils.section("println!(...)")
        exp = valor.exp
        if isinstance(exp, ExpresionValor) and exp.tipo == "identificador":
            info = self._array_info(exp.val)
            if info is not None:
                self._print_array(exp.val, info)
                return None
        res = exp.accept(self)  # apila el valor a imprimir
        self._emit_print(res.tipo, "fmtf" if res.tipo == "float" else "fmt")
        return None

    def visit_condicional(self, condicional):
        # if cond { bloque }: evalua, salta al fin si es falso, si no ejecuta.
        self.utils.section("if cond {...}")
        res = condicional.exp.accept(self)  # apila la condicion
        fin = self.utils.new_label("L_if_fin")
        self._saltar_si_falso(res.tipo, fin)  # cbz / fcmp+b.eq
        self._bloque(condicional.instrucciones, getattr(condicional, "_ambito", None))
        self.utils.emit_label(fin)  # fin del if

    def visit_bucle(self, valor):
        # while cond { bloque }: inicio -> cond -> cuerpo -> inicio; fin al salir.
        self.utils.section("while cond {...}")
        inicio = self.utils.new_label("L_while")
        fin = self.utils.new_label("L_while_fin")
        self.utils.emit_label(inicio)  # continue salta aqui (re-evalua)
        res = valor.exp.accept(self)  # apila la condicion
        self._saltar_si_falso(res.tipo, fin)  # cond falsa -> salir
        self.control.entrar_bucle(inicio, fin)  # marco para break/continue
        self._bloque(valor.instrucciones, getattr(valor, "_ambito", None))
        self.control.salir_bucle()  # cierra el marco del bucle actual
        self.utils.emit(f"    b {inicio} // WHILE: repetir")
        self.utils.emit_label(fin)  # break salta aqui

    def visit_break(self, valor):
        # break: sale del while mas interno. Fuera de bucle se ignora.
        marco = self.control.bucle_actual()
        if marco is None:
            self.utils.emit("    // BREAK fuera de bucle (ignorado)")
            return None
        _, fin = marco
        self.utils.emit(f"    b {fin} // BREAK -> fin del while")
        return None

    def visit_continue(self, valor):
        # continue: re-evalua la condicion del while mas interno.
        marco = self.control.bucle_actual()
        if marco is None:
            self.utils.emit("    // CONTINUE fuera de bucle (ignorado)")
            return None
        inicio, _ = marco
        self.utils.emit(f"    b {inicio} // CONTINUE -> re-evaluar while")
        return None

    def visit_funcion_dcl(self, funcion):
        # def id() { bloque }: subrutina tras el ret de main (opcion B).
        # parse() emite las declaraciones en segunda pasada, asi el cuerpo
        # solo es alcanzable via bl. Sin branch-over ni reorden interno.
        self.utils.section(f"def {funcion.identificador}()")
        if self.tablaSimbolos.buscar(funcion.identificador) is None:
            self.tablaSimbolos.insertar(funcion.identificador, "funcion", "funcion")
        fn_prev, base_prev = self._fn_actual, self._base_amb
        self._fn_actual = funcion.identificador
        self._base_amb = len(self._pila_ambitos)
        self.utils.emit_label(f"_fn_{funcion.identificador}")
        self.utils.emit("    stp x29, x30, [sp, #-16]! // FN: push {fp, lr}")
        self.utils.emit("    mov x29, sp // FN: nuevo frame pointer")
        p = self._layout.get(funcion.identificador, {}).get("p", 0)
        if p:
            self.utils.emit(f"    sub sp, sp, #{p} // FN: frame {p} B")
        self.utils.emit("    str x20, [x29, #-8] // FN: guarda mark (off 8)")
        fin = self.utils.new_label("L_fn_fin")
        self.control.entrar_funcion(fin, funcion.identificador)
        self._bloque(funcion.instrucciones, getattr(funcion, "_ambito", None))
        self.control.salir_funcion()  # cierra el marco de la funcion actual
        self.utils.emit_label(fin)  # cae aqui al terminar o por return
        self.utils.emit("    ldr x20, [x29, #-8] // FN: restaura mark")
        if p:
            self.utils.emit(f"    add sp, sp, #{p} // FN: libera frame")
        self.utils.emit("    ldp x29, x30, [sp], #16 // FN: pop {fp, lr}")
        self.utils.emit("    ret // FN: vuelta al bl")
        self._fn_actual, self._base_amb = fn_prev, base_prev
        return None

    def visit_funcion_exec(self, funcion):
        # id(): bl alineado + apila el retorno (x0 int / d0 float) o dummy 0
        # si es void. Asi foo(); (la limpia discard_result) y let x = foo();
        # balancean la pila en los tres casos.
        self.utils.section(f"call {funcion.identificador}()")
        self.utils.call(f"_fn_{funcion.identificador}")
        rt = self.tablaSimbolos.retorno_de(funcion.identificador)
        if rt == "float":
            self.utils.push_d("d0")  # retorno float (d0 AAPCS64) -> pila
            return ExpresionValor(None, "float")
        if rt == "int":
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
        marco = self.control.funcion_actual()
        if marco is None:
            if retorno.value is not None:
                res = retorno.value.accept(self)  # apila (solo por balance)
                self.discard_result(res)  # ... y lo descarta enseguida
            self.utils.emit("    // RETURN fuera de funcion (ignorado)")
            return None
        rt = self.tablaSimbolos.retorno_de(marco["nombre"])
        if retorno.value is None:
            # return; sin valor -> cero del tipo inferido (void -> x0 = 0).
            if rt == "float":
                self.utils.emit("    mov x0, #0 // RETURN: cero int")
                self.utils.emit("    scvtf d0, x0 // RETURN: cero -> double")
            else:
                self.utils.emit("    mov x0, #0 // RETURN: cero int")
        elif rt == "float":
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
        self.utils.emit(f"    b {marco['fin']} // RETURN -> fin")
        return None

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
