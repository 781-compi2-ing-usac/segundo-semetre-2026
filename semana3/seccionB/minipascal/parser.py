"""
MiniPascal v2 — Analizador sintáctico.

*** ESTE ES EL ARCHIVO IMPORTANTE DE LA SESIÓN. ***

Comparen con semana1/seccionB/ejemplo2/parser.py, donde las reglas hacían:

    def p_expression_plus(p):
        'expression : expression PLUS expression'
        p[0] = p[1] + p[3]          <-- el parser CALCULA

Aquí NINGUNA regla calcula nada:

    def p_expresion_suma(p):
        'expresion : expresion MAS expresion'
        p[0] = Aritmetica(p[1], '+', p[3], ...)   <-- el parser CONSTRUYE

¿Por qué el cambio? Porque calcular durante el parseo solo funciona para
una calculadora. En cuanto aparecen variables, `if`, ciclos o funciones ya
no sirve:

  - un `if` NO debe ejecutar las dos ramas, solo una; el parser no sabe
    cuál porque la condición todavía no se ha evaluado
  - un `while` debe ejecutar su cuerpo N veces, pero el parser lo lee UNA
  - una función se declara una vez y se llama muchas, quizá antes de que
    el parser llegue a su declaración
  - para dibujar el AST o llenar la tabla de símbolos hace falta el árbol,
    y si calcularon al vuelo ya no lo tienen

Separar "construir" de "ejecutar" es lo que hace posible todo lo demás.

Gramática de v2 (lo nuevo de esta semana, marcado con «NUEVO»):

    programa      -> PROGRAM IDENTIFICADOR PUNTOCOMA bloque PUNTO
    bloque        -> BEGIN instrucciones END
    instrucciones -> instrucciones instruccion | vacío
    instruccion   -> WRITELN PARIZQ expresion PARDER PUNTOCOMA
                   | bloque PUNTOCOMA
                   | VAR IDENTIFICADOR DOSPUNTOS TIPO PUNTOCOMA                    «NUEVO»
                   | VAR IDENTIFICADOR DOSPUNTOS TIPO ASIGNACION expresion PUNTOCOMA «NUEVO»
                   | CONST IDENTIFICADOR DOSPUNTOS TIPO ASIGNACION expresion PUNTOCOMA «NUEVO»
                   | IDENTIFICADOR ASIGNACION expresion PUNTOCOMA                  «NUEVO»
    expresion     -> expresion (MAS|MENOS|POR|ENTRE) expresion
                   | MENOS expresion
                   | PARIZQ expresion PARDER
                   | ENTERO | REAL | CADENA | TRUE | FALSE
                   | IDENTIFICADOR                                                «NUEVO»
"""

import ply.yacc as yacc

from lexer import tokens, encontrar_columna   # noqa: F401 (yacc necesita `tokens`)
from ast_nodes import (
    Aritmetica,
    Asignacion,
    Bloque,
    Declaracion,
    Literal,
    Negacion,
    Programa,
    Variable,
    Writeln,
)


# ---------------------------------------------------------------------------
# Precedencia y asociatividad.
#
# Se lee de MENOR a MAYOR precedencia (la última línea es la que más amarra).
# Esto es lo que hace que `2 + 3 * 4` arme el árbol con la multiplicación
# abajo, y por lo tanto valga 14 y no 20.
#
# 'right' en UMENOS porque `- - 3` se agrupa como -(-3).
# UMENOS no es un token real: es un nombre inventado que solo sirve para
# darle precedencia propia a la regla del menos unario, con `%prec`. Sin
# eso, `-2 * 3` se leería como -(2 * 3), que casualmente da lo mismo, pero
# `-2 + 3` se leería como -(2 + 3) = -5 en lugar de 1.
# ---------------------------------------------------------------------------
precedence = (
    ('left', 'MAS', 'MENOS'),
    ('left', 'POR', 'ENTRE'),
    ('right', 'UMENOS'),
)


def posicion(p, indice):
    """Devuelve (línea, columna) del símbolo `indice` de la producción.

    `p.lineno(i)` y `p.lexpos(i)` son datos que PLY arrastra desde el lexer.
    `p.lexer.lexdata` es el texto completo que se está analizando; lo
    necesitamos para calcular la columna.

    OJO: `p.lineno(i)` solo funciona para TOKENS. Si `i` apunta a un
    no-terminal (otra regla), devuelve 0. Por eso abajo siempre pedimos la
    posición de un token concreto, no de una subexpresión.
    """
    return p.lineno(indice), encontrar_columna(p.lexer.lexdata, p.lexpos(indice))


# ---------------------------------------------------------------------------
# Estructura del programa
# ---------------------------------------------------------------------------

def p_programa(p):
    'programa : PROGRAM IDENTIFICADOR PUNTOCOMA bloque PUNTO'
    linea, columna = posicion(p, 1)
    p[0] = Programa(p[2], p[4], linea, columna)


def p_bloque(p):
    'bloque : BEGIN instrucciones END'
    linea, columna = posicion(p, 1)
    p[0] = Bloque(p[2], linea, columna)


# ---------------------------------------------------------------------------
# Listas: el patrón que más van a repetir en su proyecto.
#
# Se usa recursión POR LA IZQUIERDA (`instrucciones instruccion` y no
# `instruccion instrucciones`). PLY usa LALR(1), que trabaja de abajo hacia
# arriba, y con recursión izquierda va reduciendo cada elemento apenas lo
# lee. Con recursión derecha tendría que apilar la lista completa antes de
# poder reducir nada — funciona, pero consume pila proporcional al tamaño
# de la entrada.
#
# (Esto es al revés de lo que les enseñaron para parsers descendentes, donde
# la recursión izquierda es justamente la que hay que eliminar.)
# ---------------------------------------------------------------------------

def p_instrucciones_lista(p):
    'instrucciones : instrucciones instruccion'
    p[0] = p[1] + [p[2]]


def p_instrucciones_vacia(p):
    'instrucciones : '
    # La producción vacía es lo que permite `begin end` sin instrucciones.
    p[0] = []


# ---------------------------------------------------------------------------
# Instrucciones
# ---------------------------------------------------------------------------

def p_instruccion_writeln(p):
    'instruccion : WRITELN PARIZQ expresion PARDER PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Writeln(p[3], linea, columna)


def p_instruccion_bloque(p):
    'instruccion : bloque PUNTOCOMA'
    # Un bloque anidado. Desde esta semana SÍ abre un ámbito nuevo — vean
    # Bloque.ejecutar en ast_nodes.py.
    p[0] = p[1]


# ---------------------------------------------------------------------------
# Declaraciones: var (mutable) y const (inmutable)
#
# Tres formas, porque el valor inicial es opcional para `var` pero
# obligatorio para `const` (una constante sin valor no tiene sentido):
#
#   var x: integer;
#   var x: integer := 10;
#   const PI: real := 3.14;
# ---------------------------------------------------------------------------

def p_instruccion_var_sin_valor(p):
    'instruccion : VAR IDENTIFICADOR DOSPUNTOS TIPO PUNTOCOMA'
    linea, columna = posicion(p, 1)
    #                 nombre  tipo  expresion_inicial  constante
    p[0] = Declaracion(p[2],  p[4], None,              False, linea, columna)


def p_instruccion_var_con_valor(p):
    'instruccion : VAR IDENTIFICADOR DOSPUNTOS TIPO ASIGNACION expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Declaracion(p[2], p[4], p[6], False, linea, columna)


def p_instruccion_const(p):
    'instruccion : CONST IDENTIFICADOR DOSPUNTOS TIPO ASIGNACION expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Declaracion(p[2], p[4], p[6], True, linea, columna)


# ---------------------------------------------------------------------------
# Asignación: nombre := expresion;   (la variable ya existía)
# ---------------------------------------------------------------------------

def p_instruccion_asignacion(p):
    'instruccion : IDENTIFICADOR ASIGNACION expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Asignacion(p[1], p[3], linea, columna)


# ---------------------------------------------------------------------------
# Expresiones
# ---------------------------------------------------------------------------

def p_expresion_binaria(p):
    '''expresion : expresion MAS expresion
                 | expresion MENOS expresion
                 | expresion POR expresion
                 | expresion ENTRE expresion'''
    # Las cuatro producciones comparten cuerpo porque lo único que cambia es
    # el operador, y el operador está en p[2]. Escribirlas por separado sería
    # copiar y pegar cuatro veces lo mismo.
    linea, columna = posicion(p, 2)
    p[0] = Aritmetica(p[1], p[2], p[3], linea, columna)


def p_expresion_negacion(p):
    'expresion : MENOS expresion %prec UMENOS'
    linea, columna = posicion(p, 1)
    p[0] = Negacion(p[2], linea, columna)


def p_expresion_agrupada(p):
    'expresion : PARIZQ expresion PARDER'
    # Los paréntesis NO generan un nodo. Su único trabajo fue cambiar la
    # forma del árbol mientras el parser leía, y eso ya sucedió. Un AST
    # ("abstracto") no guarda los símbolos que no aportan significado.
    p[0] = p[2]


def p_expresion_literal(p):
    '''expresion : ENTERO
                 | REAL
                 | CADENA'''
    linea, columna = posicion(p, 1)
    p[0] = Literal(p[1], linea, columna)


def p_expresion_booleana(p):
    '''expresion : TRUE
                 | FALSE'''
    linea, columna = posicion(p, 1)
    # p[1] llega como el texto 'true' / 'false'; lo convertimos al booleano
    # de Python, que es el valor con el que vamos a operar.
    p[0] = Literal(p[1].lower() == 'true', linea, columna)


def p_expresion_variable(p):
    'expresion : IDENTIFICADOR'
    # Aparece un IDENTIFICADOR dentro de una expresión (`x + 1`, no
    # `x := 1`): es una LECTURA de variable, no una asignación. Por eso
    # construye Variable y no Asignacion — son gramaticalmente distintas
    # (instruccion vs. expresion) aunque ambas empiecen con el mismo token.
    linea, columna = posicion(p, 1)
    p[0] = Variable(p[1], linea, columna)


# ---------------------------------------------------------------------------

def p_error(p):
    if p:
        columna = encontrar_columna(p.lexer.lexdata, p.lexpos)
        print(f"[Error Sintáctico] Línea {p.lineno}, Columna {columna}: "
              f"no se esperaba {p.value!r}")
    else:
        print("[Error Sintáctico] La entrada terminó antes de tiempo "
              "(¿falta un 'end' o el punto final?)")

    # ------------------------------------------------------------------
    # LO QUE FALTA AQUÍ:
    #
    # Esto solo REPORTA el error; el parser se detiene igual y devuelve
    # None. El enunciado del proyecto pide RECUPERACIÓN: seguir analizando
    # para poder listar varios errores en una sola corrida.
    #
    # PLY lo permite con el token especial `error` en una producción, por
    # ejemplo:  'instruccion : error PUNTOCOMA'  (descarta hasta el
    # siguiente ';' y continúa). Investíguenlo en la sección "Error
    # Recovery" de la documentación de PLY.
    # ------------------------------------------------------------------


parser = yacc.yacc()


def parsear(texto):
    """Analiza `texto` y devuelve el AST (o None si hubo error de sintaxis)."""
    from lexer import lexer
    # Reiniciar el contador de líneas: PLY no lo hace entre análisis y el
    # lexer se queda con el valor de la corrida anterior. Este detalle
    # importa cuando su intérprete corra dentro de un servidor web y
    # atienda una petición tras otra.
    lexer.lineno = 1
    return parser.parse(texto, lexer=lexer)


if __name__ == '__main__':
    # Permite correr "python parser.py" para probar lexer + parser sin main.
    from entorno import Entorno
    from errores import ListaErrores
    from tabla_simbolos import TablaSimbolos

    codigo = """program Prueba;
begin
  var x: integer := 10;
  writeln(x + 3 * 4);
end.
"""
    arbol = parsear(codigo)
    print(f"AST construido: {arbol}")
    print("Ejecutando:")
    arbol.ejecutar(Entorno(), ListaErrores(), TablaSimbolos())
