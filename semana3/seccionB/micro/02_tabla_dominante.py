"""
MICRO-EJEMPLO 2: La tabla de tipos resultantes, sin PLY.

Objetivo: el enunciado del proyecto pide varias tablas como esta (una para
suma, una para resta, una para comparaciones...). No hay que memorizarlas
ni escribirlas a mano con un montón de `if`: se guardan en un diccionario y
se consulta.

Aquí armamos la tabla para UN SOLO operador (`+`) y tres tipos
(`integer`, `real`, `string`). El patrón es el mismo para las demás tablas
de su proyecto — solo cambia el contenido del diccionario.

Correr con: python 02_tabla_dominante.py
"""

# La llave es (tipo_izquierdo, tipo_derecho) y el valor es el tipo del
# resultado. `None` como valor significa "esta combinación no es válida".
#
# Fíjense que la tabla NO es simétrica a propósito: sumar
# ('string', 'integer') podría significar otra cosa que sumar
# ('integer', 'string'), según cómo lo defina su lenguaje. Aquí las dejamos
# iguales por simplicidad, pero es una decisión de diseño, no un accidente.
SUMA = {
    ('integer', 'integer'): 'integer',
    ('integer', 'real'):    'real',
    ('real',    'integer'): 'real',
    ('real',    'real'):    'real',
    ('string',  'string'):  'string',   # concatenación
    ('integer', 'string'):  None,       # no está permitido en MiniPascal
    ('string',  'integer'): None,
}


def tipo_de(valor):
    """Deriva el 'tipo' de un valor de Python para este ejemplo.

    En su proyecto esto NO se hace así: el tipo de una variable lo
    guardan explícitamente cuando la declaran (`let x: i32 = ...`), no lo
    adivinan del valor de Python en tiempo de ejecución. Aquí lo hacemos
    para simplificar el ejemplo y enfocarnos solo en la tabla.
    """
    if isinstance(valor, bool):
        return 'boolean'
    if isinstance(valor, int):
        return 'integer'
    if isinstance(valor, float):
        return 'real'
    if isinstance(valor, str):
        return 'string'
    raise TypeError(f"tipo no soportado: {valor!r}")


def sumar(izquierdo, derecho):
    """Suma dos valores consultando la tabla, en vez de operar a ciegas."""
    tipo_izq = tipo_de(izquierdo)
    tipo_der = tipo_de(derecho)

    tipo_resultado = SUMA.get((tipo_izq, tipo_der))

    if tipo_resultado is None:
        # Aquí es exactamente donde su proyecto reporta el error semántico
        # (línea y columna incluidas) y devuelve None, SIN reventar.
        print(f"  [Error Semántico] no se puede sumar {tipo_izq} con {tipo_der}")
        return None

    return izquierdo + derecho


if __name__ == '__main__':
    casos = [
        (2, 3),                 # integer + integer -> integer
        (2, 3.5),               # integer + real    -> real
        ('Hola, ', 'mundo'),    # string + string   -> concatenación
        (2, 'mundo'),           # integer + string  -> ERROR (según la tabla)
    ]

    for izquierdo, derecho in casos:
        print(f"{izquierdo!r} + {derecho!r}")
        resultado = sumar(izquierdo, derecho)
        print(f"  -> {resultado!r}\n")

    # ---------------------------------------------------------------
    # Para su proyecto:
    #
    # - Necesitan UNA tabla por cada operador de la sección 3.3.5–3.3.7
    #   del enunciado (+, -, *, /, %, ==, !=, <, >, <=, >=). No hace falta
    #   escribir cinco columnas y cinco filas a mano cada vez: es un
    #   diccionario, y pueden generarlo con un loop si dos tipos siempre
    #   se comportan igual entre sí.
    # - El tipo de una variable en SU proyecto no se calcula con
    #   `isinstance` como aquí: viene de la declaración (`let x: i32`) o
    #   de la inferencia (`let x = 5` -> i32), y debería vivir guardado
    #   en la Tabla de Símbolos, no recalculado cada vez que se usa.
    # - `sumar()` aquí SOLO decide si la combinación es válida y qué tipo
    #   da. El VALOR sigue calculándose con el operador `+` normal de
    #   Python. La tabla no reemplaza la operación, solo la autoriza.
    # ---------------------------------------------------------------
