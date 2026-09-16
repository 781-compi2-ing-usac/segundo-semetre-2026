from ply import lex as lex  # importamos la funcionalidad del lexer
from ply import yacc as yacc  # importamos la funcionalidad del parser
from interprete.expr_compilador import *
from interprete.instr_compilador import *
from interprete.compilador import *
from interprete.utils_compilador import *


# todas nuestras palabras reservadas deben ser declaradas en una tupla
reserved = {
    "let": "LET",
    "int": "TIPOENTERO",
    "float": "FLOAT",
    "if": "IF",
    "println": "PRINT",
    "def": "FUNCTION",
    "struct": "RESERVEDSTRUCT",
    "while": "WHILE",
    "break": "BREAK",
    "continue": "CONTINUE",
}

# los tokens se insertan en una lista para ser tomados en cuenta, mas adelantes se definen sus valores
tokens = [
    "PUNTOCOMA",
    "DOBDOT",
    "IGUAL",
    "COMA",
    "EXCLAMACION",
    "LLAVE_OPEN",
    "LLAVE_CIERRA",
    "PARIZQ",
    "PARDER",
    "SUMA",
    "RESTA",
    "MULTIPLICACION",
    "DIGUAL",
    "DIFERENTE",
    "ENTERO",
    "DECIMAL",
    "ID",
]

tokens += list(
    reserved.values()
)  # agregamos las palabras reservadas a la lista de tokens

# declaramos nuestros simbolos a manera de raw string
t_DIGUAL = r"=="
t_DIFERENTE = r"!="

t_SUMA = (
    r"\+"  # se usa la barra de escape para indicar que no es un regex, aplcia para +*.?
)
t_RESTA = r"-"
t_MULTIPLICACION = r"\*"
t_IGUAL = r"="
t_PUNTOCOMA = r";"
t_LLAVE_OPEN = r"{"
t_LLAVE_CIERRA = r"}"
t_PARIZQ = r"\("
t_PARDER = r"\)"
t_DOBDOT = r":"
t_COMA = r","
t_EXCLAMACION = r"!"


# definimos las regex que necesitemos
def t_DECIMAL(t):
    r"\d+\.\d+"
    t.value = float(t.value)
    return t


def t_ENTERO(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_ID(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    t.type = reserved.get(t.value, "ID")
    return t


t_ignore = " \t\r"


def t_newline(t):
    r"\n+"


def t_error(t):
    print("ERROR LEXICO", str(t))

    t.lexer.skip(1)


# declaramos precedencia

precedence = (
    ("left", "DIGUAL", "DIFERENTE"),
    ("left", "SUMA", "RESTA"),
    ("left", "MULTIPLICACION"),
)

#################### DECLARAMOS EL LEXER AQUI
lexer = lex.lex()

########################## FINALIZA DECLARACION DEL LEXER


def p_init(t):
    """init : bloque"""
    t[0] = t[1]


def p_bloque(t):
    "bloque : bloque instruccion"
    t[1].append(t[2])
    t[0] = t[1]
    return t[0]


def p_instruccion_singular(t):
    "bloque : instruccion"
    t[0] = [t[1]]


def p_instruccion(t):
    """instruccion : asigna_valor
    | imprimir
    | expresion
    | condicional
    | bucle
    | transferencia"""
    t[0] = t[1]
    return t[0]


# #########################################################
### FUNCION IMPRIMIR
def p_imprimir(t):
    "imprimir : PRINT EXCLAMACION PARIZQ expresion PARDER PUNTOCOMA"
    t[0] = Imprimir(t[4])


#### CONDICIONAL IF
def p_condicional(t):
    "condicional : IF expresion LLAVE_OPEN bloque LLAVE_CIERRA"
    t[0] = Condicional(t[2], t[4])


#### BUCLE WHILE
def p_bucle(t):
    "bucle : WHILE expresion LLAVE_OPEN bloque LLAVE_CIERRA"
    t[0] = Bucle(t[2], t[4])


def p_break(t):
    """transferencia : BREAK PUNTOCOMA
    | CONTINUE PUNTOCOMA"""
    if t[1] == "continue":
        t[0] = Continue()
    else:
        t[0] = Break()


def p_asignar(t):  # declaracion implicita
    "asigna_valor : LET ID IGUAL expresion PUNTOCOMA"
    t[0] = Asignacion(t[2], t[4], None)
    return t[0]


def p_asignar_explicita(t):  # declaracion explicita
    "asigna_valor : LET tipo ID IGUAL expresion PUNTOCOMA"
    t[0] = Asignacion(t[3], t[5], t[2])
    return t[0]


def p_tipo_dato(t):
    """tipo : TIPOENTERO
    | FLOAT"""
    t[0] = t[1]


def p_expresion(t):
    """expresion : expresion DIGUAL expresion
    | expresion DIFERENTE expresion
    | expresion SUMA expresion
    | expresion RESTA expresion
    | expresion MULTIPLICACION expresion"""
    operacion = ExpresionBinaria(t[1], t[3], t[2])
    t[0] = operacion
    return t[0]


def p_expresion_entero(t):
    "expresion : ENTERO"
    # t[0] = t[1]
    t[0] = ExpresionValor(t[1], "int")


def p_expresion_decimal(t):
    "expresion : DECIMAL"
    # t[0] = t[1]
    t[0] = ExpresionValor(t[1], "float")  # { "TIPO" : "FLOAT", "VALOR": t[1]}


def p_expresion_identificador(t):
    "expresion : ID"
    t[0] = ExpresionValor(t[1], "identificador")


def p_error(t):
    if t is None:
        print("ERROR sintáctico: fin de archivo inesperado, falta cerrar algo")
    else:
        print(
            f"ERROR sintáctico línea {t.lineno}: token inesperado {t.type} ({t.value!r})"
        )


parser = yacc.yacc()


def parse(input):
    lexer.lineno = 0
    arbol = parser.parse(input)
    # print(arbol)
    utils = Utils_compilador()
    utils.add_header()
    interprete = Compilador(utils)

    for rama in arbol:
        res = rama.accept(interprete)
        if isinstance(rama, Expresion):
            interprete.discard_result(res)
    utils.add_footer()

    utils.save_file()
    print(
        "========================El archivo fue guardado en object/expresion.py========================"
    )
    print("========================Codigo generado========================")
    print(utils.get_code())
    print("=================== resultado final========================")
    print(utils.exec_file())
    return utils.get_code()


if __name__ == "__main__":
    # parse("5+5")
    # parse("1 + 4 + 5")
    f = open("./entrada.txt", "r")
    input = f.read()
    print("================ENTRADA=====================")
    print(input)
    print("=================SALIDA=====================")
    parse(input)

    # parse("let int expr = 2.5 * 2.3 + 2; ")
