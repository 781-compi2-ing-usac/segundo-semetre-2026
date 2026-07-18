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

dot = graphviz.Digraph(comment="Arithmetic Expression Grammar")

dot.attr("node", shape="circle")

OUTPUT_DIRECTORY = "output"

step = 0
node_stack = []

# Get the token map from the lexer.  This is required.
from calclex import tokens


def p_expression_plus(p):
    "expression : expression PLUS term"
    global step
    global dot
    global node_stack
    term_node = node_stack.pop()
    expr_node = node_stack.pop()
    step += 1
    dot.node(str(step), "+")    
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    step += 1
    dot.node(str(step), "E")
    dot.edge(str(step), str(expr_node))
    dot.edge(str(step), str(step - 1))
    dot.edge(str(step), str(term_node))
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    node_stack.append(step)
    p[0] = p[1] + p[3]

def p_expression_minus(p):
    "expression : expression MINUS term"
    global step
    global dot
    global node_stack
    term_node = node_stack.pop()
    expr_node = node_stack.pop()
    step += 1
    dot.node(str(step), "-")
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    step += 1
    dot.node(str(step), "E")    
    dot.edge(str(step), str(expr_node))
    dot.edge(str(step), str(step - 1))
    dot.edge(str(step), str(term_node))
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    node_stack.append(step)
    p[0] = p[1] - p[3]


def p_expression_term(p):
    "expression : term"
    global step
    global dot
    global node_stack
    term_node = node_stack.pop()
    step += 1
    dot.node(str(step), "E")
    dot.edge(str(step), str(term_node))
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    node_stack.append(step)
    p[0] = p[1]


def p_term_times(p):
    "term : term TIMES factor"
    global step
    global dot
    global node_stack
    factor_node = node_stack.pop()
    term_node = node_stack.pop()
    step += 1
    dot.node(str(step), "*")
    mul_node = step    
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    step += 1
    dot.node(str(step), "T")    
    dot.edge(str(step), str(term_node))
    dot.edge(str(step), str(mul_node))
    dot.edge(str(step), str(factor_node))
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    node_stack.append(step)
    p[0] = p[1] * p[3]


def p_term_div(p):
    "term : term DIVIDE factor"
    global step
    global dot
    global node_stack
    factor_node = node_stack.pop()
    term_node = node_stack.pop()
    step += 1
    dot.node(str(step), "/")
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    div_node = step
    step += 1
    dot.node(str(step), "T")    
    dot.edge(str(step), str(term_node))
    dot.edge(str(step), str(div_node))
    dot.edge(str(step), str(factor_node))
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    node_stack.append(step)
    p[0] = p[1] / p[3]


def p_term_factor(p):
    "term : factor"
    global step
    global dot
    global node_stack
    factor_node = node_stack.pop()
    step += 1
    dot.node(str(step), "T")
    dot.edge(str(step), str(factor_node))
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    node_stack.append(step)
    p[0] = p[1]


def p_factor_num(p):
    "factor : NUMBER"
    global step
    global dot
    global node_stack
    step += 1
    dot.node(str(step), str(p[1]))
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    step += 1
    dot.node(str(step), "F")
    dot.edge(str(step), str(step - 1))
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    node_stack.append(step)
    p[0] = p[1]


def p_factor_expr(p):
    "factor : LPAREN expression RPAREN"
    global step
    global dot
    global node_stack
    expr_node = node_stack.pop()
    step += 1
    dot.node(str(step), "F")
    dot.edge(str(step), str(expr_node))
    dot.render(filename=f"{OUTPUT_DIRECTORY}/step_{step}", format="png", cleanup=True)
    node_stack.append(step)
    p[0] = p[2]


# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")


# Build the parser
parser = yacc.yacc()

try:
    s = input("calc > ")
except EOFError:
    print("Exiting...")
    exit()
finally:
    result = parser.parse(s)
    print(result)

from pathlib import Path
from PIL import Image
import re

output_dir = Path("output")

# Ordenar correctamente por el número del archivo
files = sorted(
    output_dir.glob("step_*.png"),
    key=lambda p: int(re.search(r"step_(\d+)", p.stem).group(1))
)

# Cargar imágenes
images = [Image.open(f).convert("RGBA") for f in files]

# Calcular el tamaño máximo
max_width = max(img.width for img in images)
max_height = max(img.height for img in images)

frames = []

# Centrar cada imagen sobre un canvas del mismo tamaño
for img in images:
    canvas = Image.new("RGBA", (max_width, max_height), "white")

    x = (max_width - img.width) // 2
    y = (max_height - img.height) // 2

    canvas.paste(img, (x, y), img)
    frames.append(canvas.convert("P", palette=Image.ADAPTIVE))

# Guardar GIF
frames[0].save(
    "animation.gif",
    save_all=True,
    append_images=frames[1:],
    duration=1000,   # ms por frame
    loop=0,
    optimize=False,
)

print(f"GIF creado con {len(frames)} imágenes ({max_width}x{max_height}).")