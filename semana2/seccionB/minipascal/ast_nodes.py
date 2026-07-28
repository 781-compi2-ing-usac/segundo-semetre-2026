"""
MiniPascal v1 — Nodos del AST (patrón Intérprete).

Aquí vive TODA la lógica de ejecución del lenguaje. El parser no calcula
nada: solo construye estos objetos.

La jerarquía es:

    Nodo                 (guarda línea y columna — todos los nodos)
     ├── Expresion       -> tiene evaluar(entorno), DEVUELVE un valor
     │    ├── Literal
     │    ├── Aritmetica
     │    └── Negacion
     └── Instruccion     -> tiene ejecutar(entorno), HACE algo
          ├── Writeln
          └── Bloque

Esa división entre "devuelve un valor" y "hace algo" es la que más se les
va a repetir en el proyecto. Una expresión (`2 + 3`) produce un valor. Una
instrucción (`writeln(...)`) produce un efecto.
"""

from abc import ABC, abstractmethod


class Nodo(ABC):
    """Base de todo el AST.

    Todos los nodos guardan dónde aparecieron en el código fuente. En v1
    todavía no reportamos errores, así que parece información inútil — pero
    en la Sesión 2 cada error va a necesitar decir "Línea X, Columna Y", y
    para entonces ya no hay dónde sacar ese dato: el texto original ya se
    procesó y los tokens ya se consumieron.

    Guárdenlo desde el primer día. Agregarlo después significa tocar todas
    las clases del AST y todas las reglas del parser de un solo golpe.
    """

    def __init__(self, linea, columna):
        self.linea = linea
        self.columna = columna

    def __repr__(self):
        # Sin esto, `print(nodo)` muestra algo como
        # <ast_nodes.Programa object at 0x7f3a...>, que no sirve para nada.
        # Van a estar imprimiendo nodos todo el semestre: háganse el favor.
        return f"{type(self).__name__}(línea {self.linea}, col {self.columna})"


# ---------------------------------------------------------------------------
# EXPRESIONES — producen un valor
# ---------------------------------------------------------------------------

class Expresion(Nodo):

    @abstractmethod
    def evaluar(self, entorno):
        """Calcula el valor de esta expresión y lo devuelve."""
        ...


class Literal(Expresion):
    """Un valor escrito directamente en el código: 42, 3.14, 'hola', true."""

    def __init__(self, valor, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor

    def evaluar(self, entorno):
        # Una hoja del árbol. No hay nada que calcular.
        return self.valor


class Aritmetica(Expresion):
    """Operación binaria: izquierdo <operador> derecho."""

    def __init__(self, izquierdo, operador, derecho, linea, columna):
        super().__init__(linea, columna)
        self.izquierdo = izquierdo
        self.operador = operador
        self.derecho = derecho

    def evaluar(self, entorno):
        # El corazón del patrón Intérprete: para calcularme, primero les
        # pido a mis hijos que se calculen. No pregunto QUÉ son. Puede que
        # `self.izquierdo` sea un Literal, otra Aritmetica o una Negacion:
        # me basta con que sepan responder a `evaluar()`.
        izq = self.izquierdo.evaluar(entorno)
        der = self.derecho.evaluar(entorno)

        if self.operador == '+':
            return izq + der
        if self.operador == '-':
            return izq - der
        if self.operador == '*':
            return izq * der
        if self.operador == '/':
            # En Pascal `/` siempre da real, aunque los dos operandos sean
            # enteros: 10 / 2 es 5.0, no 5.
            return izq / der

        raise ValueError(f"Operador desconocido: {self.operador}")

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ (Sesión 2):
        #
        # Este método asume que la operación siempre es válida y deja que
        # Python decida el resultado. Prueben `writeln('hola' - 1);` y
        # verán reventar el programa con un error de Python, no un mensaje
        # de error decente.
        #
        # Su proyecto necesita, ANTES de operar:
        #   1. averiguar el tipo de `izq` y de `der`
        #   2. consultar la tabla de tipos resultantes del enunciado
        #   3. si la combinación no es válida: reportar el error semántico
        #      con su línea y columna, devolver None, y seguir ejecutando
        # ------------------------------------------------------------------


class Negacion(Expresion):
    """Menos unario: -x"""

    def __init__(self, expresion, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion

    def evaluar(self, entorno):
        return -self.expresion.evaluar(entorno)


# ---------------------------------------------------------------------------
# INSTRUCCIONES — producen un efecto
# ---------------------------------------------------------------------------

class Instruccion(Nodo):

    @abstractmethod
    def ejecutar(self, entorno):
        """Realiza la acción de esta instrucción. No devuelve un valor."""
        ...


class Writeln(Instruccion):
    """writeln(expresion);  — imprime y salta de línea."""

    def __init__(self, expresion, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion

    def ejecutar(self, entorno):
        # Una instrucción puede contener expresiones. Aquí se ve el cruce
        # entre las dos jerarquías: `ejecutar` llama a `evaluar`.
        valor = self.expresion.evaluar(entorno)
        print(formatear(valor))


class Bloque(Instruccion):
    """begin <instrucciones> end

    Un bloque es una lista de instrucciones, y a la vez ES una instrucción.
    Por eso puede aparecer anidado dentro de otro bloque.
    """

    def __init__(self, instrucciones, linea, columna):
        super().__init__(linea, columna)
        self.instrucciones = instrucciones

    def ejecutar(self, entorno):
        for instruccion in self.instrucciones:
            instruccion.ejecutar(entorno)

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ (Sesión 2):
        #
        # En un lenguaje de verdad, un bloque abre un ÁMBITO nuevo: las
        # variables declaradas adentro no existen afuera. Eso se hace
        # creando un entorno hijo antes del `for`:
        #
        #     entorno_local = Entorno(padre=entorno)
        #     for instruccion in self.instrucciones:
        #         instruccion.ejecutar(entorno_local)
        #
        # Todavía no lo hacemos porque v1 no tiene variables. Fíjense que
        # el parámetro `entorno` ya viaja por todos los métodos justamente
        # para que ese cambio sea de una línea cuando llegue el momento.
        # ------------------------------------------------------------------


class Programa(Nodo):
    """program <nombre>; <bloque> .  — la raíz del árbol."""

    def __init__(self, nombre, bloque, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.bloque = bloque

    def ejecutar(self, entorno):
        self.bloque.ejecutar(entorno)


# ---------------------------------------------------------------------------

def formatear(valor):
    """Convierte un valor de MiniPascal a texto para imprimirlo.

    Existe porque Python imprime los booleanos como `True`/`False` y en
    Pascal se escriben en minúscula. Su proyecto va a necesitar algo
    parecido: cómo se imprime un valor es decisión del lenguaje que están
    implementando, no de Python.
    """
    if isinstance(valor, bool):
        return 'true' if valor else 'false'
    return str(valor)
