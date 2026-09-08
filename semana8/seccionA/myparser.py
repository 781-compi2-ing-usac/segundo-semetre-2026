"""
S : stmts

stmts : stmt stmts
      | stmt

stmt : type ID EQUALS E
      | ID braces EQUALS E
      | PRINT LPAREN E RPAREN
      | IF LPAREN E RPAREN block
      | WHILE LPAREN E RPAREN block
      | FUNCTION ID LPAREN params RPAREN COLON type block
      | ID LPAREN args RPAREN
      | ret_stmt

ret_stmt : RETURN E
      | RETURN

block : LKEY stmts RKEY

params : params COMMA param
       | param
       |

param : type array_dimensions COLON ID

array_dimensions : array_dimensions LBRACE RBRACE
                 |

args : args COMMA E
     | E
     |

type : int | float | bool

E : E AMPERSAND E
  | E PIPE E
  | E_REL

E_REL : E_REL LT E_REL
      | E_REL GT E_REL
      | E_REL LE E_REL
      | E_REL GE E_REL
      | E_REL EQ E_REL
      | E_ARITH

E_ARITH : E_ARITH PLUS E_ARITH
        | E_ARITH MINUS E_ARITH
        | E_ARITH TIMES E_ARITH
        | E_ARITH DIVIDE E_ARITH
        | ID braces
        | NUM
        | TRUE
        | FALSE
        | LPAREN E RPAREN
        | ID LPAREN args RPAREN
        | LBRACE array RBRACE

braces : braces LBRACE E RBRACE
    | LBRACE E RBRACE
    |

array : array COMMA NUM
    | NUM
"""

import ply.yacc as yacc
from mylexer import tokens
from AST.errors import ParseError
from AST.nodes import *

# precedence rules for the arithmetic operators
precedence = (
    ("left", "AMPERSAND"),
    ("left", "EQ"),
    ("left", "LT", "GT", "LE", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE"),
)

# Parsing rules


def p_S_stmts(p):
    "S : stmts"
    p[0] = p[1]


def p_stmts_multiple(p):
    "stmts : stmt stmts"
    p[0] = [p[1]] + p[2]


def p_stmts_single(p):
    "stmts : stmt"
    p[0] = [p[1]]


def p_stmt_assignment(p):
    "stmt : type ID EQUALS E"
    p[0] = DeclarationNode(p[1], p[2], p[4], lineno=p.lineno(2))


def p_stmt_assignment_existing(p):
    "stmt : ID braces EQUALS E"
    p[0] = AssignmentNode(p[1], p[2], p[4], lineno=p.lineno(1))


def p_stmt_print(p):
    "stmt : PRINT LPAREN E RPAREN"
    p[0] = PrintNode(p[3], lineno=p.lineno(1))


def p_stmt_block(p):
    "stmt : IF LPAREN E RPAREN block"
    p[0] = IfNode(p[3], p[5], lineno=p.lineno(1))


def p_stmt_while(p):
    "stmt : WHILE LPAREN E RPAREN block"
    p[0] = WhileNode(p[3], p[5], lineno=p.lineno(1))


def p_stmt_function(p):
    "stmt : FUNCTION ID LPAREN params RPAREN COLON type block"
    p[0] = FunctionDeclarationNode(p[2], p[4], p[7], p[8], lineno=p.lineno(2))


def p_stmt_function_call(p):
    "stmt : ID LPAREN args RPAREN"
    p[0] = FunctionCallNode(p[1], p[3], lineno=p.lineno(1))


def p_stmt_return(p):
    "stmt : ret_stmt"
    p[0] = p[1]


def p_ret_stmt_return(p):
    "ret_stmt : RETURN E"
    p[0] = ReturnNode(p[2], lineno=p.lineno(1))


def p_ret_stmt_return_empty(p):
    "ret_stmt : RETURN"
    p[0] = ReturnNode(lineno=p.lineno(1))


def p_block(p):
    "block : LKEY stmts RKEY"
    p[0] = BlockNode(p[2], lineno=p.lineno(1))


def p_params_recursive(p):
    "params : params COMMA param"
    p[0] = p[1] + [p[3]]


def p_params(p):
    "params : param"
    p[0] = [p[1]]


def p_no_params(p):
    "params :"
    p[0] = []


def p_param(p):
    "param : type array_dimensions COLON ID"
    p[0] = ParamNode(p[1], p[4], p[2], lineno=p.lineno(4))


def p_array_dimensions_recursive(p):
    "array_dimensions : array_dimensions LBRACE RBRACE"
    p[0] = p[1] + [None]


def p_array_dimensions_empty(p):
    "array_dimensions :"
    p[0] = []


def p_args_recursive(p):
    "args : args COMMA E"
    p[0] = p[1] + [p[3]]


def p_args(p):
    "args : E"
    p[0] = [p[1]]


def p_no_args(p):
    "args :"
    p[0] = []


def p_type_int(p):
    "type : INT"
    p[0] = TypeNode("int", lineno=p.lineno(1))


def p_type_float(p):
    "type : FLOAT"
    p[0] = TypeNode("float", lineno=p.lineno(1))


def p_type_bool(p):
    "type : BOOL"
    p[0] = TypeNode("bool", lineno=p.lineno(1))


def p_type_void(p):
    "type : VOID"
    p[0] = TypeNode("void", lineno=p.lineno(1))


def p_E_logic(p):
    """E : E AMPERSAND E
    | E PIPE E"""
    p[0] = LogicOpNode(p[1], p[2], p[3], lineno=p.lineno(2))


def p_E_rel(p):
    "E : E_REL"
    p[0] = p[1]


def p_E_REL_binop(p):
    """E_REL : E_REL LT E_REL
    | E_REL GT E_REL
    | E_REL LE E_REL
    | E_REL GE E_REL
    | E_REL EQ E_REL"""
    p[0] = RelOpNode(p[1], p[2], p[3], lineno=p.lineno(2))


def p_E_REL_arith(p):
    "E_REL : E_ARITH"
    p[0] = p[1]


def p_E_ARITH_binop(p):
    """E_ARITH : E_ARITH PLUS E_ARITH
    | E_ARITH MINUS E_ARITH
    | E_ARITH TIMES E_ARITH
    | E_ARITH DIVIDE E_ARITH"""
    p[0] = ArithOpNode(p[1], p[2], p[3], lineno=p.lineno(2))


def p_E_ARITH_id(p):
    "E_ARITH : ID braces"
    p[0] = VariableNode(p[1], p[2], lineno=p.lineno(1))


def p_E_ARITH_num(p):
    "E_ARITH : NUM"
    p_type = "float" if isinstance(p[1], float) else "int"
    p[0] = PrimitiveNode(p[1], p_type, lineno=p.lineno(1))


def p_E_ARITH_true(p):
    """E_ARITH : TRUE
    | FALSE"""
    p[0] = PrimitiveNode(p[1], "bool", lineno=p.lineno(1))


def p_E_ARITH_group(p):
    "E_ARITH : LPAREN E RPAREN"
    p[0] = p[2]


def p_E_ARITH_function_call(p):
    "E_ARITH : ID LPAREN args RPAREN"
    p[0] = FunctionCallNode(p[1], p[3], lineno=p.lineno(1))


def p_E_ARITH_array(p):
    "E_ARITH : LBRACE array RBRACE"
    p[0] = ArrayNode(p[2], lineno=p.lineno(1))


def p_braces_recursive(p):
    "braces : braces LBRACE E RBRACE"
    p[0] = p[1] + [p[3]]


def p_braces_single(p):
    "braces : LBRACE E RBRACE"
    p[0] = [p[2]]


def p_braces_empty(p):
    "braces :"
    p[0] = []


def p_array_recursive(p):
    "array : array COMMA E"
    p[0] = p[1] + [p[3]]


def p_array_single(p):
    "array : E"
    p[0] = [p[1]]


# Error rule for syntax errors


def p_error(p):
    if p:
        raise ParseError(f"Syntax error at '{p.value}'", lineno=p.lineno)
    else:
        raise ParseError("Syntax error at EOF")


# Build the parser

parser = yacc.yacc()
