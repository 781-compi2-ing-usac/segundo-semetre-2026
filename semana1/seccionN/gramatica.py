from ply import lex as lex  #importamos la funcionalidad del lexer
from ply import yacc as yacc  # importamos la funcionalidad del parser


# todas nuestras palabras reservadas deben ser declaradas en una tupla
reserved = {

} 

# los tokens se insertan en una lista para ser tomados en cuenta, mas adelantes se definen sus valores
tokens = [
    'SUMA', 'RESTA',
    'ENTERO'
    ]  

tokens += list(reserved.values()) # agregamos las palabras reservadas a la lista de tokens

# declaramos nuestros simbolos a manera de raw string
t_SUMA = r'\+' #se usa la barra de escape para indicar que no es un regex, aplcia para +*.?
t_RESTA = r'-'

# definimos las regex que necesitemos
def t_ENTERO(t):
    r'\d+' # regex para decimales r'[0-9]+(?:\.[0-9]+)*'
    t.value = float(t.value)
    return t

t_ignore = " \t\r"

def t_newline(t):
    r'\n+'

def t_error(t):
    print("ERROR LEXICO", str(t))

    t.lexer.skip(1)

# declaramos precedencia

precedence = (
    ('left', 'SUMA' ),
    ('left', 'RESTA')
)

#################### DECLARAMOS EL LEXER AQUI
lexer = lex.lex()

########################## FINALIZA DECLARACION DEL LEXER

def p_init(t):
    '''init : expresion SUMA expresion
            | expresion RESTA expresion'''
    if t[2] == '+'  : 
        print('SUMA: ' , t[1] , 'y' , t[3])
        t[0] = "Suma" + str(t[1] + t[3])
    elif t[2] == '-'  : 
        print('RESTA: ' , t[1] , 'y' , t[3])
        t[0]= "Suma" + str(t[1] - t[3])
    return t[0]

def p_expresion(t):
    '''expresion : ENTERO'''
    t[0] = t[1]

def p_error(t):
    print("ERROR: ", str(t))

parser = yacc.yacc()

def parse(input):
    lexer.lineno = 0
    print (parser.parse(input))


if __name__ == '__main__':
    #parse("5+5")
    #parse("1-2")
    parse("1.56+4")