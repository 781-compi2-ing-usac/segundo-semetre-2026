"""
MICRO-EJEMPLO 3: dos entornos, dos preguntas distintas. Sin PLY.

Desde la Sesión 2 del Proyecto 1 ya existe un `Entorno` (entorno.py) que
responde una pregunta: "¿qué VALOR tiene 'x' ahora mismo?". Ese entorno
solo puede existir mientras el programa está corriendo — antes de
ejecutar la primera línea, ninguna variable tiene valor todavía.

Pero el generador de hoy necesita responder otra pregunta, ANTES de que
el programa corra ni una instrucción: "¿en qué DIRECCIÓN de memoria va a
vivir 'x'?". Esa pregunta se puede responder mirando solo el texto del
programa, sin ejecutar nada — y por eso el generador la responde durante
la generación de código, no durante la ejecución.

Dos entornos, dos momentos, dos preguntas:

    EntornoDeEjecucion   nombre -> valor    "¿cuánto vale 'x' AHORA?"
    EntornoDeCompilacion nombre -> offset   "¿DÓNDE va a vivir 'x'?"

Correr con: python3 03_entorno_compilacion.py
"""


# ===========================================================================
# El entorno de EJECUCIÓN — el de siempre, desde la Sesión 2
# ===========================================================================
#
# Ya lo conocen de entorno.py. Aquí va una versión mínima, solo para tener
# los dos lado a lado.

class EntornoDeEjecucion:
    """nombre -> valor. Solo tiene sentido mientras el programa CORRE."""

    def __init__(self):
        self.valores = {}

    def declarar(self, nombre, valor):
        self.valores[nombre] = valor

    def asignar(self, nombre, valor):
        self.valores[nombre] = valor

    def leer(self, nombre):
        return self.valores[nombre]


# ===========================================================================
# El entorno de COMPILACIÓN — nuevo hoy
# ===========================================================================
#
# Misma forma exacta que el de arriba — un diccionario nombre -> algo — y
# esa semejanza no es casualidad: es la razón por la que a los dos se les
# llama "entorno". La diferencia entera está en QUÉ guardan.

class EntornoDeCompilacion:
    """nombre -> offset. Tiene sentido ANTES de que el programa corra ni
    una instrucción: es información sobre la FORMA del stack frame, no
    sobre ningún valor."""

    def __init__(self):
        self.offsets = {}
        self.proximo_offset = 0

    def declarar(self, nombre):
        """Reservar la siguiente celda de 16 bytes y anotar dónde quedó."""
        self.proximo_offset += 16
        self.offsets[nombre] = self.proximo_offset
        return self.proximo_offset

    def offset_de(self, nombre):
        return self.offsets[nombre]

    def tamano_del_frame(self):
        """Cuánto espacio hay que reservar en total — lo que en
        generador_arm.py se pide con `sub sp, sp, #N`."""
        return self.proximo_offset


# ===========================================================================
# El mismo programa, leído por los dos entornos
# ===========================================================================
#
#     var a: integer := 10;
#     var b: integer := 20;
#     a := a + b;
#     writeln(a);

print("=" * 70)
print("UN PROGRAMA, DOS ENTORNOS")
print("=" * 70)

print("""
    var a: integer := 10;
    var b: integer := 20;
    a := a + b;
    writeln(a);
""")

# --- Camino 1: interpretarlo -------------------------------------------
# Esto SÍ ejecuta las instrucciones, en orden, y por eso puede contestar
# "cuánto vale a AHORA" en cada paso.
print("-" * 70)
print("EntornoDeEjecucion — corriendo el programa de verdad")
print("-" * 70)

ejecucion = EntornoDeEjecucion()
ejecucion.declarar('a', 10)
print(f"  declarar a := 10          -> a vale {ejecucion.leer('a')}")
ejecucion.declarar('b', 20)
print(f"  declarar b := 20          -> b vale {ejecucion.leer('b')}")
ejecucion.asignar('a', ejecucion.leer('a') + ejecucion.leer('b'))
print(f"  a := a + b                -> a vale {ejecucion.leer('a')}")
print(f"  writeln(a)                -> imprime {ejecucion.leer('a')}")

# --- Camino 2: generar código para él -----------------------------------
# Esto NO ejecuta nada. Nunca calcula 10+20. Solo decide dónde va a vivir
# cada variable y escribe las instrucciones que, más tarde, un procesador
# va a ejecutar para calcularlo de verdad.
print()
print("-" * 70)
print("EntornoDeCompilacion — generando ARM64, SIN ejecutar nada")
print("-" * 70)

compilacion = EntornoDeCompilacion()

offset_a = compilacion.declarar('a')
print(f"  declarar a               -> a vive en [x29, #-{offset_a}]")
print(f"                               (compilación NO sabe que a vale 10 —")
print(f"                               solo sabe DÓNDE va a estar cuando exista)")

offset_b = compilacion.declarar('b')
print(f"  declarar b               -> b vive en [x29, #-{offset_b}]")

print(f"\n  a := a + b se traduce sin calcular nada, solo leyendo offsets:")
print(f"      ldr x0, [x29, #-{compilacion.offset_de('a')}]   // x0 = a")
print(f"      str x0, [sp, #-16]!")
print(f"      ldr x0, [x29, #-{compilacion.offset_de('b')}]   // x0 = b")
print(f"      mov x1, x0")
print(f"      ldr x0, [sp], #16")
print(f"      add x0, x0, x1")
print(f"      str x0, [x29, #-{compilacion.offset_de('a')}]   // a = x0")

print(f"\n  tamaño total del frame   -> {compilacion.tamano_del_frame()} bytes")
print(f"                               (lo que generador_arm.py pediría con")
print(f"                               'sub sp, sp, #16' una vez por variable)")

print()
print("=" * 70)
print("LA DIFERENCIA, EN UNA FRASE")
print("=" * 70)
print("""
El entorno de ejecución responde "cuánto vale" corriendo el programa.
El entorno de compilación responde "dónde vive" leyendo el programa,
sin correr ni una línea. El primero no puede existir antes de ejecutar;
el segundo no puede usar ningún valor, porque todavía no hay ninguno.

Esa es la regla que ya vieron en generador_arm.py, dicha de otra forma:
un compilador escribe instrucciones para que OTRO las calcule después.
Nunca calcula él mismo.
""")
