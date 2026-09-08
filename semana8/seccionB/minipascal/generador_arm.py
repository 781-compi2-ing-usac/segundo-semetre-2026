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
Solo esto:

    * literales enteros
    * + - * / y el menos unario
    * writeln(<expresión entera>)
    * bloques y el programa

Cualquier otro nodo produce un mensaje claro diciendo qué falta (lo hace
la clase base, en `visitante.py`). Esa lista de mensajes es su hoja de
ruta: variables en el stack, control de flujo, funciones, memoria. Vayan
tachándola.

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


class GeneradorARM64(Visitante):
    """Recorre el AST y ESCRIBE ensamblador ARM64."""

    etiqueta = 'generador'

    def __init__(self):
        self.lineas = []       # el ensamblador que llevamos escrito

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

    # -- INSTRUCCIONES ------------------------------------------------------

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
        # Sin entorno ni ámbito todavía: hoy no hay variables que declarar.
        # En cuanto las agreguen, este método se vuelve el interesante — es
        # donde se abre y se cierra un ámbito de offsets del stack frame.
        for instruccion in nodo.instrucciones:
            instruccion.aceptar(self)

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

{cuerpo}

    // Epílogo: devolver 0 y restaurar lo que guardamos en el prólogo.
    mov w0, #0
    ldp x29, x30, [sp], #16
    ret
'''
