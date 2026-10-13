"""
MiniPascal v2 — Lista de errores.

El enunciado pide (sección 3.4.1) que el intérprete NO se detenga en el
primer error semántico: debe seguir analizando y ejecutando todo lo que
pueda, y al final mostrar TODOS los errores encontrados.

Para lograr eso, un nodo del AST que detecta un problema (una variable no
declarada, una operación entre tipos incompatibles...) no puede lanzar una
excepción de Python: eso destruiría la pila de llamadas y detendría todo,
exactamente lo que NO queremos.

En vez de eso, el nodo AGREGA el error a esta lista y devuelve `None` (o,
si es una instrucción, simplemente no hace nada). El programa sigue
corriendo con ese `None` dando vueltas, y al final imprimimos la lista
completa.
"""


class ListaErrores:

    def __init__(self):
        self.errores = []

    def agregar(self, tipo, descripcion, linea, columna):
        """`tipo` es uno de: 'Léxico', 'Sintáctico', 'Semántico'."""
        self.errores.append({
            'tipo': tipo,
            'descripcion': descripcion,
            'linea': linea,
            'columna': columna,
        })

    def hay_errores(self):
        return len(self.errores) > 0

    def imprimir(self):
        if not self.hay_errores():
            print("Sin errores semánticos.")
            return

        for error in self.errores:
            # Mismo formato que pide el enunciado:
            #   [Tipo de Error] Línea <línea>, Columna <columna>
            #   Descripción del error.
            print(f"[Error {error['tipo']}] Línea {error['linea']}, "
                  f"Columna {error['columna']}")
            print(f"  {error['descripcion']}")


if __name__ == '__main__':
    # Simulación rápida de cómo la va a usar un nodo del AST.
    errores = ListaErrores()

    errores.agregar('Semántico', "La variable 'total' no ha sido declarada.", 3, 15)
    errores.agregar('Semántico', "No es posible modificar la variable 'PI' porque es inmutable.", 7, 5)

    print(f"¿Hubo errores? {errores.hay_errores()}\n")
    errores.imprimir()

    # ---------------------------------------------------------------
    # Para su proyecto: esta MISMA lista es la que después van a
    # recorrer para generar el reporte de errores en HTML (sección
    # 3.4.1 del enunciado). Por ahora solo la imprimimos por consola —
    # el reporte en HTML lo dejamos para más adelante, cuando también
    # tengan el reporte de tabla de símbolos y de AST para entregar
    # los tres juntos.
    #
    # También noten que `ListaErrores` no sabe NADA de PLY, de nodos del
    # AST, ni de MiniPascal. Es una clase completamente genérica: solo
    # junta diccionarios. Toda la inteligencia de CUÁNDO reportar un
    # error vive en los nodos que la usan.
    # ---------------------------------------------------------------
