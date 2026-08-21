from ply import lex as lex  #importamos la funcionalidad del lexer
from ply import yacc as yacc  # importamos la funcionalidad del parser
from interprete.expresiones import * 
from interprete.instrucciones import *
from interprete.interprete import *


# todas nuestras palabras reservadas deben ser declaradas en una tupla
reserved = {
    'let' : 'LET',
    'int' : 'TIPOENTERO',
    'float' : 'FLOAT',
    'if' : 'IF',
    'print' : 'PRINT',
    'def' : 'FUNCTION',
    'struct' : 'RESERVEDSTRUCT'
} 

# los tokens se insertan en una lista para ser tomados en cuenta, mas adelantes se definen sus valores
tokens = [
    'PUNTOCOMA', 'DOBDOT','IGUAL', 'COMA',
    'LLAVE_OPEN', 'LLAVE_CIERRA', 'PARIZQ', 'PARDER',
    'SUMA', 'RESTA', 'MULTIPLICACION',
    'DIGUAL', 'DIFERENTE',
    'ENTERO', 'DECIMAL', 'ID'
    ]  

tokens += list(reserved.values()) # agregamos las palabras reservadas a la lista de tokens

# declaramos nuestros simbolos a manera de raw string
t_DIGUAL = r'=='
t_DIFERENTE = r'!='

t_SUMA = r'\+' #se usa la barra de escape para indicar que no es un regex, aplcia para +*.?
t_RESTA = r'-'
t_MULTIPLICACION = r'\*'
t_IGUAL = r'='
t_PUNTOCOMA = r';'
t_LLAVE_OPEN = r'{'
t_LLAVE_CIERRA = r'}'
t_PARIZQ = r'\('
t_PARDER = r'\)'
t_DOBDOT = r':'
t_COMA = R','

# definimos las regex que necesitemos
def t_DECIMAL(t):
    r'\d+.\d+'
    t.value = float(t.value)
    return t

def t_ENTERO(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value,'ID')
    return t

t_ignore = " \t\r"

def t_newline(t):
    r'\n+'

def t_error(t):
    print("ERROR LEXICO", str(t))

    t.lexer.skip(1)

# declaramos precedencia

precedence = (
    ('left', 'DIGUAL', 'DIFERENTE'),
    ('left', 'SUMA', 'RESTA' ),
    ('left', 'MULTIPLICACION')
)

#################### DECLARAMOS EL LEXER AQUI
lexer = lex.lex()

########################## FINALIZA DECLARACION DEL LEXER

def p_init(t):
    '''init : bloque'''
    t[0] = t[1]
    

def p_bloque(t):
    'bloque : bloque instruccion'
    t[1].append(t[2])
    t[0] = t[1]
    return t[0]

def p_instruccion_singular(t):
    'bloque : instruccion'
    t[0] = [t[1]]

def p_instruccion(t):
    '''instruccion : asigna_valor 
                   | condicional 
                   | imprimir
                   | funcion
                   | call_funcion
                   | struct_dcl'''
    t[0] = t[1]
    return t[0]

############ STRUCTS ################
### campos struct
def p_campo(t):
    'campo : ID DOBDOT tipo' 
    valor = Struct_campo(t[1], t[3])
    #print ('campo', str(valor.identificador))
    t[0] = valor

def p_struct_campos(t):
    'campos_struct : campos_struct COMA campo'
    t[1].append(t[3])
    t[0] = t[1]
    return t[0]
                    
def p_struct_campos_primer(t):
    'campos_struct : campo'
    print('cabeza', str(t[1]))
    t[0] = [t[1]]

### struct
def p_struct_decl(t):
    'struct_dcl : RESERVEDSTRUCT ID LLAVE_OPEN campos_struct LLAVE_CIERRA PUNTOCOMA'
    #print(t[2], t[4])
    t[0] = Struct_dcl(t[2], t[4])


############ inicializacion STRUCTS ################
### campos struct
def p_campo_init(t):
    'init_campo : ID IGUAL expresion' 
    t[0] = Struct_valor(t[1], t[3])

def p_init_struct_campos(t):
    'init_campos_struct : init_campos_struct COMA init_campo'
    t[1].append(t[3])
    t[0] = t[1]
                    
def p_init_struct_campos_primer(t):
    'init_campos_struct : init_campo'
    print('cabeza init', str(t[1]))
    t[0] = [t[1]]

### struct
def p_init_struct(t):
    'init_struct_dcl : ID LLAVE_OPEN init_campos_struct LLAVE_CIERRA'
    t[0] = Struct_init(t[1], t[3])



#########################################################
### FUNCION IMPRIMIR
def p_imprimir(t):
    'imprimir : PRINT PARIZQ expresion PARDER PUNTOCOMA'
    t[0] = Imprimir(t[3])

#### CONDICIONAL IF
def p_condicional(t):
    'condicional : IF expresion LLAVE_OPEN bloque LLAVE_CIERRA'
    t[0] = Condicional(t[2],t[4])

##### FUNCIONES
def p_funcion_paramless(t):
    'funcion : FUNCTION ID PARIZQ PARDER LLAVE_OPEN bloque LLAVE_CIERRA'
    t[0] = Funcion_paramless(t[2], t[6])

### LLAMADA FUNCION
def p_funcion_call(t):
    'call_funcion : ID PARIZQ PARDER PUNTOCOMA'
    t[0] = Funcion_exec(t[1])

def p_asignar(t):  # declaracion implicita
    'asigna_valor : LET ID IGUAL expresion PUNTOCOMA'  
    t[0] = Asignacion(t[2], t[4], None)
    return t[0]

def p_asignar_explicita(t):  # declaracion explicita
    'asigna_valor : LET tipo ID IGUAL expresion PUNTOCOMA'  
    t[0] = Asignacion(t[3], t[5], t[2])
    return t[0]

def p_tipo_dato(t):
    '''tipo : TIPOENTERO
            | FLOAT'''
    t[0] = t[1]

def p_expresion(t):
    '''expresion : expresion SUMA expresion
                 | expresion RESTA expresion
                 | expresion MULTIPLICACION expresion'''
    operacion = ExpresionBinaria(t[1], t[3], t[2])
    t[0] = operacion
    return t[0]

def p_expresion_entero(t):
    'expresion : ENTERO'
    #t[0] = t[1]
    t[0] = ExpresionValor(t[1], "int")

def p_expresion_decimal(t):
    'expresion : DECIMAL'
    #t[0] = t[1]
    t[0] = ExpresionValor(t[1], "float") #{ "TIPO" : "FLOAT", "VALOR": t[1]}

def p_expresion_identificador(t):
    'expresion : ID'
    t[0] = ExpresionValor(t[1], "identificador")

def p_expresion_funcion(t):
    'expresion : ID PARIZQ PARDER'
    t[0] = Funcion_exec(t[1])

def p_expresion_declaracion_struct(t):
    'expresion : init_struct_dcl'
    ### Aclarando: recordar que un struct es en esencia un tipo de dato definido por el usuario
    ### asi que al momento de retornarlo como un valor, es necesario definir su tipo como el
    ### TIPO DE STRUCT en este caso t[1].identificador
    print('validando tipo de struct', str(t[1].identificador))
    t[0] = ExpresionValor(t[1], t[1].identificador)

def p_error(t):
    if t is None:
        print("ERROR sintáctico: fin de archivo inesperado, falta cerrar algo")
    else:
        print(f"ERROR sintáctico línea {t.lineno}: token inesperado {t.type} ({t.value!r})")

parser = yacc.yacc()

def parse(input):
    lexer.lineno = 0
    arbol = parser.parse(input)
    print (arbol)

    interprete = Interprete()
    
    for rama in arbol:
        #print(type(rama))
        print(str(rama))
        rama.accept(interprete)


if __name__ == '__main__':
    #parse("5+5")
    #parse("1 + 4 + 5")
    f = open("./entrada.txt", "r")
    input = f.read()
    print('================ENTRADA=====================')
    print(input)
    print('=================SALIDA=====================')
    print(parse(input))
    #parse("let int expr = 2.5 * 2.3 + 2; ")