"""
S : stmts

stmts : stmt stmts
      | stmt

stmt : type ID EQUALS E
      | ID EQUALS E
      | PRINT LPAREN E RPAREN
      | IF LPAREN E RPAREN block
      | WHILE LPAREN E RPAREN block

block : LKEY stmts RKEY      

type : int | float | bool

E : E LT E
    | E GT E
    | E LE E
    | E GE E
    | E EQ E
    | E PLUS E
    | E MINUS E
    | E TIMES E
    | E DIVIDE E
    | ID
    | num
    | true
    | false
    | LPAREN E RPAREN
"""
import ply.yacc as yacc
from mylexer import tokens
from AST.nodes import *

# precedence rules for the arithmetic operators
precedence = (
    ('left', 'EQ'),
    ('left', 'LT', 'GT', 'LE', 'GE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)

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
    p[0] = DeclarationNode(p[1], p[2], p[4])

def p_stmt_assignment_existing(p):
    'stmt : ID EQUALS E'
    p[0] = AssignmentNode(p[1], p[3])

def p_stmt_print(p):
    'stmt : PRINT LPAREN E RPAREN'
    p[0] = PrintNode(p[3])

def p_stmt_block(p):
    'stmt : IF LPAREN E RPAREN block'
    p[0] = IfNode(p[3], p[5])

def p_stmt_while(p):
    'stmt : WHILE LPAREN E RPAREN block'
    p[0] = WhileNode(p[3], p[5])

def p_block(p):
    'block : LKEY stmts RKEY'
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
    '''E : E PLUS E
         | E MINUS E
         | E TIMES E
         | E DIVIDE E'''    
    p[0] = BinaryOpNode(p[1], p[2], p[3])

def p_E_comparison(p):
    '''E : E LT E
         | E GT E
         | E LE E
         | E GE E
         | E EQ E'''
    p[0] = BinaryOpNode(p[1], p[2], p[3])

def p_E_id(p):
    'E : ID'    
    p[0] = VariableNode(p[1])

def p_E_num(p):
    'E : NUM'
    p_type = 'float' if isinstance(p[1], float) else 'int'  
    p[0] = PrimitiveNode(p[1], p_type)

def p_E_true(p):
    '''E : TRUE
         | FALSE'''        
    p[0] = PrimitiveNode(p[1], 'bool')

def p_E_group(p):
    'E : LPAREN E RPAREN'
    p[0] = p[2]

# Error rule for syntax errors

def p_error(p):
    print("Syntax error at '%s'" % p.value if p else "Syntax error at EOF")
    print("Error details:", p)

# Build the parser

parser = yacc.yacc()