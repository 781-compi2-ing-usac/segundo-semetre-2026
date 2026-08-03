"""
MICRO-EJEMPLO 1: El entorno (Environment), sin PLY.

Objetivo: entender cómo un intérprete recuerda variables y por qué un
bloque anidado ve las variables de "afuera" pero afuera no ve las de
adentro. Esto es lo que en teoría llaman ámbito léxico (lexical scoping).

La idea completa cabe en una sola clase: un diccionario más un puntero al
entorno "padre".

Correr con: python3 01_entorno.py
"""


class Entorno:
    """Una tabla de variables, con un puntero opcional a su entorno padre.

    Cada bloque de código (el programa completo, el cuerpo de un `if`, el
    cuerpo de una función...) va a tener SU PROPIO `Entorno`. Cuando ese
    bloque termina, su entorno se descarta y las variables que declaró
    dejan de existir — así es como funciona el "scope".
    """

    def __init__(self, padre=None):
        self.variables = {}
        self.padre = padre

    def declarar(self, nombre, valor):
        # Declarar SIEMPRE crea la variable en ESTE entorno, nunca en el
        # padre. Si ya existía una variable con ese nombre en el padre, la
        # de aquí simplemente la tapa mientras estemos en este bloque —
        # eso es shadowing, y ya lo van a ver más abajo.
        self.variables[nombre] = valor

    def asignar(self, nombre, valor):
        """Cambia el valor de una variable que YA EXISTE.

        A diferencia de `declarar`, esto SÍ busca hacia arriba: si la
        variable no está en este entorno, hay que buscarla en el padre,
        porque quizás la declararon afuera y la estamos modificando desde
        un bloque anidado (piensen en `contador = contador + 1;` dentro de
        un `while`).
        """
        if nombre in self.variables:
            self.variables[nombre] = valor
            return True
        if self.padre is not None:
            return self.padre.asignar(nombre, valor)
        return False   # no existe en ningún entorno de la cadena

    def buscar(self, nombre):
        """Devuelve el valor de `nombre`, buscando hacia arriba si hace falta."""
        if nombre in self.variables:
            return self.variables[nombre]
        if self.padre is not None:
            return self.padre.buscar(nombre)
        raise NameError(f"variable no declarada: {nombre!r}")


if __name__ == '__main__':
    # Vamos a simular esto, sin parser, armando los entornos a mano:
    #
    #   programa:
    #       let x = 10;
    #       begin                  <- un bloque anidado
    #           let y = 20;
    #           x = 99;            <- modifica la x de AFUERA
    #           print(x, y);       <- ve las dos: 99, 20
    #       end
    #       print(x);              <- solo ve x (99). y ya no existe aquí.

    global_ = Entorno()                 # el entorno del programa completo
    global_.declarar('x', 10)

    bloque = Entorno(padre=global_)     # el entorno del `begin ... end` anidado
    bloque.declarar('y', 20)

    print("Dentro del bloque anidado:")
    bloque.asignar('x', 99)             # no está en `bloque`, sube al padre
    print(f"  x = {bloque.buscar('x')}")  # 99 (subió a buscarla en global_)
    print(f"  y = {bloque.buscar('y')}")  # 20 (está aquí mismo)

    print("\nDe vuelta en el entorno global:")
    print(f"  x = {global_.buscar('x')}")  # 99: el cambio sí se ve, porque
                                            # `asignar` modificó la variable
                                            # real, no una copia

    try:
        global_.buscar('y')
    except NameError as error:
        print(f"  y -> {error}")   # 'y' no existe aquí: bloque ya se cerró

    # ---------------------------------------------------------------
    # Shadowing: declarar una variable con el mismo nombre que una de
    # afuera. NO es lo mismo que asignar.
    # ---------------------------------------------------------------
    print("\nShadowing:")
    otro_bloque = Entorno(padre=global_)
    otro_bloque.declarar('x', 'soy la x de adentro')   # tapa a la de afuera
    print(f"  dentro del bloque:  x = {otro_bloque.buscar('x')!r}")
    print(f"  en el global:       x = {global_.buscar('x')!r}")  # sin tocar

    # ---------------------------------------------------------------
    # Para su proyecto:
    #
    # - `declarar` es lo que usan cuando procesan un `let`/`var`.
    # - `asignar` es lo que usan cuando procesan un `x = valor;` (SIN `let`).
    # - Si `asignar` devuelve False, ahí es donde reportan el error
    #   semántico "variable no declarada" — NO dejen que se interrumpa con
    #   NameError como hace `buscar` en este ejemplo.
    # - Cada `Bloque.ejecutar` de la Sesión 1 va a necesitar crear un
    #   `Entorno(padre=entorno)` nuevo antes de ejecutar sus instrucciones.
    #   Busquen el comentario "LO QUE FALTA AQUÍ" en `ast_nodes.py`.
    # ---------------------------------------------------------------
