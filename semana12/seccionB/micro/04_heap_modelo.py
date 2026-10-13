"""
MICRO-EJEMPLO 4: el heap y su tabla, modelados en Python. Sin PLY.

En 04_brk.s y 05_alloc_tabla.s el heap es memoria de verdad. Aquí lo
modelamos con objetos de Python para ver, sin ensamblador de por medio,
las tres ideas de la semana:

    1. El heap es una zona que CRECE: un "break" que solo sube.
    2. La variable vive en el FRAME, y su celda guarda una DIRECCIÓN.
    3. La TABLA anota cada bloque que se reservó: (base, tamaño).

Las direcciones de aquí son números inventados (arrancan en 1000) para que
se lean fácil. Las de verdad cambian en cada máquina y no importan: lo que
importa es la relación entre ellas.

Correr con: python3 04_heap_modelo.py
"""


# ===========================================================================
# El heap: un break que sube, y una tabla que lleva la cuenta
# ===========================================================================

class Heap:
    def __init__(self, inicio=1000):
        self.break_actual = inicio     # lo que devuelve brk(0)
        self.memoria = {}              # dirección -> valor (solo lo escrito)
        self.tabla = []                # una fila por bloque: (base, tamaño)

    def brk(self, nuevo):
        """brk(0) devuelve el break. brk(dir) lo mueve a `dir`."""
        if nuevo != 0:
            self.break_actual = nuevo
        return self.break_actual

    def alloc(self, n):
        """Lo mismo que hace la rutina `alloc` de 05_alloc_tabla.s."""
        base = self.brk(0)                  # 1. ¿dónde estamos?
        self.brk(base + n)                  # 2. crecer n bytes
        self.tabla.append((base, n))        # 3. anotarlo
        return base                         # 4. entregar la dirección

    def escribir(self, direccion, valor):
        self.memoria[direccion] = valor

    def leer(self, direccion):
        # La memoria que entrega brk viene en ceros.
        return self.memoria.get(direccion, 0)


# ===========================================================================
# El programa:   var a: array[4] of integer;
#                var b: array[2] of integer;
#                a[0] := 10;  b := a;  (¿qué pasa aquí?)
# ===========================================================================

heap = Heap()

# El FRAME: nombre -> lo que hay en su celda. Para estos arreglos, la celda
# guarda una DIRECCIÓN (un puntero), no los datos.
frame = {}

frame['a'] = heap.alloc(4 * 8)
frame['b'] = heap.alloc(2 * 8)

print("--- Después de declarar a y b ---")
print(f"frame : {frame}")
print(f"tabla : {heap.tabla}")
print(f"break : {heap.break_actual}")
print()

# a[0] := 10   ->   dirección = puntero + índice * 8
heap.escribir(frame['a'] + 0 * 8, 10)
heap.escribir(frame['a'] + 3 * 8, 40)

print("--- Después de a[0] := 10; a[3] := 40 ---")
print(f"a[0] = {heap.leer(frame['a'] + 0 * 8)}")
print(f"a[3] = {heap.leer(frame['a'] + 3 * 8)}")
print(f"a[1] = {heap.leer(frame['a'] + 1 * 8)}   <- nunca se escribió: ceros")
print()


# ===========================================================================
# La pregunta que sale sola
# ===========================================================================
#
# Si copiamos la celda de `a` en la de `b`, ¿qué copiamos?

frame['b'] = frame['a']

print("--- Después de  b := a  ---")
print(f"frame : {frame}")
print(f"b[0] = {heap.leer(frame['b'] + 0 * 8)}   <- el mismo 10 que escribimos en a")
heap.escribir(frame['b'] + 0 * 8, 99)
print(f"a[0] = {heap.leer(frame['a'] + 0 * 8)}   <- cambió AL ESCRIBIR en b")
print()
print("Se copió la DIRECCIÓN, no los datos. Las dos celdas apuntan al mismo")
print("bloque. Y el bloque que `b` tenía antes sigue en la tabla, sin dueño:")
print(f"tabla : {heap.tabla}")
print()

# ===========================================================================
# Para pensar
# ===========================================================================
#
#  * Si su lenguaje quiere que `b := a` COPIE los datos, ¿quién tiene que
#    pedir el bloque nuevo y copiar elemento por elemento: el programador
#    o el compilador? ¿Qué instrucciones de ARM64 haría falta generar?
#
#  * El bloque viejo de `b` quedó en la tabla pero ya nadie lo usa. ¿Qué
#    campo le agregarían a la tabla para saberlo? ¿Cuándo se llenaría?
