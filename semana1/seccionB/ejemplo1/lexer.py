"""

PASO 1: SOLO el lexer, sin parser todavía.
Objetivo: ver con sus propios ojos qué es un "token" y cómo el texto
plano se convierte en una secuencia de piezas reconocidas, antes de
meterse con gramáticas.

Correr con: python lexer.py
"""

import ply.lex as lex

# Lista de nombres de tokens que vamos a reconocer
tokens = (
    'NUMBER',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
)

# Reglas simples: un token = una expresión regular (como string)
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'

# Caracteres que se ignoran (no generan token)
t_ignore = ' \t'


# Regla con lógica: un número puede tener varios dígitos, y queremos
# convertirlo de string a int antes de devolverlo.
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


# Qué hacer si aparece un carácter que ninguna regla reconoce
def t_error(t):
    print(f"Carácter ilegal: {t.value[0]!r}")
    t.lexer.skip(1)


# Con todo lo anterior ya definido arriba (por convención de nombres
# t_...), construimos el lexer:
lexer = lex.lex()


if __name__ == '__main__':
    data = "3 + 4 * (2 - 1)"

    lexer.input(data)  # le damos el texto a analizar

    print(f"Entrada: {data!r}\n")
    print("Tokens reconocidos:")
    for tok in lexer:
        # tok.type  -> nombre del token (ej. 'NUMBER')
        # tok.value -> valor concreto (ej. 3)
        print(f"  {tok.type:<8} {tok.value}")