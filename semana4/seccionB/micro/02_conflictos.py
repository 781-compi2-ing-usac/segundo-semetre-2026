"""
MICRO-EJEMPLO 2: El "dangling else" y cómo leer los conflictos de PLY.

Objetivo: entender qué es un conflicto shift/reduce, verlo aparecer con
sus propios ojos, y aprender a resolverlo con `precedence` — el mismo
mecanismo que ya usaron para `%prec UMENOS` en la Sesión 1, aplicado
ahora a instrucciones en vez de a operadores.

El problema clásico: en

    if a then if b then c else d

¿el `else` le pertenece al `if b` o al `if a`? Con una gramática
"ingenua" como la de abajo, las DOS lecturas son válidas:

    (A) if a then (if b then c else d)      <- else pega con el if MÁS CERCANO
    (B) if a then (if b then c) else d      <- else pega con el if de AFUERA

Todos los lenguajes reales usan (A). Pero el generador de parsers no lo
sabe solo: hay que decírselo explícitamente.

Correr con: python 02_conflictos.py
"""

import types

import ply.lex as lex
import ply.yacc as yacc

tokens = ('IF', 'THEN', 'ELSE', 'ID')
t_ignore = ' \t'


def t_IF(t):
    r'if'
    return t


def t_THEN(t):
    r'then'
    return t


def t_ELSE(t):
    r'else'
    return t


def t_ID(t):
    r'[a-z]+'
    return t


def t_error(t):
    t.lexer.skip(1)


lexer = lex.lex()


# ---------------------------------------------------------------------------
# Gramática AMBIGUA a propósito. Fíjense que se parece mucho a lo que
# necesitamos para MiniPascal:
#
#     stmt : IF ID THEN stmt              (if sin else)
#          | IF ID THEN stmt ELSE stmt    (if con else)
#          | ID                           (una instrucción cualquiera)
#
# La armamos como una función que devuelve un "módulo falso"
# (types.SimpleNamespace) en vez de escribir las reglas sueltas en este
# archivo, para poder construir DOS parsers distintos (uno con el
# conflicto, otro ya resuelto) sin que se pisen entre sí.
# ---------------------------------------------------------------------------

def construir_parser_ambiguo():
    def p_stmt_if(p):
        'stmt : IF ID THEN stmt'
        p[0] = ('if', p[2], p[4])

    def p_stmt_if_else(p):
        'stmt : IF ID THEN stmt ELSE stmt'
        p[0] = ('if-else', p[2], p[4], p[6])

    def p_stmt_id(p):
        'stmt : ID'
        p[0] = p[1]

    def p_error(p):
        pass

    modulo = types.SimpleNamespace(
        __file__=__file__,
        tokens=tokens,
        p_stmt_if=p_stmt_if,
        p_stmt_if_else=p_stmt_if_else,
        p_stmt_id=p_stmt_id,
        p_error=p_error,
    )
    return yacc.yacc(module=modulo, debug=True, write_tables=False)


def construir_parser_arreglado():
    # LA SOLUCIÓN: igual que %prec UMENOS le dio precedencia propia al
    # menos unario, aquí le damos precedencia propia a "un if sin else"
    # con un token inventado (IFX, que no existe en el lexer — solo sirve
    # para esto). Como ELSE tiene MAYOR precedencia que IFX (va después
    # en la tupla), cuando el parser esté parado entre "reducir el if sin
    # else" (%prec IFX) o "shiftear el ELSE que viene", ahora gana ELSE:
    # shift, a propósito y no por comportamiento por defecto.
    precedence = (
        ('nonassoc', 'IFX'),
        ('nonassoc', 'ELSE'),
    )

    # OJO: aquí las funciones se llaman distinto (`_arreglado` al final)
    # solo para que PLY no las confunda con las de
    # `construir_parser_ambiguo` — su chequeo de "función redefinida" es
    # un simple regex sobre el texto del archivo, no entiende que están
    # en dos funciones anidadas totalmente separadas. Lo que de verdad
    # importa es el NOMBRE con el que se registran abajo en `modulo`
    # (`p_stmt_if=...`): ESE es el que la gramática usa.
    def p_stmt_if_arreglado(p):
        'stmt : IF ID THEN stmt %prec IFX'
        p[0] = ('if', p[2], p[4])

    def p_stmt_if_else_arreglado(p):
        'stmt : IF ID THEN stmt ELSE stmt'
        p[0] = ('if-else', p[2], p[4], p[6])

    def p_stmt_id_arreglado(p):
        'stmt : ID'
        p[0] = p[1]

    def p_error_arreglado(p):
        pass

    modulo = types.SimpleNamespace(
        __file__=__file__,
        tokens=tokens,
        precedence=precedence,
        p_stmt_if=p_stmt_if_arreglado,
        p_stmt_if_else=p_stmt_if_else_arreglado,
        p_stmt_id=p_stmt_id_arreglado,
        p_error=p_error_arreglado,
    )
    return yacc.yacc(module=modulo, debug=False, write_tables=False)


if __name__ == '__main__':
    entrada = "if a then if b then c else d"

    print("=== SIN resolver el conflicto ===\n")

    parser_ambiguo = construir_parser_ambiguo()

    resultado = parser_ambiguo.parse(entrada, lexer=lexer)
    print(f"\nResultado: {resultado}")
    print("(el 'else' YA quedó pegado al if más cercano — PLY resuelve")
    print(" shift/reduce por defecto prefiriendo SHIFT, y aquí coincide")
    print(" con lo correcto. Pero miren el WARNING de arriba: existe")
    print(" igual, avisando que hubo una AMBIGÜEDAD que se resolvió")
    print(" adivinando, no porque se la hayamos resuelto explícitamente.)")
    print("\nBusquen 'conflict' en parser.out para ver el detalle:")
    print("  grep -i conflict parser.out")

    # -----------------------------------------------------------------
    # Por qué esto es peligroso: un warning que ignoran hoy puede ser un
    # bug real mañana. Si su gramática crece y alguna regla nueva cambia
    # el estado donde ocurre este conflicto, PLY podría dejar de resolver
    # "por casualidad" del lado correcto, y ustedes ni se enterarían: no
    # hay ERROR, solo un WARNING que nadie lee en medio de 200 líneas de
    # salida de terminal.
    # -----------------------------------------------------------------

    print("\n\n=== Resolviéndolo con precedence ===\n")

    parser_arreglado = construir_parser_arreglado()
    resultado2 = parser_arreglado.parse(entrada, lexer=lexer)
    print(f"Resultado: {resultado2}")
    print("(mismo resultado que antes, pero ahora SIN warning: PLY ya no")
    print(" tuvo que adivinar, se lo dijimos explícitamente con precedence)")

    # -------------------------------------------------------------------
    # Para su proyecto:
    #
    # - En cuanto agreguen `if`/`else` a su gramática real, van a ver
    #   este MISMO warning si no lo resuelven de una vez. No lo ignoren.
    # - El patrón es siempre igual: inventar un token de precedencia baja
    #   (aquí IFX) para la producción "corta" (if sin else), y darle a
    #   ELSE una precedencia mayor. Eso fuerza el shift, que es lo que
    #   hace que el else se pegue al if más cercano.
    # - Corran SIEMPRE `python -c "import parser"` (o el equivalente)
    #   después de tocar la gramática, y lean la salida completa. Un
    #   "WARNING" no detiene el programa, pero si lo ignoran, ese
    #   silencio se les puede convertir en horas de depuración después.
    # -------------------------------------------------------------------
