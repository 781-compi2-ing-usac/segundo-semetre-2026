"""
MICRO-EJEMPLO 1: El patrón Intérprete, sin PLY.

Objetivo: entender que el patrón Intérprete NO tiene nada que ver con PLY.
Es simplemente esto: cada nodo del árbol es una clase, y cada clase sabe
calcularse a sí misma con un método `evaluar()`.

Aquí armamos el árbol a mano, con constructores. En el intérprete de verdad
(carpeta minipascal/) ese mismo árbol lo va a construir el parser, pero las
clases son idénticas.

Correr con: python 01_interprete_a_mano.py
"""

from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# La clase base. `ABC` + `@abstractmethod` obligan a que TODA expresión
# implemente `evaluar()`. Si se olvidan de implementarlo en una subclase,
# Python revienta al instanciarla en vez de fallar raro en tiempo de ejecución.
# ---------------------------------------------------------------------------
class Expresion(ABC):

    @abstractmethod
    def evaluar(self):
        """Calcula el valor de esta expresión y lo devuelve."""
        ...


class Numero(Expresion):
    """Una hoja del árbol: un número literal. Ya trae su valor."""

    def __init__(self, valor):
        self.valor = valor

    def evaluar(self):
        # Un literal no tiene nada que calcular: se devuelve a sí mismo.
        return self.valor


class Suma(Expresion):
    """Un nodo interno: tiene dos hijos que también son expresiones."""

    def __init__(self, izquierdo, derecho):
        self.izquierdo = izquierdo
        self.derecho = derecho

    def evaluar(self):
        # Aquí está la idea central del patrón: para calcularme, primero le
        # pido a mis hijos que se calculen. No me importa QUÉ son mis hijos
        # (un número, otra suma, una multiplicación...), solo que saben
        # responder a `evaluar()`. Esto es recursión sobre el árbol.
        return self.izquierdo.evaluar() + self.derecho.evaluar()


class Multiplicacion(Expresion):

    def __init__(self, izquierdo, derecho):
        self.izquierdo = izquierdo
        self.derecho = derecho

    def evaluar(self):
        return self.izquierdo.evaluar() * self.derecho.evaluar()


if __name__ == '__main__':
    # Vamos a representar la expresión:  2 + 3 * 4
    #
    # Como un árbol se ve así:
    #
    #         Suma
    #        /    \
    #    Numero   Multiplicacion
    #      (2)      /       \
    #           Numero    Numero
    #             (3)       (4)
    #
    # Fíjense que el árbol YA tiene la precedencia resuelta: la
    # multiplicación quedó más abajo, así que se evalúa primero. La
    # precedencia es una propiedad de la FORMA del árbol, no del método
    # `evaluar()`. Por eso el parser es quien tiene que armarlo bien.

    arbol = Suma(
        Numero(2),
        Multiplicacion(Numero(3), Numero(4)),
    )

    print("Expresión representada: 2 + 3 * 4")
    print(f"Resultado: {arbol.evaluar()}")   # 14, no 20

    # Y si el árbol tuviera otra forma, el resultado cambia:
    #
    #          Multiplicacion
    #          /            \
    #       Suma          Numero
    #      /    \           (4)
    #  Numero  Numero
    #    (2)     (3)

    otro = Multiplicacion(
        Suma(Numero(2), Numero(3)),
        Numero(4),
    )

    print("\nExpresión representada: (2 + 3) * 4")
    print(f"Resultado: {otro.evaluar()}")    # 20

    # ---------------------------------------------------------------
    # Lo importante:
    #
    # 1. Ningún `if` pregunta "¿qué tipo de nodo eres?". Cada clase sabe
    #    lo suyo. Agregar una resta = agregar una clase, sin tocar las
    #    demás. Eso es el patrón Intérprete.
    #
    # 2. `evaluar()` no sabe nada de tokens, ni de gramáticas, ni de PLY.
    #    El árbol es independiente de cómo se construyó.
    #
    # 3. En su proyecto van a necesitar DOS métodos, no uno:
    #       - las expresiones devuelven un valor  -> `evaluar()`
    #       - las instrucciones hacen algo        -> `ejecutar()`
    #    Eso se ve en la carpeta minipascal/.
    # ---------------------------------------------------------------
