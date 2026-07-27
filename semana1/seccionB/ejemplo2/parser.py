import ply.yacc as yacc

from lexer import tokens  # el parser necesita conocer los mismos tokens

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)


def p_expression_plus(p):
    'expression : expression PLUS expression'
    p[0] = p[1] + p[3]


def p_expression_minus(p):
    'expression : expression MINUS expression'
    p[0] = p[1] - p[3]


def p_expression_times(p):
    'expression : expression TIMES expression'
    p[0] = p[1] * p[3]


def p_expression_divide(p):
    'expression : expression DIVIDE expression'
    p[0] = p[1] / p[3]


def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]


def p_expression_number(p):
    'expression : NUMBER'
    p[0] = p[1]


def p_error(p):
    if p:
        print(f"Error de sintaxis en {p.value!r}")
    else:
        print("Error de sintaxis: entrada incompleta")


parser = yacc.yacc()


if __name__ == '__main__':
    # Permite correr "python parser.py" para probar lexer + parser
    # juntos con una expresión fija, sin necesidad del REPL de main.py
    from lexer import lexer

    data = "3 + 4 * (2 - 1)"
    resultado = parser.parse(data, lexer=lexer)
    print(f"Expresión: {data}")
    print(f"Resultado: {resultado}")