"""
MiniPascal v6 — El GENERADOR de ensamblador ARM64.

Este archivo es el segundo visitante. Recorre EXACTAMENTE el mismo árbol
que `interprete.py` y no comparte con él ni una línea de código. Ese es
todo el argumento del patrón Visitor, hecho archivo.

Comparen los dos visitantes en el mismo nodo:

    interprete.py                      generador_arm.py
    -------------                      ----------------
    def visitar_Literal(self, nodo):   def visitar_Literal(self, nodo):
        return nodo.valor                  self.emitir(f'mov x0, #{nodo.valor}')

El intérprete DEVUELVE un 14. El generador no devuelve nada: escribe una
línea de texto que, cuando el procesador la ejecute, va a dejar un 14 en
el registro x0. El primero calcula ahora; el segundo describe un cálculo
para después. Esa diferencia es el Proyecto 2 entero.


ALCANCE DE HOY — léanlo, es corto a propósito
---------------------------------------------
Todo lo de la Sesión 1, más:

    * literales enteros
    * + - * / y el menos unario
    * writeln(<expresión entera>)
    * bloques y el programa
    * NUEVO: declarar variables enteras (`var nombre: integer [:= expr];`)
    * NUEVO: leer una variable dentro de una expresión
    * NUEVO: reasignar una variable ya declarada (`nombre := expr;`)

Cualquier otro nodo produce un mensaje claro diciendo qué falta (lo hace
la clase base, en `visitante.py`). Esa lista de mensajes es su hoja de
ruta: control de flujo, funciones, memoria. Vayan tachándola.

Lo que NO entra hoy, a propósito: `const` se trata exactamente como `var`
en el generador (reservar y sobrescribir es lo mismo en ARM64 — que no se
pueda REASIGNAR una constante es una regla del análisis semántico, no del
código que se genera). Tampoco entra `real`, `boolean` ni `string`: eso
sigue siendo trabajo de `visitar_Literal`, que ya se queja si no es un
entero. Y los `begin...end` anidados no abren ni cierran su propio tramo
de offsets todavía — todas las variables del programa comparten un mismo
`EntornoDeCompilacion` de principio a fin. Ver "Qué falta para tu
proyecto" en el README.

No es que el generador esté "incompleto". Es que un compilador se
construye así, un nodo a la vez, y cada nodo nuevo se prueba corriéndolo
de verdad antes de pasar al siguiente. Háganlo en ese orden y el
Proyecto 2 es llevadero; háganlo al revés y no.


EL MODELO: una máquina de pila
------------------------------
La regla, una sola, y vale para toda expresión:

    **toda expresión deja su resultado en x0.**

Con eso, una operación binaria se arma sola:

    1. generar el operando izquierdo      -> queda en x0
    2. empujar x0 a la pila               -> porque el paso 3 lo va a pisar
    3. generar el operando derecho        -> queda en x0
    4. mover x0 a x1                      -> el derecho se corre a x1
    5. sacar de la pila a x0              -> vuelve el izquierdo
    6. add x0, x0, x1                     -> resultado en x0, se cumple la regla

El paso 2 es el que suele costar entender. Va porque generar el operando
derecho puede ser una expresión enorme, con sus propias operaciones, que
va a usar x0 mil veces. Si el izquierdo se hubiera quedado ahí, se
perdería. La pila es lo único que sobrevive a eso.

¿Es eficiente? No. Un compilador de verdad haría ASIGNACIÓN DE REGISTROS
y usaría x0-x7 en vez de tocar memoria a cada paso. Pero la asignación de
registros es un algoritmo de coloreo de grafos, y no cabe en este curso.
El modelo de pila tiene una propiedad que sí nos importa: funciona para
expresiones de CUALQUIER tamaño y anidamiento sin cambiar nada. Empiecen
por aquí. Optimizar después es opcional; funcionar no lo es.
"""

from visitante import Visitante


# La pila de AArch64 tiene que estar alineada a 16 bytes SIEMPRE. Por eso
# empujamos de 16 en 16 aunque un entero ocupe 8: gastar 8 bytes es más
# barato que depurar el fallo de alineación, que se manifiesta como un
# crash sin explicación dentro de printf.
EMPUJAR = 'str x0, [sp, #-16]!'
SACAR   = 'ldr x0, [sp], #16'

OPERADORES = {
    '+': 'add',
    '-': 'sub',
    '*': 'mul',
    '/': 'sdiv',    # signed divide: división ENTERA, ver la nota de abajo
}

# Operador de MiniPascal -> condición de ARM64 para `cset` / `b.<cond>`.
# `cmp a, b` no devuelve nada: deja el resultado en cuatro banderas (NZCV),
# y cada condición es una forma de leerlas. eq = equal, ne = not equal,
# lt = less than, gt = greater than, le = less or equal, ge = greater or equal.
COMPARADORES = {
    '==': 'eq',
    '!=': 'ne',
    '<':  'lt',
    '>':  'gt',
    '<=': 'le',
    '>=': 'ge',
}


# ---------------------------------------------------------------------------
# El HEAP: la memoria que se le pide al kernel mientras el programa corre.
#
# Estas dos piezas se escriben UNA sola vez por programa, y solo si el
# programa usa un arreglo. Son exactamente las de arm/05_alloc_tabla.s:
# léanlas allá primero, con comentarios, antes de leerlas aquí.
# ---------------------------------------------------------------------------

# Cuántas filas cabe en la tabla de bloques. Cada fila son 16 bytes
# (base y tamaño). Nada revisa que no se pase de aquí: LO QUE FALTA.
FILAS_DE_LA_TABLA = 64

SECCION_BSS = f'''// --- Heap: la tabla de bloques reservados ---
// Una fila por cada bloque que `alloc` entregó: [base][tamaño].
.section .bss
.balign 8
tabla_heap:
    .skip {FILAS_DE_LA_TABLA * 16}
tabla_n:
    .skip 8
'''

RUTINA_ALLOC = '''
// ----------------------------------------------------------
// alloc: reservar x0 bytes en el heap con brk y anotarlos
// en la tabla.   entrada: x0 = bytes   salida: x0 = dirección
// Pisa x1-x13 y x8; es una rutina hoja (no llama a nadie).
// ----------------------------------------------------------
alloc:
    mov x9, x0                   // x9 = n
    mov x0, #0
    mov x8, #214                 // 214 = brk
    svc #0                       // x0 = break actual = base del bloque
    mov x10, x0                  // x10 = base
    add x0, x10, x9
    mov x8, #214
    svc #0                       // brk(base + n): el heap creció n bytes
    adrp x11, tabla_n
    add  x11, x11, :lo12:tabla_n
    ldr  x12, [x11]              // x12 = índice de la fila nueva
    adrp x13, tabla_heap
    add  x13, x13, :lo12:tabla_heap
    add  x13, x13, x12, lsl #4   // x13 = tabla_heap + índice * 16
    str  x10, [x13]              // fila.base   = base
    str  x9,  [x13, #8]          // fila.tamaño = n
    add  x12, x12, #1
    str  x12, [x11]              // tabla_n += 1
    mov  x0, x10                 // resultado: la base del bloque
    ret
'''


class GeneradorARM64(Visitante):
    """Recorre el AST y ESCRIBE ensamblador ARM64."""

    etiqueta = 'generador'

    def __init__(self):
        self.lineas = []       # el ensamblador que llevamos escrito

        # El ENTORNO DE COMPILACIÓN de hoy: nombre -> offset desde x29.
        # Contrástenlo con `self.entorno` de interprete.py, que es
        # nombre -> valor. Uno describe dónde va a vivir cada variable en
        # el stack frame; el otro, cuánto vale ahora mismo. Ver
        # micro/03_entorno_compilacion.py, que pone los dos lado a lado
        # sobre el mismo programa.
        self.offsets = {}
        self.proximo_offset = 0   # cuántos bytes del frame llevamos reservados

        # ¿El programa pidió memoria al heap? Si no, el .s no necesita ni la
        # tabla ni la rutina `alloc`, y no las escribimos.
        self.usa_heap = False

        # Etiquetas: cada `if` y cada `while` necesita saltar a lugares que
        # tienen nombre, y dos `if` distintos NO pueden compartir nombre. Un
        # contador que solo sube basta para que nunca se repitan.
        self.contador_etiquetas = 0

        # Los ciclos que estamos recorriendo ahora mismo, el más interno al
        # final. Un `break` o `continue` consulta aquí a dónde saltar.
        self.ciclos = []

    # -- etiquetas ----------------------------------------------------------

    def nueva_etiqueta(self, prefijo):
        """Un nombre que no se ha usado antes: `.Lwhile_fin_3`.

        El `.L` inicial le dice al ensamblador que es una etiqueta LOCAL: se
        usa para saltar, pero no aparece en la tabla de símbolos del binario.
        """
        self.contador_etiquetas += 1
        return f'.L{prefijo}_{self.contador_etiquetas}'

    def poner_etiqueta(self, etiqueta):
        """Escribir `etiqueta:` en este punto del código."""
        self.lineas.append(f'{etiqueta}:')

    # -- escribir texto -----------------------------------------------------

    def emitir(self, instruccion, comentario=None):
        """Agrega una instrucción, indentada, con comentario opcional.

        Los comentarios NO son decoración: la sección 3.4.1 del enunciado
        los pide explícitamente en el código generado. Y cuando algo salga
        mal —y va a salir mal— leer un ensamblador comentado contra uno
        pelado es la diferencia entre media hora y una tarde.
        """
        if comentario:
            self.lineas.append(f'    {instruccion:<28} // {comentario}')
        else:
            self.lineas.append(f'    {instruccion}')

    def comentario(self, texto):
        self.lineas.append(f'    // {texto}')

    # -- EXPRESIONES: cada una deja su resultado en x0 ----------------------

    def visitar_Literal(self, nodo):
        # `isinstance(True, int)` es True en Python, así que los booleanos
        # hay que descartarlos ANTES de preguntar por enteros.
        if isinstance(nodo.valor, bool) or not isinstance(nodo.valor, int):
            raise NotImplementedError(
                f"[generador] Por ahora solo sé generar enteros. "
                f"Encontré {type(nodo.valor).__name__} en la línea {nodo.linea}."
            )

        if 0 <= nodo.valor < 65536:
            # `mov` con inmediato solo admite 16 bits. Para todo lo que
            # entre ahí, esta es la forma legible.
            self.emitir(f'mov x0, #{nodo.valor}', f'x0 = {nodo.valor}')
        else:
            # Para números grandes, el ensamblador guarda el valor en una
            # tabla al final de la sección y lo carga de ahí. `ldr x0, =N`
            # es la forma corta de pedir eso.
            self.emitir(f'ldr x0, ={nodo.valor}', f'x0 = {nodo.valor} (no cabe en 16 bits)')

    def visitar_Variable(self, nodo):
        # Usar una variable dentro de una expresión: leerla del stack y
        # dejarla en x0, para cumplir la misma regla de siempre. La
        # dirección sale del entorno de COMPILACIÓN (self.offsets), nunca
        # de ningún valor — en este momento el programa no ha calculado
        # nada todavía.
        offset = self.offsets.get(nodo.nombre)
        if offset is None:
            raise NotImplementedError(
                f"[generador] '{nodo.nombre}' no está en el entorno de "
                f"compilación (línea {nodo.linea}). ¿Falta su 'var'? "
                f"(los parámetros de función y los campos de struct "
                f"todavía no se generan)."
            )
        self.emitir(f'ldr x0, [x29, #-{offset}]', f'x0 = {nodo.nombre}')

    def visitar_Aritmetica(self, nodo):
        if nodo.operador not in OPERADORES:
            raise NotImplementedError(
                f"[generador] Operador '{nodo.operador}' no soportado "
                f"(línea {nodo.linea})."
            )

        nodo.izquierdo.aceptar(self)
        self.emitir(EMPUJAR, 'guardar el operando izquierdo en la pila')

        nodo.derecho.aceptar(self)
        self.emitir('mov x1, x0', 'x1 = operando derecho')
        self.emitir(SACAR, 'x0 = operando izquierdo (de vuelta de la pila)')

        instruccion = OPERADORES[nodo.operador]
        self.emitir(f'{instruccion} x0, x0, x1', f'x0 = izquierdo {nodo.operador} derecho')

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ — y es un hueco de verdad, no un adorno:
        #
        # `sdiv` es división ENTERA: 7/2 da 3. Pero el intérprete usa el
        # `/` de Python, que da 3.5. O sea que HOY los dos caminos no
        # coinciden en la división.
        #
        # Ese desacuerdo entre el intérprete y el generador es la familia
        # de bugs más difícil de encontrar en el Proyecto 2, porque el
        # programa "funciona" en los dos lados y da resultados distintos.
        # Está aquí a propósito, para que lo vean una vez en un caso
        # chiquito. Es el ejercicio 3 del README.
        # ------------------------------------------------------------------

    def visitar_Negacion(self, nodo):
        nodo.expresion.aceptar(self)
        self.emitir('neg x0, x0', 'x0 = -x0')

    def visitar_Comparacion(self, nodo):
        # El mismo esqueleto de una operación binaria: izquierdo, empujar,
        # derecho, recuperar. Lo único distinto es el final: en vez de
        # `add`, un `cmp` seguido de `cset`.
        if nodo.operador not in COMPARADORES:
            raise NotImplementedError(
                f"[generador] Comparador '{nodo.operador}' no soportado "
                f"(línea {nodo.linea})."
            )

        nodo.izquierdo.aceptar(self)
        self.emitir(EMPUJAR, 'guardar el operando izquierdo en la pila')

        nodo.derecho.aceptar(self)
        self.emitir('mov x1, x0', 'x1 = operando derecho')
        self.emitir(SACAR, 'x0 = operando izquierdo (de vuelta de la pila)')

        condicion = COMPARADORES[nodo.operador]
        self.emitir('cmp x0, x1', 'comparar: el resultado queda en las banderas, no en un registro')
        self.emitir(f'cset x0, {condicion}',
                    f'x0 = 1 si izquierdo {nodo.operador} derecho, si no 0')

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ:
        #   * Una comparación deja 1 o 0 en x0. Si la imprimen con writeln,
        #     el generador escribe `1` y el intérprete escribe `true`.
        #     Otro desacuerdo silencioso entre los dos caminos.
        #   * Un humano que escribe `if a < b` a mano NO usaría `cset`:
        #     saltaría directo con `cmp x0, x1` + `b.ge`. Aquí pasamos por
        #     un 0/1 en x0 porque así una comparación es una expresión como
        #     cualquier otra y se puede guardar, empujar o imprimir.
        #   * `&&` y `||` con corto circuito: no están en MiniPascal, y
        #     por eso no aparecen aquí. Si el lenguaje de ustedes los
        #     tiene, no se arman con `cset`: se arman con saltos.
        # ------------------------------------------------------------------

    # -- INSTRUCCIONES ------------------------------------------------------

    def visitar_Declaracion(self, nodo):
        # `var nombre: tipo [:= expresion];`  o  `const nombre: tipo := expresion;`
        #
        # En ARM64 declarar y reasignar son casi la misma instrucción
        # (`str`); lo único que hace especial a UNA declaración es que
        # antes de escribir nada hay que RESERVAR la celda donde va a vivir
        # esa variable, y anotar en el entorno de compilación dónde quedó.
        if nodo.tipo != 'integer':
            raise NotImplementedError(
                f"[generador] Por ahora solo sé reservar espacio para "
                f"'integer'. Encontré '{nodo.tipo}' en la línea {nodo.linea}."
            )

        self.lineas.append('')
        self.comentario(f"var {nodo.nombre}: {nodo.tipo}  — línea {nodo.linea}")

        # Un offset nuevo, de 16 en 16 — el mismo número que ya usan los
        # empujones de expresiones, y por la misma razón: sp siempre
        # alineado a 16 bytes. Guardar 8 bytes reales en una celda de 16
        # es desperdicio a propósito, no un error.
        self.proximo_offset += 16
        offset = self.proximo_offset

        # Fíjense en lo que ESTE método ya no escribe: el `sub sp, sp, #16`
        # de la sesión de variables. Con `if` y `while`, una declaración
        # puede ejecutarse cero veces (rama no tomada) o mil (dentro de un
        # ciclo), y un `sub sp` por declaración deja de coincidir con el
        # offset que se calculó al generar. Ahora el frame completo se
        # reserva UNA vez, en el prólogo, con el tamaño final. Ver
        # `ensamblar_archivo` y la idea 10 del README.

        # El entorno de compilación es lo que hace que la línea de abajo
        # sepa, más adelante, dónde buscar 'nodo.nombre': una consulta a
        # un diccionario de Python, resuelta HOY, no cuando corra el
        # binario.
        self.offsets[nodo.nombre] = offset

        if nodo.expresion_inicial is not None:
            nodo.expresion_inicial.aceptar(self)   # deja el valor en x0
        else:
            self.emitir('mov x0, #0', 'sin valor inicial: 0 por defecto')
        self.emitir(f'str x0, [x29, #-{offset}]', f'{nodo.nombre} = x0')

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ:
        #   * `const` no se distingue de `var`: nada impide, en ESTE
        #     archivo, reasignarla más adelante. Que sea un error es
        #     trabajo del análisis semántico, no del generador.
        #   * los `begin...end` anidados no cierran su propio tramo de
        #     offsets: una variable declarada en un bloque interno sigue
        #     "viva" (su offset sigue en self.offsets) después de `end`.
        #     Con MiniPascal de hoy no se nota porque los nombres no se
        #     repiten entre bloques — en cuanto agreguen shadowing, sí.
        # ------------------------------------------------------------------

    def visitar_Asignacion(self, nodo):
        # `nombre := expresion;`  — la variable YA existe: solo se busca
        # su offset (ya reservado por una Declaracion anterior) y se
        # sobrescribe. A diferencia de Declaracion, esto NUNCA mueve sp:
        # reservar espacio pasa una sola vez, al generar la declaración.
        offset = self.offsets.get(nodo.nombre)
        if offset is None:
            raise NotImplementedError(
                f"[generador] '{nodo.nombre}' no está en el entorno de "
                f"compilación (línea {nodo.linea}). ¿Falta su 'var'?"
            )

        self.lineas.append('')
        self.comentario(f"{nodo.nombre} := ...  — línea {nodo.linea}")
        nodo.expresion.aceptar(self)   # deja el nuevo valor en x0
        self.emitir(f'str x0, [x29, #-{offset}]', f'{nodo.nombre} = x0')

    # -- ARREGLOS: el puntero en el stack, los datos en el heap -------------

    def visitar_DeclaracionArreglo(self, nodo):
        # `var nombre: array[N] of integer;`
        #
        # Comparen con visitar_Declaracion, más arriba. Es la MISMA forma:
        # una celda de 16 bytes en el frame, un offset anotado en
        # self.offsets. Lo único distinto es QUÉ se guarda en la celda: ya
        # no el valor, sino la DIRECCIÓN de un bloque que se pidió con alloc.
        if nodo.tipo_elemento != 'integer':
            raise NotImplementedError(
                f"[generador] Por ahora solo sé reservar arreglos de "
                f"'integer'. Encontré '{nodo.tipo_elemento}' en la línea "
                f"{nodo.linea}."
            )

        self.usa_heap = True
        self.lineas.append('')
        self.comentario(
            f"var {nodo.nombre}: array[{nodo.tamano}] of {nodo.tipo_elemento}"
            f"  — línea {nodo.linea}"
        )

        self.proximo_offset += 16
        offset = self.proximo_offset          # la celda ya viene en el frame
        self.offsets[nodo.nombre] = offset

        # N enteros de 8 bytes cada uno. El tamaño sale del texto del
        # programa, así que la multiplicación se hace AQUÍ, al generar:
        # el .s ya trae el número final.
        self.emitir(f'mov x0, #{nodo.tamano * 8}', f'x0 = {nodo.tamano} enteros x 8 bytes')
        self.emitir('bl alloc', 'x0 = dirección del bloque en el heap')
        self.emitir(f'str x0, [x29, #-{offset}]', f'{nodo.nombre} = x0  (un PUNTERO, no datos)')

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ:
        #   * Arreglos de otros tipos (real, boolean, string): cada uno
        #     mide distinto y se lee con instrucciones distintas.
        #   * Arreglos de arreglos: ¿cuántos bytes pedir, y cómo se llega
        #     a la casilla [i][j]?
        #   * El arreglo arranca en ceros porque el kernel entrega la
        #     memoria de brk en ceros (ver arm/04_brk.s). Eso coincide con
        #     el valor por defecto de `integer`; no coincidiría con otro
        #     valor por defecto, y ahí habría que escribirlo a mano.
        # ------------------------------------------------------------------

    def visitar_Indexado(self, nodo):
        # `nombre[indice]` como expresión: deja en x0 el valor de la casilla.
        offset = self.offsets.get(nodo.nombre)
        if offset is None:
            raise NotImplementedError(
                f"[generador] '{nodo.nombre}' no está en el entorno de "
                f"compilación (línea {nodo.linea}). ¿Falta su 'var'?"
            )

        nodo.indice.aceptar(self)                   # x0 = el índice
        self.emitir(f'ldr x1, [x29, #-{offset}]', f'x1 = {nodo.nombre} (el puntero)')
        self.emitir('ldr x0, [x1, x0, lsl #3]', f'x0 = {nodo.nombre}[índice]  (puntero + índice * 8)')

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ: nadie comprueba que el índice esté dentro del
        # arreglo. El intérprete sí lo hace y reporta un error semántico;
        # este código lee la memoria de al lado sin avisar. Otro caso de
        # intérprete y generador en desacuerdo.
        # ------------------------------------------------------------------

    def visitar_AsignacionIndexada(self, nodo):
        # `nombre[indice] := expresion;`
        offset = self.offsets.get(nodo.nombre)
        if offset is None:
            raise NotImplementedError(
                f"[generador] '{nodo.nombre}' no está en el entorno de "
                f"compilación (línea {nodo.linea}). ¿Falta su 'var'?"
            )

        self.lineas.append('')
        self.comentario(f"{nodo.nombre}[...] := ...  — línea {nodo.linea}")

        nodo.expresion.aceptar(self)                # x0 = el valor nuevo
        self.emitir(EMPUJAR, 'guardar el valor mientras se calcula el índice')
        nodo.indice.aceptar(self)                   # x0 = el índice
        self.emitir('mov x1, x0', 'x1 = índice')
        self.emitir(SACAR, 'x0 = el valor nuevo (de vuelta de la pila)')
        self.emitir(f'ldr x2, [x29, #-{offset}]', f'x2 = {nodo.nombre} (el puntero)')
        self.emitir('str x0, [x2, x1, lsl #3]', f'{nodo.nombre}[índice] = x0  (puntero + índice * 8)')

    def visitar_Writeln(self, nodo):
        self.lineas.append('')
        self.comentario(f'writeln(...)  — línea {nodo.linea} del programa fuente')

        nodo.expresion.aceptar(self)      # el valor a imprimir queda en x0

        # printf(formato, valor): el formato va en x0 y el valor en x1. Como
        # el valor YA está en x0, hay que correrlo a x1 ANTES de pisar x0
        # con la dirección del formato. Invertir estas dos líneas es un
        # error clásico, y silencioso: imprime basura, no falla.
        self.emitir('mov x1, x0', 'x1 = el valor a imprimir')
        self.emitir('adrp x0, fmt_entero', 'x0 = página donde vive el formato')
        self.emitir('add x0, x0, :lo12:fmt_entero', 'x0 += desplazamiento dentro de la página')
        self.emitir('bl printf', 'llamar a printf de la biblioteca de C')

    def visitar_Bloque(self, nodo):
        # Nada especial: un bloque es su lista de instrucciones, en orden.
        # Fíjense en lo que ESTE método NO hace: no abre ni cierra ningún
        # ámbito de offsets. `self.offsets` es uno solo para todo el
        # programa, y las declaraciones de un `begin...end` anidado
        # simplemente se acumulan ahí — es el hueco que queda anotado en
        # `visitar_Declaracion`.
        for instruccion in nodo.instrucciones:
            instruccion.aceptar(self)

    # -- CONTROL DE FLUJO: etiquetas y saltos -------------------------------

    def saltar_si_falso(self, etiqueta):
        """La condición ya está en x0 (0 = falso, 1 = verdadero). Si es
        falso, saltar a `etiqueta`; si no, seguir con la instrucción de abajo."""
        self.emitir('cmp x0, #0', 'x0 es 0 (falso) o 1 (verdadero)')
        self.emitir(f'b.eq {etiqueta}', 'si es falso, saltar')

    def visitar_If(self, nodo):
        # if <condicion> then <bloque_si> [else <bloque_no>];
        #
        # Sin else:                 Con else:
        #
        #       <condicion>               <condicion>
        #       si falso -> fin           si falso -> sino
        #       <bloque_si>               <bloque_si>
        #   fin:                          saltar a fin
        #                             sino:
        #                                 <bloque_no>
        #                             fin:
        self.lineas.append('')
        self.comentario(f'if ...  — línea {nodo.linea}')

        fin = self.nueva_etiqueta('if_fin')
        nodo.condicion.aceptar(self)                 # x0 = 0 o 1

        if nodo.bloque_no is None:
            self.saltar_si_falso(fin)
            nodo.bloque_si.aceptar(self)
        else:
            sino = self.nueva_etiqueta('sino')
            self.saltar_si_falso(sino)
            nodo.bloque_si.aceptar(self)
            self.emitir(f'b {fin}', 'terminó el then: saltarse el else')
            self.poner_etiqueta(sino)
            nodo.bloque_no.aceptar(self)

        self.poner_etiqueta(fin)

    def visitar_While(self, nodo):
        # [etiqueta:] while <condicion> do <cuerpo>;
        #
        #   inicio:
        #       <condicion>
        #       si falso -> fin
        #       <cuerpo>
        #       saltar a inicio          <- el salto hacia ATRÁS es el ciclo
        #   fin:
        self.lineas.append('')
        self.comentario(f'while ...  — línea {nodo.linea}')

        inicio = self.nueva_etiqueta('while_inicio')
        fin = self.nueva_etiqueta('while_fin')

        # `continue` salta a `inicio` (volver a evaluar la condición) y
        # `break` salta a `fin`. Se registran ANTES de generar el cuerpo,
        # porque es adentro del cuerpo donde se van a usar.
        self.ciclos.append({'nombre': nodo.etiqueta, 'continuar': inicio, 'salir': fin})

        self.poner_etiqueta(inicio)
        nodo.condicion.aceptar(self)
        self.saltar_si_falso(fin)
        nodo.cuerpo.aceptar(self)
        self.emitir(f'b {inicio}', 'volver a evaluar la condición')
        self.poner_etiqueta(fin)

        self.ciclos.pop()

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ:
        #   * `repeat ... until` y `case`: el mecanismo es el mismo (cmp,
        #     saltos, etiquetas). Repeat evalúa la condición AL FINAL; case
        #     es una cadena de cmp + b.eq, una por rama.
        #   * Si la condición no es boolean (`while 5 + 3 do`), el
        #     intérprete reporta un error semántico y este código simplemente
        #     toma x0 != 0 como verdadero.
        # ------------------------------------------------------------------

    def ciclo_destino(self, nodo, instruccion):
        """El ciclo al que se refiere un break/continue: el más interno, o el
        que tenga la etiqueta indicada."""
        if not self.ciclos:
            raise NotImplementedError(
                f"[generador] '{instruccion}' fuera de un ciclo "
                f"(línea {nodo.linea})."
            )
        if nodo.etiqueta is None:
            return self.ciclos[-1]
        for ciclo in reversed(self.ciclos):
            if ciclo['nombre'] == nodo.etiqueta:
                return ciclo
        raise NotImplementedError(
            f"[generador] No hay un ciclo con la etiqueta "
            f"'{nodo.etiqueta}' para '{instruccion}' (línea {nodo.linea})."
        )

    def visitar_Break(self, nodo):
        destino = self.ciclo_destino(nodo, 'break')['salir']
        self.emitir(f'b {destino}', f'break: saltar al final del ciclo  — línea {nodo.linea}')

    def visitar_Continue(self, nodo):
        destino = self.ciclo_destino(nodo, 'continue')['continuar']
        self.emitir(f'b {destino}', f'continue: saltar a la condición  — línea {nodo.linea}')

    def visitar_Programa(self, nodo):
        nodo.bloque.aceptar(self)

    # -- armar el archivo completo ------------------------------------------

    def generar(self, arbol):
        """Recorre el árbol y devuelve el texto del archivo .s completo."""
        self.lineas = []
        arbol.aceptar(self)
        return self.ensamblar_archivo(arbol.nombre)

    def ensamblar_archivo(self, nombre_programa):
        """Envuelve las instrucciones generadas con lo que todo programa
        ARM64 necesita alrededor: la sección de datos, la etiqueta de
        entrada, el prólogo y el epílogo."""
        cuerpo = '\n'.join(self.lineas)

        # El tamaño del frame se conoce SOLO ahora, cuando ya se recorrió
        # todo el programa: es el último offset que se repartió. Por eso la
        # reserva se escribe aquí, en el prólogo, y no donde está cada `var`.
        if self.proximo_offset > 0:
            reserva = (f"    sub sp, sp, #{self.proximo_offset}"
                       f"          // reservar el frame completo: "
                       f"{self.proximo_offset // 16} celdas de 16 bytes\n")
        else:
            reserva = ''

        # El heap solo existe en el .s si el programa lo usa.
        bss = f'\n{SECCION_BSS}' if self.usa_heap else ''
        rutinas = RUTINA_ALLOC if self.usa_heap else ''

        return f'''// ==========================================================
// Generado automáticamente por MiniPascal v6
// Programa fuente: {nombre_programa}
//
// Para ensamblar, enlazar y ejecutar:
//     aarch64-linux-gnu-gcc -static salida.s -o salida
//     qemu-aarch64 ./salida
// ==========================================================

// --- Datos: constantes que el programa necesita en memoria ---
.section .data

// El formato que usa printf. `%ld` = entero de 64 bits (una `long`),
// que es el tamaño de los registros xN. `.asciz` agrega el byte cero
// del final, que es como C sabe dónde termina una cadena.
fmt_entero:
    .asciz "%ld\\n"
{bss}
// --- Código ---
.section .text
.global main

main:
    // Prólogo: guardar el frame pointer (x29) y la dirección de retorno
    // (x30) en la pila. Hace falta porque abajo llamamos a printf con
    // `bl`, y `bl` PISA x30 con su propia dirección de retorno. Sin esto
    // main no sabría a dónde volver.
    stp x29, x30, [sp, #-16]!
    mov x29, sp
{reserva}
{cuerpo}

    // Epílogo: devolver 0 y restaurar lo que guardamos en el prólogo.
    mov w0, #0
    mov sp, x29             // soltar TODO el frame de una vez
    ldp x29, x30, [sp], #16
    ret
{rutinas}'''
