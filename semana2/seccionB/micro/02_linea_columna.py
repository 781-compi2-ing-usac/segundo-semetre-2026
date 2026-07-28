"""
MICRO-EJEMPLO 2: Línea y columna de cada token.

Objetivo: sin esto NO pueden generar el reporte de errores que pide el
enunciado del proyecto ("[Error Semántico] Línea 6, Columna 5").

Dos cosas que hay que saber:

  - LÍNEA: PLY NO la cuenta solo. Hay que incrementar `lexer.lineno`
    manualmente en una regla que reconozca los saltos de línea. Si se les
    olvida, TODOS sus errores van a decir "Línea 1".

  - COLUMNA: PLY tampoco la da. Lo que sí da es `lexpos`, la posición
    absoluta del token dentro de todo el texto de entrada (contando desde 0).
    La columna se calcula buscando dónde empezó la línea actual.

Correr con: python 02_linea_columna.py
"""

import ply.lex as lex

tokens = (
    'IDENTIFICADOR',
    'ENTERO',
    'ASIGNACION',
    'MAS',
    'PUNTOCOMA',
)

t_ASIGNACION = r':='
t_MAS = r'\+'
t_PUNTOCOMA = r';'

t_ignore = ' \t'


def t_IDENTIFICADOR(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    return t


def t_ENTERO(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_newline(t):
    r'\n+'
    # ESTA es la regla que hace que el conteo de líneas funcione.
    # `len(t.value)` porque la regex `\n+` puede haber capturado varios
    # saltos de golpe (una línea en blanco son dos '\n' seguidos).
    # No hacemos `return t`: los saltos de línea no son tokens, solo
    # actualizan el contador.
    t.lexer.lineno += len(t.value)


def t_error(t):
    # Un error léxico también necesita línea y columna. Aquí se ve por qué
    # `encontrar_columna` recibe el texto original: el lexer no lo guarda
    # de forma cómoda, hay que pasárselo nosotros.
    columna = encontrar_columna(t.lexer.lexdata, t.lexpos)
    print(f"  [Error Léxico] Línea {t.lexer.lineno}, Columna {columna}: "
          f"carácter no reconocido {t.value[0]!r}")
    t.lexer.skip(1)


def encontrar_columna(entrada, lexpos):
    """Convierte una posición absoluta (lexpos) en un número de columna.

    Idea: buscamos hacia atrás desde `lexpos` el último salto de línea.
    Todo lo que hay entre ese salto y el token son los caracteres que lo
    preceden en su línea.

        entrada = "var x;\nx := 10;"
                            ^ lexpos = 11 (el token ':=')

        rfind('\\n', 0, 11)  ->  6   (posición del salto de línea)
        11 - 6               ->  5   columna 5, contando desde 1

    Si el token está en la primera línea no hay salto anterior y `rfind`
    devuelve -1, con lo que la cuenta sale correcta igual:
    lexpos - (-1) = lexpos + 1.
    """
    inicio_de_linea = entrada.rfind('\n', 0, lexpos)
    return lexpos - inicio_de_linea


lexer = lex.lex()


if __name__ == '__main__':
    codigo = """contador := 10;
resultado := contador + 5;

total := resultado + @;
"""

    # OJO: si analizan varios textos con el mismo lexer, hay que reiniciar
    # `lineno` a mano. PLY no lo hace por ustedes y el contador se queda
    # con el valor de la corrida anterior.
    lexer.lineno = 1
    lexer.input(codigo)

    print("Código de entrada:")
    for i, linea in enumerate(codigo.split('\n'), start=1):
        print(f"  {i} | {linea}")

    print(f"\n{'TOKEN':<15} {'VALOR':<12} {'LÍNEA':>6} {'COLUMNA':>8}")
    print("-" * 45)

    for tok in lexer:
        columna = encontrar_columna(codigo, tok.lexpos)
        print(f"{tok.type:<15} {str(tok.value):<12} {tok.lineno:>6} {columna:>8}")

    # -------------------------------------------------------------------
    # Comprueben a mano: en la línea 2, `contador` empieza en la columna 14.
    # Cuéntenlo con el dedo sobre "resultado := contador + 5;" y va a dar.
    #
    # Para su proyecto: cada nodo del AST debe guardar su línea y columna en
    # el constructor, tomándolas del parser. Si no lo hacen desde el inicio,
    # después toca modificar todas las clases del AST de una sola vez.
    # -------------------------------------------------------------------
