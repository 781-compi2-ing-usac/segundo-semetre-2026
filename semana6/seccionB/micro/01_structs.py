"""
MICRO-EJEMPLO 1: Records (structs), sin PLY.

Objetivo: ver que un registro no es un concepto nuevo — es la MISMA idea
que ya usaron para declarar variables y arreglos, aplicada dos veces:

  1. Declarar el TIPO: una lista de nombres de campo (como los parámetros
     de una función — mismo par nombre+tipo).
  2. Declarar una VARIABLE de ese tipo: un valor nuevo, con cada campo
     en su valor por defecto, igual que un arreglo arranca en
     [0, 0, 0, ...].

La única pieza genuinamente nueva es el ACCESO POR CAMPO (`persona.edad`
en vez de `arreglo[0]`) — un diccionario de Python en vez de una lista.

Correr con: python 01_structs.py
"""


VALORES_POR_DEFECTO = {
    'integer': 0,
    'real': 0.0,
    'boolean': False,
    'string': '',
}


# Paso 1: declarar el TIPO. En MiniPascal esto va a ser
#   type Persona = record
#       nombre: string;
#       edad: integer;
#   end;
# Aquí lo simulamos con un diccionario: nombre del tipo -> lista de
# (nombre_campo, tipo_campo). Fíjense que es la MISMA forma que ya usan
# para los parámetros de una función (nombre + tipo) — no es casualidad,
# en el código real ambos van a reusar la misma clase `Parametro`.
TIPOS_REGISTRO = {
    'Persona': [
        ('nombre', 'string'),
        ('edad', 'integer'),
    ],
}


def declarar_registro(nombre_tipo):
    """Simula DeclaracionRegistro.ejecutar: crea una instancia nueva con
    todos sus campos en el valor por defecto de su tipo — igual que
    DeclaracionArreglo hace con [0, 0, 0, ...], pero con un diccionario
    en vez de una lista, porque los campos tienen NOMBRE, no posición.
    """
    campos = TIPOS_REGISTRO[nombre_tipo]
    return {nombre_campo: VALORES_POR_DEFECTO[tipo_campo] for nombre_campo, tipo_campo in campos}


def leer_campo(instancia, nombre_campo):
    """Simula AccesoCampo.evaluar: persona.nombre"""
    if nombre_campo not in instancia:
        raise KeyError(f"no existe el campo {nombre_campo!r}")
    return instancia[nombre_campo]


def escribir_campo(instancia, nombre_campo, valor):
    """Simula AsignacionCampo.ejecutar: persona.nombre := 'Ana';"""
    if nombre_campo not in instancia:
        raise KeyError(f"no existe el campo {nombre_campo!r}")
    instancia[nombre_campo] = valor


if __name__ == '__main__':
    print("Declarar una instancia nueva:")
    persona = declarar_registro('Persona')
    print(f"  persona = {persona}")   # todos los campos en su valor por defecto

    print("\nEscribir campos:")
    escribir_campo(persona, 'nombre', 'Ana')
    escribir_campo(persona, 'edad', 20)
    print(f"  persona = {persona}")

    print("\nLeer un campo:")
    print(f"  persona.nombre = {leer_campo(persona, 'nombre')!r}")

    print("\nDos instancias del mismo tipo son independientes:")
    otra_persona = declarar_registro('Persona')
    escribir_campo(otra_persona, 'nombre', 'Luis')
    print(f"  persona      = {persona}")
    print(f"  otra_persona = {otra_persona}")

    print("\nAcceder a un campo que no existe:")
    try:
        leer_campo(persona, 'apellido')
    except KeyError as error:
        print(f"  {error}   <- esto en MiniPascal es un error semántico, no una excepción de Python")

    # ---------------------------------------------------------------
    # Para su proyecto:
    #
    # - Declarar el TIPO (el `record ... end`) y declarar una VARIABLE
    #   de ese tipo (`var p: Persona;`) son dos instrucciones DISTINTAS,
    #   como aquí `TIPOS_REGISTRO['Persona']` (la definición) y
    #   `declarar_registro('Persona')` (una instancia) también lo son.
    #   No las mezclen en una sola clase del AST.
    # - `leer_campo`/`escribir_campo` aquí lanzan `KeyError` para que el
    #   ejemplo sea corto. En MiniPascal real (`AccesoCampo`,
    #   `AsignacionCampo`) esto tiene que ser `errores.agregar(...)` +
    #   `return None`/`return`, NUNCA una excepción — mismo patrón de
    #   "preguntar antes de actuar" que ya usan en `Indexado` desde la
    #   Sesión 4.
    # - Dónde se guarda la definición del TIPO es una decisión de diseño:
    #   podría vivir en un diccionario aparte (como aquí), o reusar el
    #   mismo `Entorno` donde ya guardan variables y funciones (todo bajo
    #   el mismo mecanismo `declarar`/`buscar`). El código real de esta
    #   semana usa la segunda opción — vean por qué en `ast_nodes.py`.
    # ---------------------------------------------------------------
