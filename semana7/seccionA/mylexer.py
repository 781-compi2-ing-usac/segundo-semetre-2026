import ply.lex as lex

reserved = {
    'int': 'INT',
    'float': 'FLOAT',
    'bool': 'BOOL',
    'true': 'TRUE',
    'false': 'FALSE',
    'if': 'IF',
    'while': 'WHILE',
    'print': 'PRINT',
    'fn': 'FUNCTION',    
    'return': 'RETURN',
    'void': 'VOID',
}

tokens = (        
    'ID',
    'NUM',    
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'LKEY',
    'RKEY',
    'LBRACE',
    'RBRACE',
    'EQUALS',
    'LT',
    'GT',
    'LE',
    'GE',
    'EQ',    
    'COLON',
    'COMMA',
) + tuple(reserved.values())

# Regular expression rules for simple tokens
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LKEY = r'\{'
t_RKEY = r'\}'
t_LBRACE = r'\['
t_RBRACE = r'\]'
t_EQUALS = r'='
t_LT = r'<'
t_GT = r'>'
t_LE = r'<='
t_GE = r'>='
t_EQ = r'=='
t_COLON = r':'
t_COMMA = r','

t_ignore = ' \t'

# Define a rule for each token type

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')  # Check for reserved words
    if t.type == 'TRUE':
        t.value = True
    elif t.type == 'FALSE':
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