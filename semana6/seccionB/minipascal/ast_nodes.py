"""
MiniPascal v5 — Nodos del AST (patrón Intérprete).

La jerarquía es:

    Nodo                 (guarda línea y columna — todos los nodos)
     ├── Expresion       -> evaluar(entorno, errores, tabla)      DEVUELVE un valor
     │    ├── Literal
     │    ├── Variable
     │    ├── Aritmetica
     │    ├── Comparacion
     │    ├── Negacion
     │    ├── Llamada
     │    ├── Indexado
     │    ├── AccesoCampo     «NUEVO» — objeto.campo
     │    └── Slice           «NUEVO» — &nombre[inicio..fin]
     └── Instruccion     -> ejecutar(entorno, errores, tabla)     HACE algo
          ├── Writeln
          ├── Declaracion
          ├── DeclaracionArreglo
          ├── Asignacion
          ├── AsignacionIndexada
          ├── If / While / Repeat / Case (con RamaCase)
          ├── Break / Continue
          ├── Funcion / Return
          ├── TipoRegistro          «NUEVO» — type Nombre = record ... end;
          ├── DeclaracionRegistro   «NUEVO» — var p: Nombre;
          ├── AsignacionCampo       «NUEVO» — objeto.campo := expresion;
          └── Bloque

`Parametro` no es Expresion ni Instruccion: es una pieza auxiliar de
`Funcion` (sus parámetros) Y de `TipoRegistro` (sus campos) — un registro
es, estructuralmente, una lista de "parámetros" con nombre por defecto en
vez de con valor recibido. Reusarla evita una gramática duplicada.

Novedades de v5 frente a v4:

  - Records (`type Nombre = record ...; end;`): `TipoRegistro` (la
    definición del tipo) y `DeclaracionRegistro` (una variable de ese
    tipo). Declarar un tipo es, otra vez, lo mismo que declarar una
    variable o una función — se guarda en el mismo `Entorno`, con un
    marcador para no confundirlo con un valor normal. Ver
    micro/01_structs.py.
  - `AccesoCampo`/`AsignacionCampo`: leer y escribir `objeto.campo`. Un
    registro se representa en tiempo de ejecución como un `dict` de
    Python (nombre de campo -> valor), la misma idea que un arreglo es
    una `list`.
  - Slices: `VistaArreglo` (una clase — NO un `Nodo`, es un valor en
    tiempo de ejecución, como una lista) y `Slice` (el nodo del AST que
    la construye). A diferencia de un arreglo, un slice NO copia sus
    datos — es una vista sobre el arreglo original. Ver
    micro/02_slices.py antes de leer `Slice`/`VistaArreglo` aquí abajo.
  - Sin registros anidados (un campo no puede ser de tipo `record`) ni
    slices de slices — simplificaciones deliberadas de esta semana.
"""

from abc import ABC, abstractmethod

from entorno import Entorno
from senales import SenalBreak, SenalContinue, SenalReturn


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
    def evaluar(self, entorno, errores, tabla):
        """Calcula el valor de esta expresión y lo devuelve.

        Si algo sale mal, agrega el error a `errores` y devuelve `None` —
        NUNCA lanza una excepción para reportar un error semántico. `tabla`
        solo la usan las expresiones que, por dentro, ejecutan instrucciones
        (hoy: `Llamada`, al correr el cuerpo de una función).
        """
        ...


class Literal(Expresion):
    """Un valor escrito directamente en el código: 42, 3.14, 'hola', true."""

    def __init__(self, valor, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor

    def evaluar(self, entorno, errores, tabla):
        return self.valor


class Variable(Expresion):
    """Uso de un identificador dentro de una expresión: por ejemplo, la
    `x` en `x + 1`. NO confundir con `Declaracion`, que es la instrucción
    que la crea (`var x: integer;`) — esta clase es solo LEERLA.
    """

    def __init__(self, nombre, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre

    def evaluar(self, entorno, errores, tabla):
        if not entorno.existe(self.nombre):
            errores.agregar(
                'Semántico',
                f"La variable '{self.nombre}' no ha sido declarada.",
                self.linea, self.columna,
            )
            return None
        return entorno.buscar(self.nombre)


TIPOS_SUMA = {
    ('integer', 'integer'): 'integer',
    ('integer', 'real'):    'real',
    ('real',    'integer'): 'real',
    ('real',    'real'):    'real',
    ('string',  'string'):  'string',
}


def tipo_de_valor(valor):
    """Deriva el tipo de MiniPascal a partir de un valor de Python.

    Un arreglo (lista de Python) no tiene un tipo MiniPascal representable
    aquí con esta función de una sola palabra — por eso `Indexado` y
    `AsignacionIndexada` comprueban `isinstance(..., list)` directamente en
    vez de pasar por `tipo_de_valor`.
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

    def evaluar(self, entorno, errores, tabla):
        izq = self.izquierdo.evaluar(entorno, errores, tabla)
        der = self.derecho.evaluar(entorno, errores, tabla)

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
            return izq / der

        raise ValueError(f"Operador desconocido: {self.operador}")

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ (viene desde la Sesión 2, sigue igual):
        # Solo `+` está protegido con tabla de tipos. Repliquen el mismo
        # patrón para `-`, `*`, `/`.
        # ------------------------------------------------------------------


class Negacion(Expresion):
    """Menos unario: -x"""

    def __init__(self, expresion, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion

    def evaluar(self, entorno, errores, tabla):
        valor = self.expresion.evaluar(entorno, errores, tabla)
        if valor is None:
            return None
        return -valor


TIPOS_MENOR = {
    ('integer', 'integer'): 'boolean',
    ('integer', 'real'):    'boolean',
    ('real',    'integer'): 'boolean',
    ('real',    'real'):    'boolean',
    ('string',  'string'):  'boolean',
}


class Comparacion(Expresion):
    """Operador relacional: izquierdo (== != < > <= >=) derecho."""

    def __init__(self, izquierdo, operador, derecho, linea, columna):
        super().__init__(linea, columna)
        self.izquierdo = izquierdo
        self.operador = operador
        self.derecho = derecho

    def evaluar(self, entorno, errores, tabla):
        izq = self.izquierdo.evaluar(entorno, errores, tabla)
        der = self.derecho.evaluar(entorno, errores, tabla)

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
        # LO QUE FALTA AQUÍ (viene desde la Sesión 3, sigue igual):
        # Solo `<` tiene tabla de tipos.
        # ------------------------------------------------------------------


# Funciones embebidas (built-ins). Un solo caso representativo: `length`,
# que sirve tanto para arreglos como para cadenas porque en Python ambos
# responden a `len()`. Se resuelven ANTES de mirar el entorno: no ocupan
# una entrada ahí, así que no se pueden "sobrescribir" declarando una
# variable con el mismo nombre — es una simplificación deliberada, no una
# regla real de shadowing.
FUNCIONES_EMBEBIDAS = {
    'length': len,
}


class Llamada(Expresion):
    """nombre(argumentos)  — llamar una función declarada, o una función
    embebida (`length`).

    Este es el nodo que junta TODO lo nuevo de esta semana: evalúa los
    argumentos, arma el entorno de activación (colgado del entorno donde
    la función fue DECLARADA — `funcion.entorno_definicion` — nunca del
    entorno de quien llama), ejecuta el cuerpo, y atrapa SenalReturn para
    convertirla de vuelta en un valor normal de Python. También es, igual
    que `Programa.ejecutar`, un LÍMITE de pila: un `break`/`continue` que
    se escapa del cuerpo de la función sin que ningún ciclo de ADENTRO lo
    haya atrapado no debe seguir subiendo hacia el ciclo de quien llama —
    ver micro/02_limite_de_funcion.py.
    """

    def __init__(self, nombre, argumentos, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.argumentos = argumentos   # lista de Expresion

    def evaluar(self, entorno, errores, tabla):
        valores = []
        for argumento in self.argumentos:
            valor = argumento.evaluar(entorno, errores, tabla)
            if valor is None:
                return None
            valores.append(valor)

        if self.nombre in FUNCIONES_EMBEBIDAS:
            try:
                return FUNCIONES_EMBEBIDAS[self.nombre](*valores)
            except TypeError:
                # `len()` (y cualquier otro built-in de Python que agreguen
                # en el ejercicio 3) lanza TypeError por DOS causas
                # distintas: cantidad de argumentos incorrecta (`length()`,
                # `length(a, b)`) o un argumento de un tipo que no soporta
                # (`length(5)`). Las distinguimos con la cantidad, que sí
                # podemos comprobar nosotros mismos de antemano — así el
                # mensaje no le echa la culpa a la cantidad cuando en
                # realidad es el tipo el que está mal.
                if len(valores) != 1:
                    errores.agregar(
                        'Semántico',
                        f"'{self.nombre}' espera 1 argumento, recibió {len(valores)}.",
                        self.linea, self.columna,
                    )
                else:
                    errores.agregar(
                        'Semántico',
                        f"'{self.nombre}' no admite un argumento de tipo "
                        f"{tipo_de_valor(valores[0]) or 'desconocido'}.",
                        self.linea, self.columna,
                    )
                return None

        if not entorno.existe(self.nombre):
            errores.agregar(
                'Semántico',
                f"La función '{self.nombre}' no ha sido declarada.",
                self.linea, self.columna,
            )
            return None

        funcion = entorno.buscar(self.nombre)
        if not isinstance(funcion, Funcion):
            errores.agregar(
                'Semántico',
                f"'{self.nombre}' no es una función, no se puede llamar.",
                self.linea, self.columna,
            )
            return None

        if len(valores) != len(funcion.parametros):
            errores.agregar(
                'Semántico',
                f"'{self.nombre}' espera {len(funcion.parametros)} "
                f"argumento(s), recibió {len(valores)}.",
                self.linea, self.columna,
            )
            return None

        # *** El corazón de la sesión ***
        # padre=funcion.entorno_definicion, NUNCA padre=entorno. Si esto
        # dijera `padre=entorno` (el entorno de QUIEN LLAMA), cualquier
        # variable local de quien llama sería visible por accidente dentro
        # de la función — scoping dinámico. Colgar del entorno donde la
        # función fue declarada es lo mismo que hace un cierre (closure) en
        # Python o JavaScript.
        entorno_activacion = Entorno(padre=funcion.entorno_definicion, ambito=self.nombre)
        for parametro, valor in zip(funcion.parametros, valores):
            # Todo se pasa por VALOR en MiniPascal, incluidos los arreglos:
            # si `valor` es una lista, la copiamos, para que lo que la
            # función le haga a su copia no se refleje en el arreglo de
            # quien llamó. Ver "Qué falta para tu proyecto" — pasar por
            # referencia es una decisión de diseño distinta que ustedes sí
            # tienen que tomar explícitamente.
            #
            # A un `VistaArreglo` (un slice) esto A PROPÓSITO no lo toca:
            # `isinstance(valor, list)` da False para una vista, así que
            # pasa tal cual, sin copiar — un slice nunca copia, ni siquiera
            # al cruzar una llamada a función. Es la misma regla de
            # "vista, no copia" de micro/02_slices.py, aplicada aquí.
            if isinstance(valor, list):
                valor = list(valor)
            # Un registro (dict) es igual de mutable que un arreglo, por
            # la misma razón se copia — si no, modificar un campo DENTRO
            # de la función cambiaría el registro original de quien llamó,
            # sin que nada en el código lo avise.
            elif isinstance(valor, dict):
                valor = dict(valor)
            entorno_activacion.declarar(parametro.nombre, valor, tipo=parametro.tipo)

        try:
            funcion.cuerpo.ejecutar(entorno_activacion, errores, tabla)
        except SenalReturn as señal:
            return señal.valor
        except SenalBreak as señal:
            errores.agregar('Semántico', "'break' usado fuera de un ciclo.",
                             señal.linea, señal.columna)
        except SenalContinue as señal:
            errores.agregar('Semántico', "'continue' usado fuera de un ciclo.",
                             señal.linea, señal.columna)

        # El cuerpo terminó (o se cortó por un break/continue perdido) sin
        # pasar por ningún `return`. LO QUE FALTA AQUÍ: un compilador de
        # verdad exigiría que TODO camino posible de la función termine en
        # return; aquí no lo validamos, solo devolvemos silenciosamente el
        # valor por defecto del tipo declarado.
        return VALORES_POR_DEFECTO.get(funcion.tipo_retorno)


class VistaArreglo:
    """Una vista sobre parte de un arreglo, SIN copiar sus datos.

    NO es un `Nodo` — nunca aparece en el AST. Es un VALOR en tiempo de
    ejecución, exactamente como una `list` de Python lo es para un
    arreglo normal. Ver micro/02_slices.py para la explicación completa.

    Implementa `__len__`/`__getitem__`/`__setitem__` a propósito: así
    `len(vista)`, `vista[i]` y `vista[i] = valor` funcionan igual que con
    una lista de verdad, y `Indexado`/`AsignacionIndexada`/`length()` casi
    no necesitan saber que por dentro es otra cosa.
    """

    def __init__(self, arreglo_original, inicio, fin):
        self.arreglo_original = arreglo_original
        self.inicio = inicio
        self.fin = fin   # no incluido: [inicio, fin)

    def __len__(self):
        return self.fin - self.inicio

    def __getitem__(self, indice_local):
        # Sin este chequeo, `for x in vista` (el protocolo de iteración
        # "viejo" de Python, que usan por ejemplo `list(vista)` o un
        # `for` sin `__iter__`) seguiría de largo más allá de `self.fin`,
        # leyendo del arreglo ORIGINAL completo en vez de detenerse en el
        # borde del slice.
        if not (0 <= indice_local < len(self)):
            raise IndexError(indice_local)
        return self.arreglo_original[self.inicio + indice_local]

    def __setitem__(self, indice_local, valor):
        if not (0 <= indice_local < len(self)):
            raise IndexError(indice_local)
        self.arreglo_original[self.inicio + indice_local] = valor

    def __repr__(self):
        # Sin esto, imprimir una vista (por ejemplo en TablaSimbolos, que
        # no pasa por `formatear`) muestra la dirección de memoria cruda
        # de Python (`<ast_nodes.VistaArreglo object at 0x...>`) en vez
        # de algo legible.
        return '[' + ', '.join(str(self[i]) for i in range(len(self))) + ']'


# `Indexado`/`AsignacionIndexada` aceptan un arreglo O una vista — de ahí
# este alias, para no repetir `(list, VistaArreglo)` en cada isinstance.
TIPOS_INDEXABLES = (list, VistaArreglo)


class Slice(Expresion):
    """&nombre[inicio..fin]  — una VISTA sobre una porción de un arreglo.

    A diferencia de `Indexado` (que devuelve UN valor), esto devuelve una
    `VistaArreglo` — otro "arreglo" indexable, que comparte los datos con
    el original en vez de copiarlos.
    """

    def __init__(self, nombre, inicio, fin, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.inicio = inicio   # Expresion
        self.fin = fin         # Expresion

    def evaluar(self, entorno, errores, tabla):
        if not entorno.existe(self.nombre):
            errores.agregar(
                'Semántico',
                f"El arreglo '{self.nombre}' no ha sido declarado.",
                self.linea, self.columna,
            )
            return None

        arreglo = entorno.buscar(self.nombre)
        if not isinstance(arreglo, TIPOS_INDEXABLES):
            errores.agregar(
                'Semántico',
                f"'{self.nombre}' no es un arreglo, no se puede tomar un slice.",
                self.linea, self.columna,
            )
            return None

        inicio = self.inicio.evaluar(entorno, errores, tabla)
        fin = self.fin.evaluar(entorno, errores, tabla)
        if inicio is None or fin is None:
            return None

        if not (0 <= inicio <= fin <= len(arreglo)):
            errores.agregar(
                'Semántico',
                f"Rango [{inicio}..{fin}) inválido para '{self.nombre}' "
                f"(tamaño {len(arreglo)}).",
                self.linea, self.columna,
            )
            return None

        # Si `arreglo` YA es una VistaArreglo (un slice de un slice), la
        # nueva vista sigue apuntando al arreglo ORIGINAL de verdad, con
        # el rango recalculado — para no ir acumulando vistas-de-vistas.
        if isinstance(arreglo, VistaArreglo):
            return VistaArreglo(arreglo.arreglo_original, arreglo.inicio + inicio, arreglo.inicio + fin)
        return VistaArreglo(arreglo, inicio, fin)


class Indexado(Expresion):
    """nombre[indice]  — leer una casilla de un arreglo (o de un slice)."""

    def __init__(self, nombre, indice, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.indice = indice

    def evaluar(self, entorno, errores, tabla):
        if not entorno.existe(self.nombre):
            errores.agregar(
                'Semántico',
                f"El arreglo '{self.nombre}' no ha sido declarado.",
                self.linea, self.columna,
            )
            return None

        arreglo = entorno.buscar(self.nombre)
        if not isinstance(arreglo, TIPOS_INDEXABLES):
            errores.agregar(
                'Semántico',
                f"'{self.nombre}' no es un arreglo, no se puede indexar.",
                self.linea, self.columna,
            )
            return None

        indice = self.indice.evaluar(entorno, errores, tabla)
        if indice is None:
            return None

        if not (0 <= indice < len(arreglo)):
            errores.agregar(
                'Semántico',
                f"Índice {indice} fuera de rango para '{self.nombre}' "
                f"(tamaño {len(arreglo)}).",
                self.linea, self.columna,
            )
            return None

        return arreglo[indice]


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
        valor = self.expresion.evaluar(entorno, errores, tabla)
        if valor is None:
            return
        print(formatear(valor))


VALORES_POR_DEFECTO = {
    'integer': 0,
    'real': 0.0,
    'boolean': False,
    'string': '',
}


class Declaracion(Instruccion):
    """var nombre: tipo [:= expresion];   o   const nombre: tipo := expresion;"""

    def __init__(self, nombre, tipo, expresion_inicial, constante, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tipo = tipo
        self.expresion_inicial = expresion_inicial   # puede ser None
        self.constante = constante

    def ejecutar(self, entorno, errores, tabla):
        if self.expresion_inicial is not None:
            valor = self.expresion_inicial.evaluar(entorno, errores, tabla)
            if valor is None:
                valor = VALORES_POR_DEFECTO.get(self.tipo)
        else:
            valor = VALORES_POR_DEFECTO.get(self.tipo)

        entorno.declarar(self.nombre, valor, tipo=self.tipo, constante=self.constante)

        tabla.registrar(
            nombre=self.nombre,
            categoria='Constante' if self.constante else 'Variable',
            tipo=self.tipo,
            # Antes esto decía 'programa', fijo, sin importar cuántos
            # niveles de anidamiento hubiera — el hueco marcado en el
            # README de la Sesión 3. `entorno.ambito` ya sabe si estamos
            # dentro de una función (y de cuál), así que ahora sí queda
            # bien registrado.
            ambito=entorno.ambito,
            linea=self.linea,
            valor=valor,
        )


def describir_tipo(valor):
    """Como `tipo_de_valor`, pero también sabe describir arreglos,
    registros y slices — cosas que no tienen una sola palabra de tipo
    (`array[N] of T`, un nombre de record, "vista sobre un arreglo").
    Solo se usa para mostrar algo razonable en la tabla de símbolos; NO
    reemplaza a `tipo_de_valor` en la validación de operadores.
    """
    tipo_simple = tipo_de_valor(valor)
    if tipo_simple is not None:
        return tipo_simple
    if isinstance(valor, list):
        if valor:
            return f'array[{len(valor)}] of {describir_tipo(valor[0])}'
        return 'array[0] of ?'
    if isinstance(valor, dict):
        return '<registro>'
    return 'slice'   # el único caso que queda es VistaArreglo


class DeclaracionInferida(Instruccion):
    """var nombre := expresion;   (SIN anotación de tipo)

    El único caso donde MiniPascal permite `var` sin `: tipo`. Hace falta
    porque un slice no tiene una palabra de tipo que se pueda escribir de
    antemano (no existe un token para "vista sobre un arreglo") — así que
    la única forma razonable de guardar uno en una variable es dejar que
    el tipo se infiera del valor, en el momento en que se evalúa la
    expresión. Ver micro/02_slices.py y `Slice` más abajo.
    """

    def __init__(self, nombre, expresion, constante, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.expresion = expresion
        self.constante = constante

    def ejecutar(self, entorno, errores, tabla):
        valor = self.expresion.evaluar(entorno, errores, tabla)
        if valor is None:
            return   # el error ya se reportó al evaluar la expresión

        tipo = describir_tipo(valor)
        entorno.declarar(self.nombre, valor, tipo=tipo, constante=self.constante)

        tabla.registrar(
            nombre=self.nombre,
            categoria='Constante' if self.constante else 'Variable',
            tipo=tipo,
            ambito=entorno.ambito,
            linea=self.linea,
            # Una VistaArreglo comparte datos con el arreglo original a
            # propósito (es lo que la hace un slice) — pero LA TABLA sigue
            # necesitando una FOTO del momento, no un espejo en vivo del
            # slice (mismo bug que ya encontramos y arreglamos en la
            # Sesión 4 con DeclaracionArreglo). list(valor) funciona
            # gracias a que VistaArreglo.__getitem__ ya respeta sus
            # propios límites — ver el comentario ahí.
            valor=list(valor) if isinstance(valor, VistaArreglo) else valor,
        )

        # ------------------------------------------------------------------
        # LO QUE FALTA AQUÍ:
        #
        # Esta clase solo cubre `var` (mutable). `const nombre := expresion;`
        # con inferencia sería el mismo patrón, para una constante — no
        # está aquí porque ninguno de los ejemplos de esta semana lo
        # necesita, pero es una extensión de una sola clase más si la
        # llegan a necesitar.
        # ------------------------------------------------------------------


class DeclaracionArreglo(Instruccion):
    """var nombre: array[tamano] of tipo;

    Sin valor inicial (a diferencia de Declaracion): un arreglo siempre
    arranca lleno con el valor por defecto de su tipo de elemento. No
    existe sintaxis de arreglo LITERAL (`[1, 2, 3]`) en MiniPascal — es la
    simplificación deliberada de esta semana.
    """

    def __init__(self, nombre, tamano, tipo_elemento, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tamano = tamano
        self.tipo_elemento = tipo_elemento

    def ejecutar(self, entorno, errores, tabla):
        valor_por_defecto = VALORES_POR_DEFECTO.get(self.tipo_elemento)
        # Multiplicar una lista de un solo elemento SOLO es seguro porque
        # los valores por defecto son todos inmutables (int/float/bool/
        # str). Con un tipo de elemento mutable, las N casillas terminarían
        # apuntando al MISMO objeto — otro motivo para que un `record`
        # (que sí sería mutable) sea el hueco que queda para esta semana.
        valores = [valor_por_defecto] * self.tamano
        tipo_declarado = f'array[{self.tamano}] of {self.tipo_elemento}'

        entorno.declarar(self.nombre, valores, tipo=tipo_declarado, constante=False)

        tabla.registrar(
            nombre=self.nombre,
            categoria='Arreglo',
            tipo=tipo_declarado,
            ambito=entorno.ambito,
            linea=self.linea,
            # list(valores), no valores: la tabla guarda una FOTO de este
            # momento (todo en su valor por defecto), igual que hace
            # Declaracion con una variable escalar. Si guardáramos
            # `valores` directo, sería la misma lista que después mutan
            # AsignacionIndexada/Llamada — la tabla dejaría de ser una
            # bitácora y pasaría a ser un espejo en vivo, que es
            # exactamente lo que el README de la Sesión 2 dice que NO debe
            # ser.
            valor=list(valores),
        )


class Asignacion(Instruccion):
    """nombre := expresion;   (SIN `var`/`const`: la variable ya existía)"""

    def __init__(self, nombre, expresion, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.expresion = expresion

    def ejecutar(self, entorno, errores, tabla):
        valor = self.expresion.evaluar(entorno, errores, tabla)
        if valor is None:
            return

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


class AsignacionIndexada(Instruccion):
    """nombre[indice] := expresion;"""

    def __init__(self, nombre, indice, expresion, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.indice = indice
        self.expresion = expresion

    def ejecutar(self, entorno, errores, tabla):
        if not entorno.existe(self.nombre):
            errores.agregar(
                'Semántico',
                f"El arreglo '{self.nombre}' no ha sido declarado.",
                self.linea, self.columna,
            )
            return

        arreglo = entorno.buscar(self.nombre)
        if not isinstance(arreglo, TIPOS_INDEXABLES):
            errores.agregar(
                'Semántico',
                f"'{self.nombre}' no es un arreglo, no se puede indexar.",
                self.linea, self.columna,
            )
            return

        indice = self.indice.evaluar(entorno, errores, tabla)
        valor = self.expresion.evaluar(entorno, errores, tabla)
        if indice is None or valor is None:
            return

        if not (0 <= indice < len(arreglo)):
            errores.agregar(
                'Semántico',
                f"Índice {indice} fuera de rango para '{self.nombre}' "
                f"(tamaño {len(arreglo)}).",
                self.linea, self.columna,
            )
            return

        # `arreglo` es el MISMO objeto (lista o VistaArreglo) que vive
        # dentro de `Entorno` — mutamos la casilla directamente en vez de
        # llamar entorno.asignar(nombre, ...): no estamos reemplazando el
        # arreglo completo, solo una posición de él. Si `arreglo` es una
        # VistaArreglo, su propio `__setitem__` se encarga de traducir
        # esto en una escritura sobre el arreglo ORIGINAL — ni esta clase
        # ni `Indexado` necesitan saber cuál de los dos es.
        arreglo[indice] = valor


class Bloque(Instruccion):
    """begin <instrucciones> end"""

    def __init__(self, instrucciones, linea, columna):
        super().__init__(linea, columna)
        self.instrucciones = instrucciones

    def ejecutar(self, entorno, errores, tabla):
        entorno_local = Entorno(padre=entorno)
        for instruccion in self.instrucciones:
            instruccion.ejecutar(entorno_local, errores, tabla)


def verificar_condicion_booleana(valor, errores, linea, columna, de_donde):
    if valor is None:
        return False

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
        self.bloque_no = bloque_no

    def ejecutar(self, entorno, errores, tabla):
        valor = self.condicion.evaluar(entorno, errores, tabla)
        if not verificar_condicion_booleana(valor, errores, self.linea, self.columna, "un 'if'"):
            return
        if valor:
            self.bloque_si.ejecutar(entorno, errores, tabla)
        elif self.bloque_no is not None:
            self.bloque_no.ejecutar(entorno, errores, tabla)


class While(Instruccion):
    """[etiqueta:] while <condicion> do <cuerpo>;"""

    def __init__(self, condicion, cuerpo, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.condicion = condicion
        self.cuerpo = cuerpo
        self.etiqueta = etiqueta

    def ejecutar(self, entorno, errores, tabla):
        while True:
            valor = self.condicion.evaluar(entorno, errores, tabla)
            if not verificar_condicion_booleana(valor, errores, self.linea, self.columna, "un 'while'"):
                return
            if not valor:
                break

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
            # SenalReturn NO se atrapa aquí — tiene que atravesar este
            # `while` sin tocarlo y seguir subiendo hasta la Llamada que la
            # originó. Igual que en micro/01_senales.py de la Sesión 3.


class Repeat(Instruccion):
    """repeat <instrucciones> until <condicion>;"""

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
                    raise
            except SenalBreak as señal:
                if señal.etiqueta is not None:
                    raise
                break

            valor = self.condicion.evaluar(entorno_local, errores, tabla)
            if not verificar_condicion_booleana(valor, errores, self.linea, self.columna, "un 'repeat...until'"):
                return
            if valor:
                break


class RamaCase(Nodo):
    """Una rama de `case`: valor: bloque."""

    def __init__(self, valor, bloque, linea, columna):
        super().__init__(linea, columna)
        self.valor = valor
        self.bloque = bloque


class Case(Instruccion):
    """case <selector> of <ramas> [else <bloque_por_defecto>] end;"""

    def __init__(self, selector, ramas, bloque_por_defecto, linea, columna):
        super().__init__(linea, columna)
        self.selector = selector
        self.ramas = ramas
        self.bloque_por_defecto = bloque_por_defecto

    def ejecutar(self, entorno, errores, tabla):
        valor = self.selector.evaluar(entorno, errores, tabla)
        if valor is None:
            return

        for rama in self.ramas:
            if valor == rama.valor:
                rama.bloque.ejecutar(entorno, errores, tabla)
                return

        if self.bloque_por_defecto is not None:
            self.bloque_por_defecto.ejecutar(entorno, errores, tabla)


class Break(Instruccion):
    """break; o break etiqueta;"""

    def __init__(self, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta

    def ejecutar(self, entorno, errores, tabla):
        raise SenalBreak(self.etiqueta, self.linea, self.columna)


class Continue(Instruccion):
    """continue; o continue etiqueta;"""

    def __init__(self, etiqueta, linea, columna):
        super().__init__(linea, columna)
        self.etiqueta = etiqueta

    def ejecutar(self, entorno, errores, tabla):
        raise SenalContinue(self.etiqueta, self.linea, self.columna)


class Parametro(Nodo):
    """Un parámetro de función: nombre y tipo.

    Es un `Nodo` (no una tupla suelta) por la misma razón que `RamaCase`
    en la Sesión 3: así `dot.py` lo dibuja sin que tengamos que tocar ese
    archivo — sigue sin conocer ninguna clase del AST por nombre.
    """

    def __init__(self, nombre, tipo, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.tipo = tipo


class Funcion(Instruccion):
    """function nombre(parametros): tipo_retorno; cuerpo;

    Declarar una función es, en el fondo, lo mismo que declarar una
    variable: guardar un valor bajo un nombre en el `Entorno` (ver
    `Entorno.buscar` en entorno.py — no distingue "valor normal" de
    "función", los dos viven en el mismo diccionario). La diferencia es
    que el "valor" guardado aquí es la función completa — sus parámetros,
    su tipo de retorno y su cuerpo — para poder ejecutarla más tarde
    cuando aparezca una `Llamada`. Declararla NO ejecuta su cuerpo.

    Lo segundo que hace `ejecutar` es guardar `entorno_definicion`: el
    entorno que estaba activo justo cuando se declaró la función. Es la
    pieza que hace posible el scoping estático — ver `Llamada.evaluar`
    más arriba y micro/01_entornos_activacion.py. Sin esto, la única
    referencia al "entorno donde vive la función" se perdería en cuanto
    terminara de ejecutarse la instrucción `Funcion` misma.
    """

    def __init__(self, nombre, parametros, tipo_retorno, cuerpo, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.parametros = parametros   # lista de Parametro
        self.tipo_retorno = tipo_retorno
        self.cuerpo = cuerpo   # Bloque
        self.entorno_definicion = None   # lo llena ejecutar()

    def ejecutar(self, entorno, errores, tabla):
        self.entorno_definicion = entorno
        entorno.declarar(self.nombre, self, tipo='function', constante=True)

        firma = ', '.join(f'{p.nombre}: {p.tipo}' for p in self.parametros)
        tabla.registrar(
            nombre=self.nombre,
            categoria='Función',
            tipo=f'({firma}) -> {self.tipo_retorno}',
            ambito=entorno.ambito,
            linea=self.linea,
            valor='<función>',
        )


class Return(Instruccion):
    """return expresion;

    No "hace" nada por sí sola — solo lanza `SenalReturn`, exactamente
    como `Break`/`Continue` lanzan la suya. Quien decide qué significa esa
    señal es `Llamada.evaluar`, en ast_nodes.py más arriba, el único lugar
    que la atrapa.
    """

    def __init__(self, expresion, linea, columna):
        super().__init__(linea, columna)
        self.expresion = expresion

    def ejecutar(self, entorno, errores, tabla):
        valor = self.expresion.evaluar(entorno, errores, tabla)
        raise SenalReturn(valor, self.linea, self.columna)


# ---------------------------------------------------------------------------
# Records (structs) — ver micro/01_structs.py antes de leer esto.
# ---------------------------------------------------------------------------

class TipoRegistro(Instruccion):
    """type Nombre = record campo1: tipo1; campo2: tipo2; ... end;

    Declarar un tipo record es, otra vez, lo mismo que declarar una
    variable o una función (ver `Funcion` más arriba): se guarda un valor
    bajo un nombre en el `Entorno`. Aquí el "valor" es la propia
    definición del tipo — la lista de campos — no algo que se pueda usar
    en una expresión. `DeclaracionRegistro` es quien la consulta después
    para saber qué campos crear y con qué valores por defecto.

    Simplificación deliberada: un campo solo puede ser de un tipo
    primitivo (`integer`/`real`/`boolean`/`string`), nunca de otro
    `record` — sin registros anidados por ahora.
    """

    def __init__(self, nombre, campos, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.campos = campos   # lista de Parametro (mismo par nombre+tipo)

    def ejecutar(self, entorno, errores, tabla):
        entorno.declarar(self.nombre, self, tipo='record-type', constante=True)

        firma = ', '.join(f'{c.nombre}: {c.tipo}' for c in self.campos)
        tabla.registrar(
            nombre=self.nombre,
            categoria='Tipo',
            tipo=f'record {{ {firma} }}',
            ambito=entorno.ambito,
            linea=self.linea,
            valor='<tipo>',
        )


class DeclaracionRegistro(Instruccion):
    """var nombre: NombreDeTipo;   (NombreDeTipo ya declarado con TipoRegistro)

    Crea una instancia nueva: un `dict` con todos los campos del tipo, en
    su valor por defecto — la misma idea que `DeclaracionArreglo` usa para
    llenar un arreglo con `[0, 0, 0, ...]`, aplicada a nombres en vez de
    posiciones.
    """

    def __init__(self, nombre, nombre_tipo, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.nombre_tipo = nombre_tipo

    def ejecutar(self, entorno, errores, tabla):
        if not entorno.existe(self.nombre_tipo):
            errores.agregar(
                'Semántico',
                f"El tipo '{self.nombre_tipo}' no ha sido declarado.",
                self.linea, self.columna,
            )
            return

        definicion = entorno.buscar(self.nombre_tipo)
        if not isinstance(definicion, TipoRegistro):
            errores.agregar(
                'Semántico',
                f"'{self.nombre_tipo}' no es un tipo record.",
                self.linea, self.columna,
            )
            return

        valores = {campo.nombre: VALORES_POR_DEFECTO.get(campo.tipo) for campo in definicion.campos}
        entorno.declarar(self.nombre, valores, tipo=self.nombre_tipo, constante=False)

        tabla.registrar(
            nombre=self.nombre,
            categoria='Registro',
            tipo=self.nombre_tipo,
            ambito=entorno.ambito,
            linea=self.linea,
            # dict(valores), no valores: la tabla guarda una FOTO de este
            # momento, igual que DeclaracionArreglo hace con list(valores)
            # — no un espejo en vivo del registro (ver README Sesión 2).
            valor=dict(valores),
        )


class AccesoCampo(Expresion):
    """objeto.campo  — leer un campo de un registro."""

    def __init__(self, nombre_objeto, nombre_campo, linea, columna):
        super().__init__(linea, columna)
        self.nombre_objeto = nombre_objeto
        self.nombre_campo = nombre_campo

    def evaluar(self, entorno, errores, tabla):
        if not entorno.existe(self.nombre_objeto):
            errores.agregar(
                'Semántico',
                f"'{self.nombre_objeto}' no ha sido declarado.",
                self.linea, self.columna,
            )
            return None

        objeto = entorno.buscar(self.nombre_objeto)
        if not isinstance(objeto, dict):
            errores.agregar(
                'Semántico',
                f"'{self.nombre_objeto}' no es un registro, no tiene campos.",
                self.linea, self.columna,
            )
            return None

        if self.nombre_campo not in objeto:
            errores.agregar(
                'Semántico',
                f"'{self.nombre_objeto}' no tiene un campo llamado '{self.nombre_campo}'.",
                self.linea, self.columna,
            )
            return None

        return objeto[self.nombre_campo]


class AsignacionCampo(Instruccion):
    """objeto.campo := expresion;"""

    def __init__(self, nombre_objeto, nombre_campo, expresion, linea, columna):
        super().__init__(linea, columna)
        self.nombre_objeto = nombre_objeto
        self.nombre_campo = nombre_campo
        self.expresion = expresion

    def ejecutar(self, entorno, errores, tabla):
        if not entorno.existe(self.nombre_objeto):
            errores.agregar(
                'Semántico',
                f"'{self.nombre_objeto}' no ha sido declarado.",
                self.linea, self.columna,
            )
            return

        objeto = entorno.buscar(self.nombre_objeto)
        if not isinstance(objeto, dict):
            errores.agregar(
                'Semántico',
                f"'{self.nombre_objeto}' no es un registro, no tiene campos.",
                self.linea, self.columna,
            )
            return

        if self.nombre_campo not in objeto:
            errores.agregar(
                'Semántico',
                f"'{self.nombre_objeto}' no tiene un campo llamado '{self.nombre_campo}'.",
                self.linea, self.columna,
            )
            return

        valor = self.expresion.evaluar(entorno, errores, tabla)
        if valor is None:
            return

        # `objeto` es el MISMO dict que vive en `Entorno` — mutamos el
        # campo directamente, igual que AsignacionIndexada muta una
        # casilla de un arreglo en vez de reemplazarlo completo.
        objeto[self.nombre_campo] = valor


class Programa(Nodo):
    """program <nombre>; <bloque> .  — la raíz del árbol."""

    def __init__(self, nombre, bloque, linea, columna):
        super().__init__(linea, columna)
        self.nombre = nombre
        self.bloque = bloque

    def ejecutar(self, entorno, errores, tabla):
        try:
            self.bloque.ejecutar(entorno, errores, tabla)
        except SenalBreak as señal:
            errores.agregar('Semántico', "'break' usado fuera de un ciclo.",
                             señal.linea, señal.columna)
        except SenalContinue as señal:
            errores.agregar('Semántico', "'continue' usado fuera de un ciclo.",
                             señal.linea, señal.columna)
        except SenalReturn as señal:
            errores.agregar('Semántico', "'return' usado fuera de una función.",
                             señal.linea, señal.columna)


# ---------------------------------------------------------------------------

def formatear(valor):
    """Convierte un valor de MiniPascal a texto para imprimirlo."""
    if isinstance(valor, bool):
        return 'true' if valor else 'false'
    if isinstance(valor, TIPOS_INDEXABLES):
        # Gracias a __len__/__getitem__, un VistaArreglo se recorre con
        # `range(len(...))` exactamente igual que una lista — no hace
        # falta un caso especial solo porque por dentro es una vista.
        return '[' + ', '.join(formatear(valor[i]) for i in range(len(valor))) + ']'
    if isinstance(valor, dict):
        campos = ', '.join(f'{nombre}: {formatear(v)}' for nombre, v in valor.items())
        return '{' + campos + '}'
    return str(valor)
