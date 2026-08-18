"""
MiniPascal v4 — Analizador léxico.

Novedades de v4 frente a v3:
  - Palabras reservadas de funciones y arreglos: function, return, array.
  - Tokens sueltos que faltaban: COMA (para listas de parámetros y
    argumentos), CORCHETEIZQ/CORCHETEDER (para `array[N]` y `x[i]`).
"""

import ply.lex as lex


reservadas = {
    'program': 'PROGRAM',
    'begin': 'BEGIN',
    'end': 'END',
    'writeln': 'WRITELN',
    'true': 'TRUE',
    'false': 'FALSE',
    'var': 'VAR',
    'const': 'CONST',
    'integer': 'TIPO',
    'real': 'TIPO',
    'boolean': 'TIPO',
    'string': 'TIPO',
    # Control de flujo
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'repeat': 'REPEAT',
    'until': 'UNTIL',
    'case': 'CASE',
    'of': 'OF',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    # Funciones y arreglos — NUEVO esta semana
    'function': 'FUNCTION',
    'return': 'RETURN',
    'array': 'ARRAY',
}

tokens = [
    'IDENTIFICADOR',
    'ENTERO',
    'REAL',
    'CADENA',
    'MAS',
    'MENOS',
    'POR',
    'ENTRE',
    'PARIZQ',
    'PARDER',
    'CORCHETEIZQ',
    'CORCHETEDER',
    'COMA',
    'PUNTOCOMA',
    'PUNTO',
    'DOSPUNTOS',
    'ASIGNACION',
    'IGUAL',
    'DISTINTO',
    'MENOR',
    'MAYOR',
    'MENORIGUAL',
    'MAYORIGUAL',
] + list(set(reservadas.values()))


t_MAS = r'\+'
t_MENOS = r'-'
t_POR = r'\*'
t_ENTRE = r'/'
t_PARIZQ = r'\('
t_PARDER = r'\)'
t_CORCHETEIZQ = r'\['
t_CORCHETEDER = r'\]'
t_COMA = r','
t_PUNTOCOMA = r';'
t_PUNTO = r'\.'
t_ASIGNACION = r':='
t_DOSPUNTOS = r':'

t_IGUAL = r'=='
t_DISTINTO = r'!='
t_MENORIGUAL = r'<='
t_MAYORIGUAL = r'>='
t_MENOR = r'<'
t_MAYOR = r'>'

t_ignore = ' \t'


def t_comentario_bloque(t):
    r'\(\*(.|\n)*?\*\)'
    t.lexer.lineno += t.value.count('\n')


def t_comentario_llaves(t):
    r'\{[^}]*\}'
    t.lexer.lineno += t.value.count('\n')


def t_REAL(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t


def t_ENTERO(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_CADENA(t):
    r"'([^'\n]|'')*'"
    t.value = t.value[1:-1].replace("''", "'")
    return t


def t_IDENTIFICADOR(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reservadas.get(t.value.lower(), 'IDENTIFICADOR')
    return t


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    columna = encontrar_columna(t.lexer.lexdata, t.lexpos)
    print(f"[Error Léxico] Línea {t.lexer.lineno}, Columna {columna}: "
          f"carácter no reconocido {t.value[0]!r}")
    t.lexer.skip(1)


def encontrar_columna(entrada, lexpos):
    inicio_de_linea = entrada.rfind('\n', 0, lexpos)
    return lexpos - inicio_de_linea


lexer = lex.lex()


if __name__ == '__main__':
    codigo = """program Demo;
begin
  writeln(2 + 3 * 4);   { esto es un comentario }
end.
"""
    lexer.lineno = 1
    lexer.input(codigo)

    print(f"{'TOKEN':<15} {'VALOR':<12} {'LÍNEA':>6} {'COLUMNA':>8}")
    print("-" * 45)
    for tok in lexer:
        columna = encontrar_columna(codigo, tok.lexpos)
        print(f"{tok.type:<15} {str(tok.value):<12} {tok.lineno:>6} {columna:>8}")
