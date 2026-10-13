"""
MICRO-EJEMPLO 2: el patrón Visitor. Sin PLY.

Objetivo: el mismo árbol de 01_por_que_visitor.py, pero cortado por
columnas en vez de por filas. Al final del archivo agregamos un TERCER
recorrido sin tocar ni una línea de las clases de nodo — esa es la prueba
de que el patrón sirve.

Correr con: python3 02_visitor.py
"""


# ===========================================================================
# LOS NODOS — ahora son datos, y nada más
# ===========================================================================
#
# Fíjense en lo que ya NO está: `evaluar`. Un nodo ya no sabe hacer nada.
# Solo sabe qué es y quiénes son sus hijos.
#
# `aceptar` no es lógica: es una sola línea que dice "de tus métodos, el
# mío es este". Siempre la misma forma, en las 30 clases.

class Numero:
    def __init__(self, valor):
        self.valor = valor

    def aceptar(self, v):
        return v.visitar_Numero(self)


class Suma:
    def __init__(self, izq, der):
        self.izq = izq
        self.der = der

    def aceptar(self, v):
        return v.visitar_Suma(self)


class Multiplicacion:
    def __init__(self, izq, der):
        self.izq = izq
        self.der = der

    def aceptar(self, v):
        return v.visitar_Multiplicacion(self)


# ===========================================================================
# RECORRIDO 1 — ejecutar
# ===========================================================================
#
# Todo el intérprete, junto, en un solo lugar. Esta clase es la COLUMNA
# "evaluar" de la tabla del ejemplo anterior.

class Interprete:
    def visitar_Numero(self, nodo):
        return nodo.valor

    def visitar_Suma(self, nodo):
        return nodo.izq.aceptar(self) + nodo.der.aceptar(self)

    def visitar_Multiplicacion(self, nodo):
        return nodo.izq.aceptar(self) * nodo.der.aceptar(self)


# ===========================================================================
# RECORRIDO 2 — generar ensamblador ARM64
# ===========================================================================
#
# Otra columna, otro archivo (aquí es otra clase para que quepa todo en
# una pantalla; en minipascal/ sí son archivos separados).
#
# La diferencia con el intérprete es la que importa: el intérprete
# DEVUELVE un 14; este no devuelve nada, va ESCRIBIENDO instrucciones.
# El 14 no existe todavía y no va a existir hasta que el procesador
# ejecute lo que escribimos.

class GeneradorARM64:
    def __init__(self):
        self.lineas = []
        # Este contador es la razón número 3 del ejemplo anterior: le
        # pertenece al RECORRIDO, no a ningún nodo. Aquí tiene dónde
        # vivir sin esfuerzo. Hoy no se usa; en cuanto agreguen `if` y
        # `while` va a ser imprescindible, porque cada ciclo necesita sus
        # propias etiquetas (L_inicio_1, L_fin_1, L_inicio_2, ...) y ese
        # contador no le pertenece a ningún nodo.
        self.siguiente_etiqueta = 0

    def visitar_Numero(self, nodo):
        self.lineas.append(f'mov x0, #{nodo.valor}')

    def visitar_Suma(self, nodo):
        self.binaria(nodo, 'add')

    def visitar_Multiplicacion(self, nodo):
        self.binaria(nodo, 'mul')

    def binaria(self, nodo, instruccion):
        # La regla, la misma de generador_arm.py:
        # toda expresión deja su resultado en x0.
        nodo.izq.aceptar(self)
        self.lineas.append('str x0, [sp, #-16]!')   # empujar el izquierdo
        nodo.der.aceptar(self)
        self.lineas.append('mov x1, x0')            # el derecho pasa a x1
        self.lineas.append('ldr x0, [sp], #16')     # recuperar el izquierdo
        self.lineas.append(f'{instruccion} x0, x0, x1')


# ===========================================================================
# Probar los dos sobre EL MISMO árbol
# ===========================================================================

arbol = Suma(Numero(2), Multiplicacion(Numero(3), Numero(4)))   # 2 + 3 * 4

print("=" * 70)
print("UN ÁRBOL, DOS RECORRIDOS")
print("=" * 70)
print(f"\nRecorrido 1 (Interprete):  {arbol.aceptar(Interprete())}")

generador = GeneradorARM64()
arbol.aceptar(generador)
print("\nRecorrido 2 (GeneradorARM64):")
for linea in generador.lineas:
    print(f"    {linea}")

print("""
Sigan el ensamblador de arriba con un dedo, empezando con la pila vacía:

    mov x0, #2            x0=2
    str x0, [sp,#-16]!    pila: [2]        <- el 2 se guarda porque lo que
    mov x0, #3            x0=3                sigue va a pisar x0
    str x0, [sp,#-16]!    pila: [2, 3]
    mov x0, #4            x0=4
    mov x1, x0            x1=4
    ldr x0, [sp],#16      x0=3   pila: [2]
    mul x0, x0, x1        x0=12
    mov x1, x0            x1=12
    ldr x0, [sp],#16      x0=2   pila: []
    add x0, x0, x1        x0=14             <- el mismo 14, dos días después
""")


# ===========================================================================
# LA PRUEBA: un tercer recorrido, sin tocar los nodos
# ===========================================================================
#
# Nada de lo de arriba se modificó para que esto exista. Ni una línea.

class ContadorDeOperaciones:
    """Cuenta cuántas operaciones aritméticas tiene una expresión.

    Un recorrido de juguete, pero de la misma familia que los que sí van a
    escribir: un verificador de tipos, un detector de código muerto, un
    optimizador de constantes.
    """

    def visitar_Numero(self, nodo):
        return 0

    def visitar_Suma(self, nodo):
        return 1 + nodo.izq.aceptar(self) + nodo.der.aceptar(self)

    def visitar_Multiplicacion(self, nodo):
        return 1 + nodo.izq.aceptar(self) + nodo.der.aceptar(self)


print("=" * 70)
print("EL TERCER RECORRIDO")
print("=" * 70)
print(f"""
Operaciones en el árbol: {arbol.aceptar(ContadorDeOperaciones())}

Para agregarlo hubo que escribir una clase. Cero cambios en Numero, Suma
y Multiplicacion.

Con el patrón Intérprete habría que haber abierto las tres clases y
agregarle un método a cada una. Con 30 clases, treinta ediciones.
""")

print("=" * 70)
print("EL PRECIO — porque todo patrón tiene uno")
print("=" * 70)
print("""
Agregar un RECORRIDO es gratis. Agregar un NODO no.

Si mañana aparece `Resta`, hay que tocar CUATRO lugares: la clase nueva,
y los tres visitantes. Con el patrón Intérprete habría sido un solo
lugar: la clase, con sus métodos adentro.

O sea que el Visitor no es "mejor". Es un intercambio:

    facilita agregar recorridos    <->    dificulta agregar nodos

Conviene cuando uno agrega recorridos seguido y nodos casi nunca. Que es
exactamente la situación del Proyecto 2: la gramática ya está definida en
el enunciado y no va a cambiar, mientras que recorridos van a necesitar
por lo menos dos, probablemente tres.

Si su proyecto fuera al revés —gramática cambiando todas las semanas, un
solo recorrido— el patrón Intérprete del Proyecto 1 seguiría siendo la
mejor opción. Elegir un patrón es elegir qué cambio quieren que sea
barato.
""")
