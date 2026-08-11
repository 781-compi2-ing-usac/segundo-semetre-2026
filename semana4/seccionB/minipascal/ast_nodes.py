"""
MiniPascal v3 — Nodos del AST (patrón Intérprete).

Aquí vive TODA la lógica de ejecución del lenguaje. El parser no calcula
nada: solo construye estos objetos.

La jerarquía es:

    Nodo                 (guarda línea y columna — todos los nodos)
     ├── Expresion       -> evaluar(entorno, errores)         DEVUELVE un valor
     │    ├── Literal
     │    ├── Variable
     │    ├── Aritmetica
     │    ├── Comparacion
     │    └── Negacion
     └── Instruccion     -> ejecutar(entorno, errores, tabla) HACE algo
          ├── Writeln
          ├── Declaracion
          ├── Asignacion
          ├── If
          ├── While
          ├── Repeat
          ├── Case          (usa RamaCase, que no es ni Expresion ni Instruccion)
          ├── Break
          ├── Continue
          └── Bloque

Novedades de v3 frente a v2:

  - Comparaciones (`==`, `!=`, `<`, `>`, `<=`, `>=`), necesarias para
    escribir una condición que no sea siempre `true`/`false` a mano.
  - Control de flujo: `if`/`while`/`repeat`/`case`. Todas validan que su
    condición sea de tipo `boolean` ANTES de decidir qué rama tomar —
    ver `verificar_condicion_booleana` más abajo.
  - `break`/`continue`, implementados con excepciones (`senales.py`), tal
    como se explica en `micro/01_senales.py`.
  - `While` acepta una etiqueta opcional (`nombre: while ... do ...;`).
    `Repeat` NO — es la única simplificación deliberada de esta semana.
"""

from abc import ABC, abstractmethod

from entorno import Entorno
from senales import SenalBreak, SenalContinue


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


# Tabla de tipos para `<`, igual de "un solo caso representativo" que
# TIPOS_SUMA. `==`, `!=`, `>`, `<=` y `>=` operan sin tabla más abajo —
# mismo hueco deliberado que -, * y / en Aritmetica.
TIPOS_MENOR = {
    ('integer', 'integer'): 'boolean',
    ('integer', 'real'):    'boolean',
    ('real',    'integer'): 'boolean',
    ('real',    'real'):    'boolean',
    ('string',  'string'):  'boolean',   # orden lexicográfico, como en Python
}


class Comparacion(Expresion):
    """Operador relacional: izquierdo (== != < > <= >=) derecho.

    A diferencia de Aritmetica, el resultado SIEMPRE es boolean (si la
    comparación es válida) — nunca integer ni real.
    """

    def __init__(self, izquierdo, operador, derecho, linea, columna):
        super().__init__(linea, columna)
        self.izquierdo = izquierdo
        self.operador = operador
        self.derecho = derecho

    def evaluar(self, entorno, errores):
        izq = self.izquierdo.evaluar(entorno, errores)
        der = self.derecho.evaluar(entorno, errores)

        if izq is None or der is None:
            return None

        if self.operador == '<':
            if TIPOS_MENOR.get((tipo_de_valor(izq), tipo_de_valor(der))) is None:
                errores.agregar(
                    'Semántico',
                    f"No es posible comparar los tipos {tipo_de_valor(izq)} "
                    f"y {tipo_de_valor(der)} con '<'.",
                    self.linea, self.columna,
                )
                return None
            return izq < der

        if self.operador == '==':
            return izq == der
        if self.operador == '!=':
            return izq != der
        if self.operador == '>':
            return izq > der
        if self.operador == '<=':
            return izq <= der
        if self.operador == '>=':
            return izq >= der

        raise ValueError(f"Operador desconocido: {self.operador}")

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ:
        #
        # Solo `<` tiene tabla de tipos. Repliquen el mismo patrón para
        # `>`, `<=`, `>=` (secciones 3.3.6 del enunciado), y decidan qué
        # combinaciones tienen sentido para `==`/`!=` — el enunciado
        # permite comparar CUALQUIER par de tipos con igualdad, así que
        # esos dos probablemente no necesiten tabla, solo reglas propias.
        # ------------------------------------------------------------------


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


def verificar_condicion_booleana(valor, errores, linea, columna, de_donde):
    """Confirma que `valor` (ya evaluado) sea de tipo boolean.

    Usado por If/While/Repeat antes de decidir qué rama tomar. Devuelve
    True/False; si devuelve False, YA se reportó el error (o ya venía
    reportado desde más abajo, si `valor` llegó en None) — quien llama
    solo necesita decidir qué hacer para seguir sin reventar.
    """
    if valor is None:
        return False   # el error ya se reportó al evaluar la condición

    if tipo_de_valor(valor) != 'boolean':
        errores.agregar(
            'Semántico',
            f"La condición de {de_donde} debe ser de tipo boolean, "
            f"no {tipo_de_valor(valor)}.",
            linea, columna,
        )
        return False

    return True


class If(Instruccion):
    """if <condicion> then <bloque_si> [else <bloque_no>];"""

    def __init__(self, condicion, bloque_si, bloque_no, linea, columna):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.bloque_si = bloque_si
        self.bloque_no = bloque_no   # puede ser None

    def ejecutar(self, entorno, errores, tabla):
        valor = self.condicion.evaluar(entorno, errores)
        if not verificar_condicion_booleana(valor, errores, self.linea, self.columna, "un 'if'"):
            return   # ni bloque_si ni bloque_no: no sabemos qué rama tomar
        if valor:
            self.bloque_si.ejecutar(entorno, errores, tabla)
        elif self.bloque_no is not None:
            self.bloque_no.ejecutar(entorno, errores, tabla)


class While(Instruccion):
    """[etiqueta:] while <condicion> do <cuerpo>;

    `etiqueta` es opcional (None si no se puso ninguna). `cuerpo` es un
    Bloque, así que abre su propio ámbito solo — While no toca `Entorno`
    directamente, solo la condición.
    """

    def __init__(self, condicion, cuerpo, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.cuerpo = cuerpo
        self.etiqueta = etiqueta

    def ejecutar(self, entorno, errores, tabla):
        while True:
            valor = self.condicion.evaluar(entorno, errores)
            if not verificar_condicion_booleana(valor, errores, self.linea, self.columna, "un 'while'"):
                return
            if not valor:
                break

            # Mismo patrón que micro/01_senales.py: atrapamos Break/Continue
            # que nos correspondan (etiqueta None, o igual a la nuestra);
            # todo lo demás lo dejamos subir sin tocarlo.
            try:
                self.cuerpo.ejecutar(entorno, errores, tabla)
            except SenalContinue as señal:
                if señal.etiqueta not in (None, self.etiqueta):
                    raise
                continue
            except SenalBreak as señal:
                if señal.etiqueta not in (None, self.etiqueta):
                    raise
                break


class Repeat(Instruccion):
    """repeat <instrucciones> until <condicion>;

    La ÚNICA estructura de control que no usa begin/end (usa repeat/until
    como sus propios delimitadores), así que es la única que abre su
    propio `Entorno` directamente — no delega en `Bloque`. Y no acepta
    etiqueta: es la simplificación deliberada de esta semana.

    Corre el cuerpo AL MENOS UNA VEZ (a diferencia de while, que puede no
    ejecutarse nunca), y termina cuando la condición se vuelve VERDADERA
    — al revés de while, que sigue mientras es verdadera.
    """

    def __init__(self, instrucciones, condicion, linea, columna):
        super().__init__(linea, columna)
        self.instrucciones = instrucciones
        self.condicion = condicion

    def ejecutar(self, entorno, errores, tabla):
        entorno_local = Entorno(padre=entorno)
        while True:
            try:
                for instruccion in self.instrucciones:
                    instruccion.ejecutar(entorno_local, errores, tabla)
            except SenalContinue as señal:
                if señal.etiqueta is not None:
                    raise   # repeat no soporta etiquetas: no es para mí
                # un continue en un repeat salta directo a evaluar la
                # condición de abajo — no hace falta nada más aquí.
            except SenalBreak as señal:
                if señal.etiqueta is not None:
                    raise
                break

            valor = self.condicion.evaluar(entorno_local, errores)
            if not verificar_condicion_booleana(valor, errores, self.linea, self.columna, "un 'repeat...until'"):
                return
            if valor:
                break


class RamaCase(Nodo):
    """Una rama de `case`: valor: bloque.

    No es Expresion ni Instruccion por sí sola — es una pieza intermedia
    que solo `Case` usa. La hacemos un `Nodo` (y no una tupla suelta) para
    que `dot.py` la pueda dibujar sin que le tengamos que enseñar nada
    nuevo: sigue sin conocer ninguna clase del AST por nombre.
    """

    def __init__(self, valor, bloque, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor
        self.bloque = bloque


class Case(Instruccion):
    """case <selector> of <ramas> [else <bloque_por_defecto>] end;

    Compara el valor de `selector` contra cada `RamaCase.valor` en orden,
    y ejecuta la PRIMERA que coincida. Si ninguna coincide, ejecuta
    `bloque_por_defecto` (si existe).
    """

    def __init__(self, selector, ramas, bloque_por_defecto, linea, columna):
        super().__init__(linea, columna)
        self.selector = selector
        self.ramas = ramas   # lista de RamaCase
        self.bloque_por_defecto = bloque_por_defecto   # puede ser None

    def ejecutar(self, entorno, errores, tabla):
        valor = self.selector.evaluar(entorno, errores)
        if valor is None:
            return

        for rama in self.ramas:
            if valor == rama.valor:
                rama.bloque.ejecutar(entorno, errores, tabla)
                return

        if self.bloque_por_defecto is not None:
            self.bloque_por_defecto.ejecutar(entorno, errores, tabla)

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ:
        #
        # `RamaCase.valor` en esta versión solo admite literales enteros
        # (revisen parser.py). El enunciado permite comparar contra
        # cualquier expresión constante; si quieren admitir cadenas o
        # booleanos como valores de rama, empiecen por la gramática.
        # ------------------------------------------------------------------


class Break(Instruccion):
    """break; o break etiqueta;"""

    def __init__(self, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta

    def ejecutar(self, entorno, errores, tabla):
        # No "hace" nada por sí misma: solo lanza la señal y deja que el
        # While/Repeat correspondiente decida qué hacer con ella.
        raise SenalBreak(self.etiqueta, self.linea, self.columna)


class Continue(Instruccion):
    """continue; o continue etiqueta;"""

    def __init__(self, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta

    def ejecutar(self, entorno, errores, tabla):
        raise SenalContinue(self.etiqueta, self.linea, self.columna)


class Programa(Nodo):
    """program <nombre>; <bloque> .  — la raíz del árbol."""

    def __init__(self, nombre, bloque, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.bloque = bloque

    def ejecutar(self, entorno, errores, tabla):
        # Si un `break`/`continue` llega hasta aquí sin que ningún ciclo
        # lo haya atrapado en el camino, es porque estaba fuera de
        # cualquier ciclo — un error semántico, no un motivo para que
        # Python reviente con una excepción sin capturar.
        try:
            self.bloque.ejecutar(entorno, errores, tabla)
        except SenalBreak as señal:
            errores.agregar('Semántico', "'break' usado fuera de un ciclo.",
                             señal.linea, señal.columna)
        except SenalContinue as señal:
            errores.agregar('Semántico', "'continue' usado fuera de un ciclo.",
                             señal.linea, señal.columna)


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
