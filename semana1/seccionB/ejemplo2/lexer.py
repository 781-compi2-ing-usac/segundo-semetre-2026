import ply.lex as lex

tokens = (
    'NUMBER',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
)

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_ignore = ' \t'


def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_error(t):
    print(f"Carácter ilegal: {t.value[0]!r}")
    t.lexer.skip(1)


lexer = lex.lex()


if __name__ == '__main__':
    # Permite correr "python lexer.py" para probar SOLO el lexer
    data = "3 + 4 * (2 - 1)"
    lexer.input(data)
    print(f"Entrada: {data!r}\n")
    for tok in lexer:
        print(tok)