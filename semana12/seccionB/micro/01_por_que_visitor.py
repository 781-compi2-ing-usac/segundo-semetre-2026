"""
MICRO-EJEMPLO 1: por qué necesitamos el patrón Visitor. Sin PLY.

Objetivo: NO aprender el patrón todavía. Sentir el problema que resuelve.
Si se saltan este archivo y van directo al 02, el patrón les va a parecer
burocracia innecesaria. Con este, no.

El punto de partida es el AST que ya tienen del Proyecto 1: cada nodo
sabe evaluarse a sí mismo. Funcionó perfecto durante cinco sesiones.
Aquí lo reducimos a tres clases para que quepa en una pantalla.

Correr con: python3 01_por_que_visitor.py
"""


# ===========================================================================
# LO QUE YA TIENEN — el patrón Intérprete
# ===========================================================================

class Numero:
    def __init__(self, valor):
        self.valor = valor

    def evaluar(self):
        return self.valor


class Suma:
    def __init__(self, izq, der):
        self.izq = izq
        self.der = der

    def evaluar(self):
        return self.izq.evaluar() + self.der.evaluar()


class Multiplicacion:
    def __init__(self, izq, der):
        self.izq = izq
        self.der = der

    def evaluar(self):
        return self.izq.evaluar() * self.der.evaluar()


# El árbol de  2 + 3 * 4  (el mismo del ejemplo 02_aritmetica.mpas)
arbol = Suma(Numero(2), Multiplicacion(Numero(3), Numero(4)))

print("=" * 70)
print("LO QUE YA FUNCIONA")
print("=" * 70)
print(f"2 + 3 * 4  =  {arbol.evaluar()}")
print()
print("Tres clases, un método cada una. Limpio. Nada que arreglar.")
print()


# ===========================================================================
# LO QUE PIDE EL PROYECTO 2
# ===========================================================================

print("=" * 70)
print("AHORA LLEGA EL PROYECTO 2")
print("=" * 70)
print("""
Ya no basta con ejecutar el árbol: hay que GENERAR ENSAMBLADOR a partir
de él. Y ejecutar sigue haciendo falta, porque los reportes y las pruebas
lo usan.

La salida obvia es agregarle otro método a cada clase:

    class Suma:
        def evaluar(self):
            return self.izq.evaluar() + self.der.evaluar()

        def generar(self):                       # <- el método nuevo
            return (self.izq.generar()
                    + ['str x0, [sp, #-16]!']
                    + self.der.generar()
                    + ['mov x1, x0', 'ldr x0, [sp], #16', 'add x0, x0, x1'])

Funciona. Con tres clases se ve hasta razonable.

Hagan la cuenta con el árbol de verdad, el de MiniPascal:

    30 clases de nodo  x  1 recorrido   =  30 métodos     <- Proyecto 1
    30 clases de nodo  x  2 recorridos  =  60 métodos     <- Proyecto 2
    30 clases de nodo  x  3 recorridos  =  90 métodos     <- + verificador de tipos

Y los 90 en el MISMO archivo, alternados de tres en tres.
""")

print("Los tres problemas concretos, sin dramatismo:")
print("""
1. NO SE PUEDE LEER "EL GENERADOR" DE CORRIDO.
   Está partido en 30 pedazos, uno por clase, cada uno separado del
   siguiente por dos métodos que no tienen nada que ver. Para entender
   cómo se genera código hay que saltar por todo el archivo.

2. NO SE PUEDE TRABAJAR SIN CHOCAR.
   Aunque el proyecto es individual: cuando estén depurando la generación
   de `while` y a la vez un error del intérprete en `case`, los dos
   cambios caen en el mismo archivo de 2000 líneas.

3. LOS RECORRIDOS NECESITAN COSAS DISTINTAS Y NO HAY DÓNDE PONERLAS.
   El intérprete necesita un entorno de valores. El generador necesita un
   contador de etiquetas, la tabla de offsets del stack frame y el texto
   que lleva escrito. ¿Dónde viven esos contadores? ¿Como atributos del
   nodo `Suma`? ¿Como variables globales?

   Este tercero es el que de verdad duele, y el que se van a topar en
   octubre generando `while`: cada ciclo necesita etiquetas ÚNICAS
   (L_inicio_1, L_fin_1, L_inicio_2, ...) y ese contador no le pertenece
   a ningún nodo — le pertenece al RECORRIDO.
""")

print("=" * 70)
print("LA PREGUNTA")
print("=" * 70)
print("""
Los métodos están agrupados por NODO (todo lo de Suma junto).
Los necesitamos agrupados por RECORRIDO (todo lo del generador junto).

Es la misma información en una tabla de 30 x 3; solo cambia por cuál
de los dos ejes se corta.

           evaluar    generar    verificar_tipos
Numero        .          .             .
Suma          .          .             .
Multiplic.    .          .             .
            ^^^^
            queremos ESTA columna en un archivo

Cortar por columnas en vez de por filas es, literalmente, todo el patrón
Visitor. Sigan con 02_visitor.py.
""")
