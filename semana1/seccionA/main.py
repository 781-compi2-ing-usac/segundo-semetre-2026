# Yacc example

"""
Grammar:
expression : expression PLUS term
            | expression MINUS term
            | term

term       : term TIMES factor
            | term DIVIDE factor
            | factor

factor     : NUMBER
            | LPAREN expression RPAREN
"""

import ply.yacc as yacc
import graphviz

dot = graphviz.Digraph(comment='Arithmetic Expression Grammar')

dot.attr('node', shape='circle')

OUTPUT_DIRECTORY = 'output'

# Get the token map from the lexer.  This is required.
from calclex import tokens

def p_expression_plus(p):
    'expression : expression PLUS term'
    p[0] = p[1] + p[3]

def p_expression_minus(p):
    'expression : expression MINUS term'
    p[0] = p[1] - p[3]

def p_expression_term(p):
    'expression : term'
    p[0] = p[1]

def p_term_times(p):
    'term : term TIMES factor'
    p[0] = p[1] * p[3]

def p_term_div(p):
    'term : term DIVIDE factor'
    p[0] = p[1] / p[3]

def p_term_factor(p):
    'term : factor'
    p[0] = p[1]

def p_factor_num(p):
    'factor : NUMBER'
    p[0] = p[1]

def p_factor_expr(p):
    'factor : LPAREN expression RPAREN'
    p[0] = p[2]

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")

# Build the parser
parser = yacc.yacc()

try:
    s = input('calc > ')
except EOFError:
    print("Exiting...")
    exit()
finally:
    result = parser.parse(s)
    print(result)