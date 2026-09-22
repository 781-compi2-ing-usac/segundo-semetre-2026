"""
MiniPascal v5 — Analizador sintáctico.

Gramática de v5 (lo nuevo de esta semana, marcado con «NUEVO»):

    instruccion   -> ... (todo lo de la Sesión 4, igual)
                   | TYPE IDENTIFICADOR IGUALTIPO RECORD campos
                       END PUNTOCOMA                                     «NUEVO»
                   | VAR IDENTIFICADOR DOSPUNTOS IDENTIFICADOR PUNTOCOMA «NUEVO»
                   | IDENTIFICADOR PUNTO IDENTIFICADOR
                       ASIGNACION expresion PUNTOCOMA                    «NUEVO»
    campos        -> campos campo | campo                                «NUEVO»
    campo         -> IDENTIFICADOR DOSPUNTOS TIPO PUNTOCOMA               «NUEVO»
    expresion     -> ... (todo lo de la Sesión 4, igual)
                   | IDENTIFICADOR PUNTO IDENTIFICADOR                    «NUEVO»
                   | AMPERSAND IDENTIFICADOR CORCHETEIZQ expresion
                       RANGO expresion CORCHETEDER                       «NUEVO»

Gramática de v4 (para referencia — sigue vigente):

    instruccion   -> ... (todo lo de la Sesión 3, igual)
                   | FUNCTION IDENTIFICADOR PARIZQ parametros PARDER
                       DOSPUNTOS TIPO PUNTOCOMA bloque PUNTOCOMA           «NUEVO»
                   | RETURN expresion PUNTOCOMA                           «NUEVO»
                   | VAR IDENTIFICADOR DOSPUNTOS ARRAY CORCHETEIZQ ENTERO
                       CORCHETEDER OF TIPO PUNTOCOMA                      «NUEVO»
                   | IDENTIFICADOR CORCHETEIZQ expresion CORCHETEDER
                       ASIGNACION expresion PUNTOCOMA                     «NUEVO»
    parametros    -> parametros COMA parametro | parametro | vacío        «NUEVO»
    parametro     -> IDENTIFICADOR DOSPUNTOS TIPO                         «NUEVO»
    expresion     -> ... (todo lo de la Sesión 3, igual)
                   | IDENTIFICADOR PARIZQ argumentos PARDER               «NUEVO»
                   | IDENTIFICADOR CORCHETEIZQ expresion CORCHETEDER      «NUEVO»
    argumentos    -> argumentos COMA expresion | expresion | vacío        «NUEVO»

Un detalle de diseño que vale la pena notar: en Pascal de verdad, las
funciones se declaran ANTES del `begin` del bloque principal, en una
sección aparte. Aquí, `function ...;` es una `instruccion` más, mezclada
con el resto — igual que ya pasaba con `var`/`const` desde la Sesión 2.
Es menos "correcto" que el Pascal real, pero mantiene la gramática
pequeña, que es la prioridad de estos ejemplos.

Sobre la "declaración previa" (poder llamar a una función que aparece
MÁS ABAJO en el texto, o dos funciones que se llaman entre sí): en un
COMPILADOR de una sola pasada esto es un problema de verdad, porque hay
que conocer la firma de una función antes de generar código para
llamarla. Aquí NO lo es, y vale la pena entender por qué: `Funcion.
ejecutar` solo GUARDA la función en el entorno (ver ast_nodes.py) — no
corre su cuerpo. El cuerpo corre después, cuando alguien la LLAMA, y para
entonces todas las declaraciones anteriores en el mismo bloque ya se
ejecutaron. Prueben ejemplos/07_arreglos.mpas y
ejemplos/06_funciones.mpas (esPar / esImpar se llaman mutuamente) para
verlo funcionar sin ningún truco especial de "forward declaration".
"""

import ply.yacc as yacc

from lexer import tokens, encontrar_columna   # noqa: F401 (yacc necesita `tokens`)
from ast_nodes import (
    AccesoCampo,
    Aritmetica,
    Asignacion,
    AsignacionCampo,
    AsignacionIndexada,
    Bloque,
    Break,
    Case,
    Comparacion,
    Continue,
    Declaracion,
    DeclaracionArreglo,
    DeclaracionInferida,
    DeclaracionRegistro,
    Funcion,
    If,
    Indexado,
    Literal,
    Llamada,
    Negacion,
    Parametro,
    Programa,
    RamaCase,
    Repeat,
    Return,
    Slice,
    TipoRegistro,
    Variable,
    While,
    Writeln,
)


precedence = (
    ('nonassoc', 'IGUAL', 'DISTINTO', 'MENOR', 'MAYOR', 'MENORIGUAL', 'MAYORIGUAL'),
    ('left', 'MAS', 'MENOS'),
    ('left', 'POR', 'ENTRE'),
    ('right', 'UMENOS'),
    ('nonassoc', 'IFX'),
    ('nonassoc', 'ELSE'),
)


def posicion(p, indice):
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


def p_instrucciones_lista(p):
    'instrucciones : instrucciones instruccion'
    p[0] = p[1] + [p[2]]


def p_instrucciones_vacia(p):
    'instrucciones : '
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
    p[0] = p[1]


def p_instruccion_var_sin_valor(p):
    'instruccion : VAR IDENTIFICADOR DOSPUNTOS TIPO PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Declaracion(p[2], p[4], None, False, linea, columna)


def p_instruccion_var_con_valor(p):
    'instruccion : VAR IDENTIFICADOR DOSPUNTOS TIPO ASIGNACION expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Declaracion(p[2], p[4], p[6], False, linea, columna)


def p_instruccion_const(p):
    'instruccion : CONST IDENTIFICADOR DOSPUNTOS TIPO ASIGNACION expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Declaracion(p[2], p[4], p[6], True, linea, columna)


def p_instruccion_var_inferida(p):
    # var nombre := expresion;   — SIN `: tipo`. Necesario para los
    # slices (Slice/VistaArreglo más abajo), que no tienen una palabra de
    # tipo que se pueda escribir de antemano. Se distingue de
    # `p_instruccion_var_con_valor` por el token que sigue al
    # identificador: DOSPUNTOS (":") allá, ASIGNACION (":=") aquí — mismo
    # mecanismo de siempre.
    'instruccion : VAR IDENTIFICADOR ASIGNACION expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = DeclaracionInferida(p[2], p[4], False, linea, columna)


# ---------------------------------------------------------------------------
# Arreglos — NUEVO
#
# Solo la forma de declaración `var nombre: array[N] of tipo;`. El tamaño
# tiene que ser un ENTERO literal (no una expresión, ni una constante ya
# declarada): MiniPascal no soporta arreglos de tamaño dinámico. Es la
# simplificación deliberada de esta semana para esta parte.
# ---------------------------------------------------------------------------

def p_instruccion_var_arreglo(p):
    'instruccion : VAR IDENTIFICADOR DOSPUNTOS ARRAY CORCHETEIZQ ENTERO CORCHETEDER OF TIPO PUNTOCOMA'
    linea, columna = posicion(p, 1)
    #                       nombre  tamaño  tipo_elemento
    p[0] = DeclaracionArreglo(p[2], p[6],   p[9], linea, columna)


def p_instruccion_asignacion_indexada(p):
    'instruccion : IDENTIFICADOR CORCHETEIZQ expresion CORCHETEDER ASIGNACION expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = AsignacionIndexada(p[1], p[3], p[6], linea, columna)


def p_expresion_indexado(p):
    'expresion : IDENTIFICADOR CORCHETEIZQ expresion CORCHETEDER'
    linea, columna = posicion(p, 1)
    p[0] = Indexado(p[1], p[3], linea, columna)


# ---------------------------------------------------------------------------
# Slices — NUEVO
#
# &nombre[inicio..fin]  — el AMPERSAND ('&', "préstamo") es lo que marca
# que esto es una VISTA, no una copia. Ver Slice/VistaArreglo en
# ast_nodes.py, y micro/02_slices.py para el porqué.
# ---------------------------------------------------------------------------

def p_expresion_slice(p):
    'expresion : AMPERSAND IDENTIFICADOR CORCHETEIZQ expresion RANGO expresion CORCHETEDER'
    linea, columna = posicion(p, 1)
    #             nombre  inicio  fin
    p[0] = Slice(p[2],    p[4],   p[6], linea, columna)


# ---------------------------------------------------------------------------
# Records (structs) — NUEVO
#
# type Nombre = record
#     campo1: tipo1;
#     campo2: tipo2;
# end;
#
# Ojo con IGUALTIPO ('=') en vez de ASIGNACION (':='): declarar un TIPO no
# es lo mismo que asignar un VALOR, y la gramática lo distingue con un
# símbolo distinto — igual que en Pascal de verdad.
# ---------------------------------------------------------------------------

def p_instruccion_tipo_registro(p):
    'instruccion : TYPE IDENTIFICADOR IGUALTIPO RECORD campos END PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = TipoRegistro(p[2], p[5], linea, columna)


def p_campos_lista(p):
    'campos : campos campo'
    p[0] = p[1] + [p[2]]


def p_campos_una(p):
    'campos : campo'
    p[0] = [p[1]]


def p_campo(p):
    # Reusa la clase Parametro (nombre + tipo): un campo de un registro es
    # estructuralmente lo mismo que un parámetro de función. La única
    # diferencia real es el separador: campos van con ';', parámetros con
    # ',' — por eso son gramáticas DISTINTAS aunque construyan el mismo
    # tipo de nodo.
    'campo : IDENTIFICADOR DOSPUNTOS TIPO PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Parametro(p[1], p[3], linea, columna)


def p_instruccion_var_registro(p):
    # var p: Persona;   — IDENTIFICADOR en vez de TIPO: el nombre de un
    # tipo record ya declarado, no uno de los 4 tipos primitivos. LALR(1)
    # distingue esto de `var x: integer;` por el token que aparece en esa
    # posición — mismo mecanismo de siempre, sin conflicto.
    'instruccion : VAR IDENTIFICADOR DOSPUNTOS IDENTIFICADOR PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = DeclaracionRegistro(p[2], p[4], linea, columna)


def p_expresion_acceso_campo(p):
    'expresion : IDENTIFICADOR PUNTO IDENTIFICADOR'
    linea, columna = posicion(p, 1)
    p[0] = AccesoCampo(p[1], p[3], linea, columna)


def p_instruccion_asignacion_campo(p):
    'instruccion : IDENTIFICADOR PUNTO IDENTIFICADOR ASIGNACION expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = AsignacionCampo(p[1], p[3], p[5], linea, columna)


# ---------------------------------------------------------------------------
# Funciones — NUEVO
# ---------------------------------------------------------------------------

def p_instruccion_funcion(p):
    'instruccion : FUNCTION IDENTIFICADOR PARIZQ parametros PARDER DOSPUNTOS TIPO PUNTOCOMA bloque PUNTOCOMA'
    linea, columna = posicion(p, 1)
    #                nombre  parametros  tipo_retorno  cuerpo
    p[0] = Funcion(p[2],     p[4],       p[7],         p[9], linea, columna)


def p_parametros_lista(p):
    'parametros : parametros COMA parametro'
    p[0] = p[1] + [p[3]]


def p_parametros_una(p):
    'parametros : parametro'
    p[0] = [p[1]]


def p_parametros_vacia(p):
    'parametros : '
    # function saludar(): boolean;  — cero parámetros, sí es válido.
    p[0] = []


def p_parametro(p):
    'parametro : IDENTIFICADOR DOSPUNTOS TIPO'
    linea, columna = posicion(p, 1)
    p[0] = Parametro(p[1], p[3], linea, columna)


def p_parametro_arreglo(p):
    # Un parámetro también puede ser un arreglo. Se guarda con el MISMO
    # formato de texto ('array[N] of tipo') que usa DeclaracionArreglo,
    # para que Funcion.ejecutar registre una firma consistente en la
    # tabla de símbolos sin importar si el arreglo se declaró o llegó
    # como parámetro.
    'parametro : IDENTIFICADOR DOSPUNTOS ARRAY CORCHETEIZQ ENTERO CORCHETEDER OF TIPO'
    linea, columna = posicion(p, 1)
    tipo = f'array[{p[5]}] of {p[8]}'
    p[0] = Parametro(p[1], tipo, linea, columna)


def p_parametro_registro(p):
    # Un parámetro también puede ser de un tipo record ya declarado
    # (`persona: Persona`) — IDENTIFICADOR en vez de TIPO, mismo truco de
    # siempre para distinguir un tipo primitivo de uno definido por
    # ustedes.
    'parametro : IDENTIFICADOR DOSPUNTOS IDENTIFICADOR'
    linea, columna = posicion(p, 1)
    p[0] = Parametro(p[1], p[3], linea, columna)


def p_instruccion_return(p):
    'instruccion : RETURN expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Return(p[2], linea, columna)


def p_expresion_llamada(p):
    'expresion : IDENTIFICADOR PARIZQ argumentos PARDER'
    linea, columna = posicion(p, 1)
    p[0] = Llamada(p[1], p[3], linea, columna)


def p_argumentos_lista(p):
    'argumentos : argumentos COMA expresion'
    p[0] = p[1] + [p[3]]


def p_argumentos_una(p):
    'argumentos : expresion'
    p[0] = [p[1]]


def p_argumentos_vacia(p):
    'argumentos : '
    # foo()  — llamar sin argumentos también es válido.
    p[0] = []


# ---------------------------------------------------------------------------
# Asignación simple: nombre := expresion;
# ---------------------------------------------------------------------------

def p_instruccion_asignacion(p):
    'instruccion : IDENTIFICADOR ASIGNACION expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Asignacion(p[1], p[3], linea, columna)


# ---------------------------------------------------------------------------
# if / else
# ---------------------------------------------------------------------------

def p_instruccion_if_sin_else(p):
    'instruccion : IF expresion THEN bloque PUNTOCOMA %prec IFX'
    linea, columna = posicion(p, 1)
    p[0] = If(p[2], p[4], None, linea, columna)


def p_instruccion_if_con_else(p):
    'instruccion : IF expresion THEN bloque ELSE bloque PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = If(p[2], p[4], p[6], linea, columna)


# ---------------------------------------------------------------------------
# while, con y sin etiqueta
# ---------------------------------------------------------------------------

def p_instruccion_while(p):
    'instruccion : WHILE expresion DO bloque PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = While(p[2], p[4], None, linea, columna)


def p_instruccion_while_etiquetado(p):
    'instruccion : IDENTIFICADOR DOSPUNTOS WHILE expresion DO bloque PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = While(p[4], p[6], p[1], linea, columna)


# ---------------------------------------------------------------------------
# repeat...until
# ---------------------------------------------------------------------------

def p_instruccion_repeat(p):
    'instruccion : REPEAT instrucciones UNTIL expresion PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Repeat(p[2], p[4], linea, columna)


# ---------------------------------------------------------------------------
# case...of
# ---------------------------------------------------------------------------

def p_instruccion_case_sin_else(p):
    'instruccion : CASE expresion OF ramas END PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Case(p[2], p[4], None, linea, columna)


def p_instruccion_case_con_else(p):
    'instruccion : CASE expresion OF ramas ELSE bloque PUNTOCOMA END PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = Case(p[2], p[4], p[6], linea, columna)


def p_ramas_lista(p):
    'ramas : ramas rama'
    p[0] = p[1] + [p[2]]


def p_ramas_una(p):
    'ramas : rama'
    p[0] = [p[1]]


def p_rama(p):
    'rama : ENTERO DOSPUNTOS bloque PUNTOCOMA'
    linea, columna = posicion(p, 1)
    p[0] = RamaCase(p[1], p[3], linea, columna)


# ---------------------------------------------------------------------------
# break / continue
# ---------------------------------------------------------------------------

def p_instruccion_break(p):
    '''instruccion : BREAK PUNTOCOMA
                    | BREAK IDENTIFICADOR PUNTOCOMA'''
    linea, columna = posicion(p, 1)
    etiqueta = p[2] if len(p) == 4 else None
    p[0] = Break(etiqueta, linea, columna)


def p_instruccion_continue(p):
    '''instruccion : CONTINUE PUNTOCOMA
                    | CONTINUE IDENTIFICADOR PUNTOCOMA'''
    linea, columna = posicion(p, 1)
    etiqueta = p[2] if len(p) == 4 else None
    p[0] = Continue(etiqueta, linea, columna)


# ---------------------------------------------------------------------------
# Expresiones
# ---------------------------------------------------------------------------

def p_expresion_binaria(p):
    '''expresion : expresion MAS expresion
                 | expresion MENOS expresion
                 | expresion POR expresion
                 | expresion ENTRE expresion'''
    linea, columna = posicion(p, 2)
    p[0] = Aritmetica(p[1], p[2], p[3], linea, columna)


def p_expresion_comparacion(p):
    '''expresion : expresion IGUAL expresion
                 | expresion DISTINTO expresion
                 | expresion MENOR expresion
                 | expresion MAYOR expresion
                 | expresion MENORIGUAL expresion
                 | expresion MAYORIGUAL expresion'''
    linea, columna = posicion(p, 2)
    p[0] = Comparacion(p[1], p[2], p[3], linea, columna)


def p_expresion_negacion(p):
    'expresion : MENOS expresion %prec UMENOS'
    linea, columna = posicion(p, 1)
    p[0] = Negacion(p[2], linea, columna)


def p_expresion_agrupada(p):
    'expresion : PARIZQ expresion PARDER'
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
    p[0] = Literal(p[1].lower() == 'true', linea, columna)


def p_expresion_variable(p):
    'expresion : IDENTIFICADOR'
    # OJO: como `IDENTIFICADOR PARIZQ ...` (llamada) e `IDENTIFICADOR
    # CORCHETEIZQ ...` (indexado) son producciones DISTINTAS de esta,
    # LALR(1) las distingue con un solo token de anticipación (el que
    # venga después del identificador) — el mismo truco de siempre, no un
    # caso especial nuevo.
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


parser = yacc.yacc()


def parsear(texto):
    """Analiza `texto` y devuelve el AST (o None si hubo error de sintaxis)."""
    from lexer import lexer
    lexer.lineno = 1
    return parser.parse(texto, lexer=lexer)


if __name__ == '__main__':
    from entorno import Entorno
    from errores import ListaErrores
    from tabla_simbolos import TablaSimbolos

    codigo = """program Prueba;
begin
  function cuadrado(n: integer): integer;
  begin
    return n * n;
  end;

  writeln(cuadrado(5));
end.
"""
    arbol = parsear(codigo)
    print(f"AST construido: {arbol}")
    print("Ejecutando:")
    arbol.ejecutar(Entorno(), ListaErrores(), TablaSimbolos())
