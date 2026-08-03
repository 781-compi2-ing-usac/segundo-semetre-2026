"""
MiniPascal v2 — Nodos del AST (patrón Intérprete).

Aquí vive TODA la lógica de ejecución del lenguaje. El parser no calcula
nada: solo construye estos objetos.

La jerarquía es:

    Nodo                 (guarda línea y columna — todos los nodos)
     ├── Expresion       -> evaluar(entorno, errores)         DEVUELVE un valor
     │    ├── Literal
     │    ├── Variable
     │    ├── Aritmetica
     │    └── Negacion
     └── Instruccion     -> ejecutar(entorno, errores, tabla) HACE algo
          ├── Writeln
          ├── Declaracion
          ├── Asignacion
          └── Bloque

Novedades de v2 frente a v1:

  - Los métodos reciben, además del `entorno`, una `ListaErrores`
    (`errores.py`). Ahora que hay variables, hay formas nuevas de
    equivocarse (usar una variable que no existe, modificar una
    constante...), y esos errores NO deben detener el programa — se
    reportan ahí y se sigue.
  - Las instrucciones reciben también una `TablaSimbolos` (para el
    reporte de símbolos). Solo `Declaracion` la usa de verdad; las demás
    solo la reenvían, igual que ya reenviaban el `entorno` en v1 sin
    necesitarlo todas.
  - `Bloque.ejecutar` por fin abre su propio ámbito, tal como decía el
    comentario "LO QUE FALTA AQUÍ" de la semana pasada.
"""

from abc import ABC, abstractmethod

from entorno import Entorno


class Nodo(ABC):
    """Base de todo el AST. Ver semana2/seccionB para la explicación completa."""

    def __init__(self, linea, columna):
        self.linea = linea
        self.columna = columna

    def __repr__(self):
        return f"{type(self).__name__}(línea {self.linea}, col {self.columna})"


# ---------------------------------------------------------------------------
# EXPRESIONES — producen un valor
# ---------------------------------------------------------------------------

class Expresion(Nodo):

    @abstractmethod
    def evaluar(self, entorno, errores):
        """Calcula el valor de esta expresión y lo devuelve.

        Si algo sale mal, agrega el error a `errores` y devuelve `None` —
        NUNCA lanza una excepción. Un `None` viajando hacia arriba es la
        señal de "aquí hubo un problema, ya se reportó, sigan sin usar
        este valor".
        """
        ...


class Literal(Expresion):
    """Un valor escrito directamente en el código: 42, 3.14, 'hola', true."""

    def __init__(self, valor, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor

    def evaluar(self, entorno, errores):
        # Una hoja del árbol. No hay nada que calcular ni que pueda fallar.
        return self.valor


class Variable(Expresion):
    """Uso de un identificador dentro de una expresión: por ejemplo, la
    `x` en `x + 1`. NO confundir con `Declaracion`, que es la instrucción
    que la crea (`var x: integer;`) — esta clase es solo LEERLA.
    """

    def __init__(self, nombre, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre

    def evaluar(self, entorno, errores):
        if not entorno.existe(self.nombre):
            errores.agregar(
                'Semántico',
                f"La variable '{self.nombre}' no ha sido declarada.",
                self.linea, self.columna,
            )
            return None
        return entorno.buscar(self.nombre)


# Tabla de tipos resultantes para `+`, igual que en
# micro/02_tabla_dominante.py, pero ahora conectada a errores de verdad en
# vez de un `print`. Solo cubrimos `+`: es el caso representativo. `-`, `*`
# y `/` siguen operando "a ciegas" más abajo — arréglenlos ustedes con el
# mismo patrón para su proyecto (y agreguen las suyas para %, ==, <, etc).
TIPOS_SUMA = {
    ('integer', 'integer'): 'integer',
    ('integer', 'real'):    'real',
    ('real',    'integer'): 'real',
    ('real',    'real'):    'real',
    ('string',  'string'):  'string',
}


def tipo_de_valor(valor):
    """Deriva el tipo de MiniPascal a partir de un valor de Python.

    Válido AQUÍ porque los tipos de MiniPascal (integer/real/boolean/
    string) coinciden 1 a 1 con tipos de Python (int/float/bool/str). Su
    proyecto no puede hacer lo mismo sin cuidado: i32 vs i64, o char vs
    String de un carácter, no tienen un tipo de Python distinto que los
    diferencie. El tipo de una variable en su proyecto debe venir de la
    declaración/inferencia, no de adivinar con `isinstance`.
    """
    if isinstance(valor, bool):
        return 'boolean'
    if isinstance(valor, int):
        return 'integer'
    if isinstance(valor, float):
        return 'real'
    if isinstance(valor, str):
        return 'string'
    return None


class Aritmetica(Expresion):
    """Operación binaria: izquierdo <operador> derecho."""

    def __init__(self, izquierdo, operador, derecho, linea, columna):
        super().__init__(linea, columna)
        self.izquierdo = izquierdo
        self.operador = operador
        self.derecho = derecho

    def evaluar(self, entorno, errores):
        izq = self.izquierdo.evaluar(entorno, errores)
        der = self.derecho.evaluar(entorno, errores)

        # Si algún hijo ya falló (y ya reportó su propio error), no tiene
        # sentido seguir: seguiríamos operando sobre un None y acabaríamos
        # apilando un segundo error encima del primero, que no aporta nada.
        if izq is None or der is None:
            return None

        if self.operador == '+':
            tipo_resultado = TIPOS_SUMA.get((tipo_de_valor(izq), tipo_de_valor(der)))
            if tipo_resultado is None:
                errores.agregar(
                    'Semántico',
                    f"No es posible aplicar el operador '+' entre los "
                    f"tipos {tipo_de_valor(izq)} y {tipo_de_valor(der)}.",
                    self.linea, self.columna,
                )
                return None
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
        # LO QUE FALTA AQUÍ:
        #
        # Solo `+` está protegido con tabla de tipos. `-`, `*` y `/` operan
        # igual que en v1: si los tipos no cuadran, Python revienta con su
        # propio error (vean el try/except de main.py). Repitan el mismo
        # patrón de `+` para las demás, y agreguen las tablas que les pide
        # el enunciado para cada operador (secciones 3.3.5 a 3.3.7).
        # ------------------------------------------------------------------


class Negacion(Expresion):
    """Menos unario: -x"""

    def __init__(self, expresion, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion

    def evaluar(self, entorno, errores):
        valor = self.expresion.evaluar(entorno, errores)
        if valor is None:
            return None
        return -valor


# ---------------------------------------------------------------------------
# INSTRUCCIONES — producen un efecto
# ---------------------------------------------------------------------------

class Instruccion(Nodo):

    @abstractmethod
    def ejecutar(self, entorno, errores, tabla):
        """Realiza la acción de esta instrucción. No devuelve un valor."""
        ...


class Writeln(Instruccion):
    """writeln(expresion);  — imprime y salta de línea."""

    def __init__(self, expresion, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion

    def ejecutar(self, entorno, errores, tabla):
        valor = self.expresion.evaluar(entorno, errores)
        if valor is None:
            # La expresión ya falló y ya quedó reportado en `errores`.
            # Imprimir "None" no le sirve a nadie, así que no imprimimos
            # nada — el programa sigue con la siguiente instrucción.
            return
        print(formatear(valor))


# Qué valor trae una variable declarada sin inicializar
# (`var contador: integer;`), tal como los pide la tabla de la sección
# 3.2.3 del enunciado.
VALORES_POR_DEFECTO = {
    'integer': 0,
    'real': 0.0,
    'boolean': False,
    'string': '',
}


class Declaracion(Instruccion):
    """var nombre: tipo [:= expresion];   o   const nombre: tipo := expresion;

    Es la única instrucción que toca a la vez `Entorno` (para poder USAR
    la variable mientras el programa corre) y `TablaSimbolos` (para que
    quede registrada en el reporte, aunque su ámbito ya haya cerrado
    cuando el programa termine). No las confundan.
    """

    def __init__(self, nombre, tipo, expresion_inicial, constante, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tipo = tipo
        self.expresion_inicial = expresion_inicial   # puede ser None
        self.constante = constante

    def ejecutar(self, entorno, errores, tabla):
        if self.expresion_inicial is not None:
            valor = self.expresion_inicial.evaluar(entorno, errores)
            if valor is None:
                # La expresión de inicialización falló. Igual declaramos
                # la variable (con su valor por defecto) para que el resto
                # del bloque pueda seguir usándola sin explotar por
                # "variable no declarada" encima del error que ya hubo.
                valor = VALORES_POR_DEFECTO.get(self.tipo)
        else:
            valor = VALORES_POR_DEFECTO.get(self.tipo)

        entorno.declarar(self.nombre, valor, tipo=self.tipo, constante=self.constante)

        tabla.registrar(
            nombre=self.nombre,
            categoria='Constante' if self.constante else 'Variable',
            tipo=self.tipo,
            ambito='programa',   # hasta que existan funciones (Sesión 4)
            linea=self.linea,
            valor=valor,
        )


class Asignacion(Instruccion):
    """nombre := expresion;   (SIN `var`/`const`: la variable ya existía)"""

    def __init__(self, nombre, expresion, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.expresion = expresion

    def ejecutar(self, entorno, errores, tabla):
        valor = self.expresion.evaluar(entorno, errores)
        if valor is None:
            return   # ya se reportó el error al evaluar la expresión

        if not entorno.existe(self.nombre):
            errores.agregar(
                'Semántico',
                f"La variable '{self.nombre}' no ha sido declarada.",
                self.linea, self.columna,
            )
            return

        if entorno.es_constante(self.nombre):
            errores.agregar(
                'Semántico',
                f"No es posible modificar la variable '{self.nombre}' "
                f"porque fue declarada como inmutable.",
                self.linea, self.columna,
            )
            return

        entorno.asignar(self.nombre, valor)


class Bloque(Instruccion):
    """begin <instrucciones> end

    Un bloque es una lista de instrucciones, y a la vez ES una instrucción.
    Por eso puede aparecer anidado dentro de otro bloque.
    """

    def __init__(self, instrucciones, linea, columna):
        super().__init__(linea, columna)
        self.instrucciones = instrucciones

    def ejecutar(self, entorno, errores, tabla):
        # Esto es lo que decía el comentario "LO QUE FALTA AQUÍ" de la
        # semana pasada: un bloque abre su PROPIO ámbito. Las variables
        # que se declaren aquí adentro dejan de existir apenas termine
        # este `for` — porque `entorno_local` deja de tener referencias y
        # nadie más la puede alcanzar (padre nunca apunta hacia sus hijos).
        entorno_local = Entorno(padre=entorno)
        for instruccion in self.instrucciones:
            instruccion.ejecutar(entorno_local, errores, tabla)


class Programa(Nodo):
    """program <nombre>; <bloque> .  — la raíz del árbol."""

    def __init__(self, nombre, bloque, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.bloque = bloque

    def ejecutar(self, entorno, errores, tabla):
        self.bloque.ejecutar(entorno, errores, tabla)


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
