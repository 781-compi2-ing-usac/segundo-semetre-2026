"""
MiniPascal v1 — Analizador léxico.

Novedades respecto al lexer de la semana pasada:
  - palabras reservadas resueltas con un diccionario (no con regex sueltas)
  - conteo de líneas y cálculo de columnas
  - comentarios de línea y de bloque, que se descartan
"""

import ply.lex as lex


# ---------------------------------------------------------------------------
# Palabras reservadas
#
# ¿Por qué un diccionario y no un token por cada palabra?
#
# Si escribieran  t_BEGIN = r'begin'  el lexer partiría el identificador
# `beginner` en el token BEGIN + el identificador `ner`. Es un bug clásico y
# silencioso.
#
# La solución estándar: reconocer TODO como identificador, y después
# preguntarle al diccionario si esa palabra en realidad era reservada.
# ---------------------------------------------------------------------------
reservadas = {
    'program': 'PROGRAM',
    'begin': 'BEGIN',
    'end': 'END',
    'writeln': 'WRITELN',
    'true': 'TRUE',
    'false': 'FALSE',
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
    'PUNTOCOMA',
    'PUNTO',
] + list(reservadas.values())


# Reglas simples: token = expresión regular como string
t_MAS = r'\+'
t_MENOS = r'-'
t_POR = r'\*'
t_ENTRE = r'/'
t_PARIZQ = r'\('
t_PARDER = r'\)'
t_PUNTOCOMA = r';'
t_PUNTO = r'\.'

t_ignore = ' \t'


# ---------------------------------------------------------------------------
# IMPORTANTE — el orden importa.
#
# PLY prueba primero TODAS las reglas escritas como función, en el orden en
# que aparecen en este archivo. Después prueba las escritas como string,
# ordenadas de la regex más larga a la más corta.
#
# Por eso REAL va antes que ENTERO: si ENTERO fuera primero, `3.14` se
# leería como ENTERO(3), PUNTO, ENTERO(14).
#
# Y por eso los comentarios van antes que todo: `(*` debe ganarle a `(`.
# ---------------------------------------------------------------------------

def t_comentario_bloque(t):
    r'\(\*(.|\n)*?\*\)'
    # El `?` de `*?` lo hace "no ambicioso": para en el PRIMER `*)` que
    # encuentre. Sin él, un archivo con dos comentarios se tragaría todo el
    # código que hay entre ellos.
    t.lexer.lineno += t.value.count('\n')
    # No hacemos `return t`: sin return, el token se descarta y nunca llega
    # al parser. Así es como se ignora algo en PLY.


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
    # En Pascal las cadenas van entre comillas simples, y una comilla dentro
    # de la cadena se escribe duplicándola:  'no se ve as''i'
    t.value = t.value[1:-1].replace("''", "'")
    return t


def t_IDENTIFICADOR(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    # Aquí se aplica el truco de las palabras reservadas. Si la palabra está
    # en el diccionario, le cambiamos el TIPO del token; el valor se queda
    # igual. Si no está, se queda como IDENTIFICADOR.
    #
    # `.lower()` porque Pascal NO distingue mayúsculas de minúsculas en las
    # palabras reservadas: `Begin`, `BEGIN` y `begin` son lo mismo.
    # (Ojo: OxigenScript sí es case sensitive. Revisen su enunciado.)
    t.type = reservadas.get(t.value.lower(), 'IDENTIFICADOR')
    return t


def t_newline(t):
    r'\n+'
    # Sin esta regla, TODOS sus errores dirían "Línea 1". PLY no cuenta
    # líneas solo.
    t.lexer.lineno += len(t.value)


def t_error(t):
    columna = encontrar_columna(t.lexer.lexdata, t.lexpos)
    print(f"[Error Léxico] Línea {t.lexer.lineno}, Columna {columna}: "
          f"carácter no reconocido {t.value[0]!r}")
    # `skip(1)` descarta un carácter y sigue. Sin esto el lexer se queda
    # atorado en el mismo carácter para siempre.
    t.lexer.skip(1)


def encontrar_columna(entrada, lexpos):
    """Convierte una posición absoluta en el texto a número de columna.

    Ver micro/02_linea_columna.py para la explicación detallada.
    """
    inicio_de_linea = entrada.rfind('\n', 0, lexpos)
    return lexpos - inicio_de_linea


lexer = lex.lex()


if __name__ == '__main__':
    # Permite correr "python lexer.py" para ver solo los tokens, sin parser.
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
