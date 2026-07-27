"""
S : stmts

stmts : stmt stmts
      | stmt

stmt : type ID EQUALS E
      | LKEY stmts RKEY

type : int | float | bool

E : E + T
   | E - T
   | T

T : T * F
   | T / F
   | F

F : id
   | num   
   | true
   | false
   | ( E )
"""
import ply.yacc as yacc
from mylexer import tokens
from AST.nodes import *

# Parsing rules

def p_S_stmts(p):
    'S : stmts'
    p[0] = p[1]

def p_stmts_multiple(p):
    'stmts : stmt stmts'
    p[0] = [p[1]] + p[2]

def p_stmts_single(p):
    'stmts : stmt'
    p[0] = [p[1]]

def p_stmt_assignment(p):
    'stmt : type ID EQUALS E'
    p[0] = AssignmentNode(p[1], p[2], p[4])

def p_stmt_block(p):
    'stmt : LKEY stmts RKEY'
    p[0] = BlockNode(p[2])

def p_type_int(p):
    'type : INT'
    p[0] = TypeNode('int')

def p_type_float(p):
    'type : FLOAT'
    p[0] = TypeNode('float')

def p_type_bool(p):
    'type : BOOL'
    p[0] = TypeNode('bool')

def p_E_binop(p):
    '''E : E PLUS T
         | E MINUS T'''
    p[0] = BinaryOpNode(p[1], p[2], p[3])

def p_T_binop(p):
    '''T : T TIMES F
         | T DIVIDE F'''
    p[0] = BinaryOpNode(p[1], p[2], p[3])

def p_E_T(p):
    'E : T'
    p[0] = p[1]

def p_T_F(p):
    'T : F'
    p[0] = p[1]

def p_F_id(p):
    'F : ID'
    p[0] = VariableNode(p[1])

def p_F_num(p):
    'F : NUM'
    p_type = 'float' if isinstance(p[1], float) else 'int'
    p[0] = PrimitiveNode(p[1], p_type)

def p_F_true(p):
    'F : TRUE'
    p[0] = PrimitiveNode(p[1], 'bool')

def p_F_false(p):
    'F : FALSE'
    p[0] = PrimitiveNode(p[1], 'bool')

def p_F_paren(p):
    'F : LPAREN E RPAREN'
    p[0] = p[2]

# Error rule for syntax errors

def p_error(p):
    print("Syntax error at '%s'" % p.value if p else "Syntax error at EOF")

# Build the parser

parser = yacc.yacc()