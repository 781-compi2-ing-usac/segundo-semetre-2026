"""
MiniPascal v6 — Nodos del AST (patrón VISITOR).

Esto es lo que cambió esta semana, y es TODO lo que cambió del árbol:

    ANTES (todo el Proyecto 1, patrón Intérprete)
    ---------------------------------------------
    class Literal(Expresion):
        def __init__(self, valor, linea, columna): ...
        def evaluar(self, entorno, errores, tabla):
            return self.valor                       <- la lógica, aquí adentro

    AHORA (Proyecto 2, patrón Visitor)
    ----------------------------------
    class Literal(Expresion):
        def __init__(self, valor, linea, columna): ...
        def aceptar(self, v):
            return v.visitar_Literal(self)          <- la lógica, en otro lado


Los nodos ya no SABEN HACER nada. Solo saben qué son y quiénes son sus
hijos. Toda la lógica se fue a los visitantes:

    interprete.py     recorre el árbol y EJECUTA
    generador_arm.py  recorre el árbol y ESCRIBE ENSAMBLADOR

Los dos recorren EXACTAMENTE este mismo árbol, sin tocar ni una línea de
este archivo. Ese es el punto entero del patrón, y la razón por la que su
Proyecto 2 lo necesita: el Proyecto 1 tenía un solo recorrido (ejecutar),
el Proyecto 2 tiene por lo menos dos (ejecutar y generar), y muy
probablemente tres (más adelante, verificar tipos).


¿Por qué `aceptar` no hace `v.visitar(self)` y ya?
--------------------------------------------------
Porque Python tendría que averiguar en tiempo de ejecución cuál de los 30
`visitar_X` corresponde. Al escribir `v.visitar_Literal(self)` DENTRO de
`Literal`, la clase ya se conoce a sí misma: el nombre del método queda
resuelto sin ningún `if` ni ningún `isinstance`.

A eso se le llama DOBLE DESPACHO, y es el mecanismo del patrón:

    1. `nodo.aceptar(visitante)`   -> el primer despacho elige el NODO
    2. `v.visitar_Literal(nodo)`   -> el segundo despacho elige el VISITANTE

Dos decisiones, una por cada eje. Por eso funciona agregar visitantes sin
tocar nodos.


El precio del patrón (esto también hay que decirlo)
---------------------------------------------------
Agregar un RECORRIDO nuevo es baratísimo: un archivo nuevo, cero cambios
aquí. Pero agregar un NODO nuevo es más caro que antes: hay que tocar
este archivo Y todos los visitantes que existan.

Es un intercambio deliberado. En un compilador uno agrega recorridos
seguido (ejecutar, generar, verificar tipos, optimizar) y nodos casi
nunca, porque la gramática se estabiliza temprano. Por eso conviene.


Qué NO cambió
-------------
La jerarquía es la misma de la Sesión 5, con las mismas clases y los
mismos constructores. `parser.py` no cambió ni una línea: sigue armando
los mismos nodos. Si hacen `diff` contra semana6/seccionB/minipascal/
van a ver que la única diferencia real es "se fue la lógica".

Los VALORES en tiempo de ejecución (VistaArreglo, formatear, los tipos)
se mudaron a `valores.py`. Este archivo ya no sabe nada de valores — solo
de formas. Lean el encabezado de `valores.py`: esa separación es la idea
central del Proyecto 2.
"""

from abc import ABC, abstractmethod


class Nodo(ABC):
    """Base de todo el AST. Ver semana2/seccionB para la explicación completa."""

    def __init__(self, linea, columna):
        self.linea = linea
        self.columna = columna

    @abstractmethod
    def aceptar(self, v):
        """Le dice al visitante `v` cuál de sus métodos corresponde a este nodo.

        Una sola línea en cada subclase, siempre con la misma forma:
        `return v.visitar_<NombreDeLaClase>(self)`.
        """
        ...

    def __repr__(self):
        return f"{type(self).__name__}(línea {self.linea}, col {self.columna})"


# ---------------------------------------------------------------------------
# EXPRESIONES — el visitante devuelve algo al visitarlas
#
#   en el intérprete  -> un valor  (14)
#   en el generador   -> nada; deja el resultado en la pila del ensamblador
# ---------------------------------------------------------------------------

class Expresion(Nodo):
    pass


class Literal(Expresion):
    """Un valor escrito directamente en el código: 42, 3.14, 'hola', true."""

    def __init__(self, valor, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor

    def aceptar(self, v):
        return v.visitar_Literal(self)


class Variable(Expresion):
    """Uso de un identificador dentro de una expresión: la `x` en `x + 1`.
    NO confundir con `Declaracion`, que es la instrucción que la crea.
    """

    def __init__(self, nombre, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre

    def aceptar(self, v):
        return v.visitar_Variable(self)


class Aritmetica(Expresion):
    """Operación binaria: izquierdo <operador> derecho."""

    def __init__(self, izquierdo, operador, derecho, linea, columna):
        super().__init__(linea, columna)
        self.izquierdo = izquierdo
        self.operador = operador
        self.derecho = derecho

    def aceptar(self, v):
        return v.visitar_Aritmetica(self)


class Negacion(Expresion):
    """Menos unario: -x"""

    def __init__(self, expresion, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion

    def aceptar(self, v):
        return v.visitar_Negacion(self)


class Comparacion(Expresion):
    """Operador relacional: izquierdo (== != < > <= >=) derecho."""

    def __init__(self, izquierdo, operador, derecho, linea, columna):
        super().__init__(linea, columna)
        self.izquierdo = izquierdo
        self.operador = operador
        self.derecho = derecho

    def aceptar(self, v):
        return v.visitar_Comparacion(self)


class Llamada(Expresion):
    """nombre(argumentos) — llamar una función declarada, o una embebida."""

    def __init__(self, nombre, argumentos, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.argumentos = argumentos   # lista de Expresion

    def aceptar(self, v):
        return v.visitar_Llamada(self)


class Slice(Expresion):
    """&nombre[inicio..fin] — una VISTA sobre una porción de un arreglo."""

    def __init__(self, nombre, inicio, fin, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.inicio = inicio   # Expresion
        self.fin = fin         # Expresion

    def aceptar(self, v):
        return v.visitar_Slice(self)


class Indexado(Expresion):
    """nombre[indice] — leer una casilla de un arreglo (o de un slice)."""

    def __init__(self, nombre, indice, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.indice = indice

    def aceptar(self, v):
        return v.visitar_Indexado(self)


class AccesoCampo(Expresion):
    """objeto.campo — leer un campo de un registro."""

    def __init__(self, nombre_objeto, nombre_campo, linea, columna):
        super().__init__(linea, columna)
        self.nombre_objeto = nombre_objeto
        self.nombre_campo = nombre_campo

    def aceptar(self, v):
        return v.visitar_AccesoCampo(self)


# ---------------------------------------------------------------------------
# INSTRUCCIONES — el visitante NO devuelve nada al visitarlas
# ---------------------------------------------------------------------------

class Instruccion(Nodo):
    pass


class Writeln(Instruccion):
    """writeln(expresion); — imprime y salta de línea."""

    def __init__(self, expresion, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion

    def aceptar(self, v):
        return v.visitar_Writeln(self)


class Declaracion(Instruccion):
    """var nombre: tipo [:= expresion];   o   const nombre: tipo := expresion;"""

    def __init__(self, nombre, tipo, expresion_inicial, constante, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tipo = tipo
        self.expresion_inicial = expresion_inicial   # puede ser None
        self.constante = constante

    def aceptar(self, v):
        return v.visitar_Declaracion(self)


class DeclaracionInferida(Instruccion):
    """var nombre := expresion;   (SIN anotación de tipo)

    El único caso donde MiniPascal permite `var` sin `: tipo`. Hace falta
    porque un slice no tiene una palabra de tipo que se pueda escribir de
    antemano. Ver semana6/seccionB/micro/02_slices.py.
    """

    def __init__(self, nombre, expresion, constante, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.expresion = expresion
        self.constante = constante

    def aceptar(self, v):
        return v.visitar_DeclaracionInferida(self)


class DeclaracionArreglo(Instruccion):
    """var nombre: array[tamano] of tipo;"""

    def __init__(self, nombre, tamano, tipo_elemento, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tamano = tamano
        self.tipo_elemento = tipo_elemento

    def aceptar(self, v):
        return v.visitar_DeclaracionArreglo(self)


class Asignacion(Instruccion):
    """nombre := expresion;   (SIN `var`/`const`: la variable ya existía)"""

    def __init__(self, nombre, expresion, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.expresion = expresion

    def aceptar(self, v):
        return v.visitar_Asignacion(self)


class AsignacionIndexada(Instruccion):
    """nombre[indice] := expresion;"""

    def __init__(self, nombre, indice, expresion, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.indice = indice
        self.expresion = expresion

    def aceptar(self, v):
        return v.visitar_AsignacionIndexada(self)


class AsignacionCampo(Instruccion):
    """objeto.campo := expresion;"""

    def __init__(self, nombre_objeto, nombre_campo, expresion, linea, columna):
        super().__init__(linea, columna)
        self.nombre_objeto = nombre_objeto
        self.nombre_campo = nombre_campo
        self.expresion = expresion

    def aceptar(self, v):
        return v.visitar_AsignacionCampo(self)


class Bloque(Instruccion):
    """begin <instrucciones> end"""

    def __init__(self, instrucciones, linea, columna):
        super().__init__(linea, columna)
        self.instrucciones = instrucciones

    def aceptar(self, v):
        return v.visitar_Bloque(self)


class If(Instruccion):
    """if <condicion> then <bloque_si> [else <bloque_no>];"""

    def __init__(self, condicion, bloque_si, bloque_no, linea, columna):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.bloque_si = bloque_si
        self.bloque_no = bloque_no

    def aceptar(self, v):
        return v.visitar_If(self)


class While(Instruccion):
    """[etiqueta:] while <condicion> do <cuerpo>;"""

    def __init__(self, condicion, cuerpo, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.cuerpo = cuerpo
        self.etiqueta = etiqueta

    def aceptar(self, v):
        return v.visitar_While(self)


class Repeat(Instruccion):
    """repeat <instrucciones> until <condicion>;"""

    def __init__(self, instrucciones, condicion, linea, columna):
        super().__init__(linea, columna)
        self.instrucciones = instrucciones
        self.condicion = condicion

    def aceptar(self, v):
        return v.visitar_Repeat(self)


class RamaCase(Nodo):
    """Una rama de `case`: valor: bloque.

    No es Expresion ni Instruccion — es una pieza auxiliar de `Case`. Aun
    así lleva `aceptar`, para que `dot.py` la siga dibujando y para que
    ningún nodo del árbol quede fuera del patrón.
    """

    def __init__(self, valor, bloque, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor
        self.bloque = bloque

    def aceptar(self, v):
        return v.visitar_RamaCase(self)


class Case(Instruccion):
    """case <selector> of <ramas> [else <bloque_por_defecto>] end;"""

    def __init__(self, selector, ramas, bloque_por_defecto, linea, columna):
        super().__init__(linea, columna)
        self.selector = selector
        self.ramas = ramas
        self.bloque_por_defecto = bloque_por_defecto

    def aceptar(self, v):
        return v.visitar_Case(self)


class Break(Instruccion):
    """break; o break etiqueta;"""

    def __init__(self, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta

    def aceptar(self, v):
        return v.visitar_Break(self)


class Continue(Instruccion):
    """continue; o continue etiqueta;"""

    def __init__(self, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta

    def aceptar(self, v):
        return v.visitar_Continue(self)


class Parametro(Nodo):
    """Un parámetro de función (o un campo de record): nombre y tipo."""

    def __init__(self, nombre, tipo, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tipo = tipo

    def aceptar(self, v):
        return v.visitar_Parametro(self)


class Funcion(Instruccion):
    """function nombre(parametros): tipo_retorno; cuerpo;

    Ojo con lo que YA NO está aquí: el atributo `entorno_definicion`. En
    la Sesión 5 este nodo se guardaba a sí mismo el entorno donde había
    sido declarado, y `ejecutar()` se lo rellenaba.

    Con Visitor eso se vuelve un error de diseño: el mismo árbol lo van a
    recorrer dos visitantes distintos, y un nodo que guarda resultados de
    una pasada anterior deja de describir el programa y pasa a describir
    una ejecución. Ahora el intérprete guarda un `FuncionValor`
    (declaración + entorno) en el entorno — ver `valores.py`.

    Regla general que les va a servir todo el Proyecto 2:
    **un nodo del AST nunca debe guardar nada que dependa de haberse
    ejecutado.**
    """

    def __init__(self, nombre, parametros, tipo_retorno, cuerpo, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.parametros = parametros   # lista de Parametro
        self.tipo_retorno = tipo_retorno
        self.cuerpo = cuerpo           # Bloque

    def aceptar(self, v):
        return v.visitar_Funcion(self)


class Return(Instruccion):
    """return expresion;"""

    def __init__(self, expresion, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion

    def aceptar(self, v):
        return v.visitar_Return(self)


class TipoRegistro(Instruccion):
    """type Nombre = record campo1: tipo1; ... end;

    Simplificación deliberada de la Sesión 5, que sigue vigente: un campo
    solo puede ser de un tipo primitivo, nunca de otro `record`.
    """

    def __init__(self, nombre, campos, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.campos = campos   # lista de Parametro (mismo par nombre+tipo)

    def aceptar(self, v):
        return v.visitar_TipoRegistro(self)


class DeclaracionRegistro(Instruccion):
    """var nombre: NombreDeTipo;   (NombreDeTipo declarado con TipoRegistro)"""

    def __init__(self, nombre, nombre_tipo, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.nombre_tipo = nombre_tipo

    def aceptar(self, v):
        return v.visitar_DeclaracionRegistro(self)


class Programa(Nodo):
    """program <nombre>; <bloque> .  — la raíz del árbol."""

    def __init__(self, nombre, bloque, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.bloque = bloque

    def aceptar(self, v):
        return v.visitar_Programa(self)
