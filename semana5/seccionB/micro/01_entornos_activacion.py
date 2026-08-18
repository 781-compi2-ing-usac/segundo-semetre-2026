"""
MICRO-EJEMPLO 1: Entornos de activación, sin PLY.

Objetivo: entender de qué entorno debe "colgar" el entorno de activación
de una función al llamarla, y por qué la respuesta NO es "el entorno de
quien la está llamando en este momento" — aunque esa sea la respuesta
intuitiva la primera vez que uno lo piensa.

La pregunta con trampa: si una función `f` fue declarada afuera, con una
variable global `version`, pero se LLAMA desde adentro de otra función `g`
que tiene su PROPIA variable local `version`, ¿cuál `version` debería ver
`f` al ejecutarse?

  - Si `f` ve la de `g` (la de quien la llamó): eso es scoping DINÁMICO.
  - Si `f` ve la global (la que existía donde `f` fue declarada): eso es
    scoping ESTÁTICO (o léxico).

Todos los lenguajes de propósito general modernos —incluido Rust, la base
de OxigenScript— usan scoping ESTÁTICO. Y el mecanismo que lo logra es
simple una vez que se ve: cada función recuerda el entorno donde fue
DECLARADA, y cada llamada cuelga su entorno de activación de ESE entorno,
nunca del entorno de quien llama. Es lo mismo que un cierre (closure) en
Python o JavaScript.

Correr con: python3 01_entornos_activacion.py
"""


class Entorno:
    """Versión mínima del Entorno real (entorno.py): diccionario + padre."""

    def __init__(self, padre=None):
        self.variables = {}
        self.padre = padre

    def declarar(self, nombre, valor):
        self.variables[nombre] = valor

    def buscar(self, nombre):
        if nombre in self.variables:
            return self.variables[nombre]
        return self.padre.buscar(nombre)


class Funcion:
    """Simula el nodo Funcion de minipascal/ast_nodes.py: guarda su cuerpo
    (aquí, una función de Python en vez de un Bloque del AST) y el entorno
    donde fue DECLARADA — inicialmente desconocido (None)."""

    def __init__(self, nombre, cuerpo):
        self.nombre = nombre
        self.cuerpo = cuerpo
        self.entorno_definicion = None


def declarar(entorno, funcion):
    """Simula Funcion.ejecutar: registra la función Y recuerda dónde vive."""
    funcion.entorno_definicion = entorno
    entorno.declarar(funcion.nombre, funcion)


def llamar(funcion, argumentos):
    """Simula Llamada.evaluar — LA FORMA CORRECTA.

    El entorno de activación cuelga de `funcion.entorno_definicion`. No
    recibe el entorno de quien llama para nada relacionado con esto (en el
    intérprete real sí lo recibe, pero solo para evaluar las expresiones
    de los ARGUMENTOS antes de esta llamada — una vez adentro, no se
    vuelve a tocar).
    """
    activacion = Entorno(padre=funcion.entorno_definicion)
    for nombre, valor in argumentos.items():
        activacion.declarar(nombre, valor)
    return funcion.cuerpo(activacion)


def llamar_con_el_bug(funcion, argumentos, entorno_de_quien_llama):
    """La misma idea, pero con el error fácil de cometer: cuelga del
    entorno de QUIEN LLAMA en vez del entorno de definición."""
    activacion = Entorno(padre=entorno_de_quien_llama)
    for nombre, valor in argumentos.items():
        activacion.declarar(nombre, valor)
    return funcion.cuerpo(activacion)


if __name__ == '__main__':
    # -----------------------------------------------------------------
    # Demo 1: scoping estático vs. dinámico
    # -----------------------------------------------------------------
    print("Demo 1: scoping estático vs. dinámico\n")

    global_ = Entorno()
    global_.declarar('version', 100)

    def cuerpo_leer_version(activacion):
        return activacion.buscar('version')

    leer_version = Funcion('leerVersion', cuerpo_leer_version)
    declarar(global_, leer_version)

    # quienLlama() tiene su PROPIA 'version' = 999. Con scoping estático,
    # eso NO debería filtrarse a leerVersion() cuando la llama.
    entorno_quien_llama = Entorno(padre=global_)
    entorno_quien_llama.declarar('version', 999)

    resultado_correcto = llamar(leer_version, {})
    resultado_con_bug = llamar_con_el_bug(leer_version, {}, entorno_quien_llama)

    print(f"  llamar()            -> leerVersion() = {resultado_correcto}   (correcto: ve la global, 100)")
    print(f"  llamar_con_el_bug()  -> leerVersion() = {resultado_con_bug}   (bug: 've' el 999 de quien llamó)")
    print("\n  El bug no revienta nada — el programa corre y da un número.")
    print("  Por eso es peligroso: no hay ningún error que los avise.\n")

    # -----------------------------------------------------------------
    # Demo 2: recursión — factorial se encuentra a sí misma
    # -----------------------------------------------------------------
    print("Demo 2: recursión (factorial)\n")

    def cuerpo_factorial(activacion):
        n = activacion.buscar('n')
        if n <= 1:
            return 1
        funcion_factorial = activacion.buscar('factorial')
        return n * llamar(funcion_factorial, {'n': n - 1})

    factorial = Funcion('factorial', cuerpo_factorial)
    declarar(global_, factorial)

    resultado = llamar(factorial, {'n': 5})
    print(f"  factorial(5) = {resultado}")
    print("  Cada llamada recursiva crea su PROPIA activación (con su propia")
    print("  'n'), pero todas cuelgan del MISMO entorno de definición — por")
    print("  eso todas encuentran 'factorial' al buscarse a sí mismas, sin")
    print("  importar cuántos niveles de profundidad lleve la recursión.")

    # -------------------------------------------------------------------
    # Para su proyecto:
    #
    # - `Funcion.ejecutar` (ast_nodes.py) guarda
    #   `self.entorno_definicion = entorno` al declararse — exactamente lo
    #   que hace `declarar()` aquí arriba.
    # - `Llamada.evaluar` (ast_nodes.py) arma el entorno de activación con
    #   `padre=funcion.entorno_definicion` — exactamente lo que hace
    #   `llamar()` aquí arriba.
    # - El bug de `llamar_con_el_bug` es fácil de cometer sin darse cuenta:
    #   basta con escribir `Entorno(padre=entorno)` (el entorno de QUIEN
    #   LLAMA) en vez de `Entorno(padre=funcion.entorno_definicion)` dentro
    #   de `Llamada`, y el intérprete sigue corriendo — solo empieza a dar
    #   resultados mal en casos de anidamiento, que son los más difíciles
    #   de depurar porque no hay ningún mensaje de error que los delate.
    # -------------------------------------------------------------------
