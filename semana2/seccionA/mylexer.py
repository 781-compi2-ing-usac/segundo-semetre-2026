import ply.lex as lex

tokens = (
    'INT',
    'FLOAT',
    'BOOL',
    'ID',
    'NUM',
    'TRUE',
    'FALSE',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'LKEY',
    'RKEY',
    'EQUALS'
)

# Regular expression rules for simple tokens

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LKEY = r'\{'
t_RKEY = r'\}'
t_EQUALS = r'='
t_ID = r'[a-zA-Z_][a-zA-Z0-9_]*'

t_ignore = ' \t'

# Define a rule for each token type

def t_INT(t):
    r'int'
    t.value = 'int'
    return t

def t_FLOAT(t):
    r'float'
    t.value = 'float'
    return t

def t_BOOL(t):
    r'bool'
    t.value = 'bool'
    return t

def t_TRUE(t):
    r'true'
    t.value = True    
    return t

def t_FALSE(t):
    r'false'
    t.value = False    
    return t

def t_NUM(t):
    r'\d+(\.\d+)?'
    if '.' in t.value:
        t.value = float(t.value)        
    else:
        t.value = int(t.value)        
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Error handling rule

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()