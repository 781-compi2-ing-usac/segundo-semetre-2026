# Semana 1

En el desarrollo del proyecto, la herramienta que utilizaremos para la creación de nuestro intérprete/compilador será **PLY** (Python Lex-Yacc). Esta herramienta nos permitirá definir la gramática de nuestro lenguaje y generar el analizador léxico y sintáctico de manera eficiente.

PLY es una implementación de las herramientas Lex y Yacc en Python, por lo que es un tipo de analizador LALR(1) en otras palabras, es un analizador **ascendente**.

## Visualización del recorrido del parser

El propósito de este proyecto es demostrar visualmente cómo un parser LALR(1) procesa una expresión aritmética paso a paso mediante un **recorrido ascendente** (*bottom-up*).

### Gramática utilizada

```
expression : expression PLUS term
           | expression MINUS term
           | term

term       : term TIMES factor
           | term DIVIDE factor
           | factor

factor     : NUMBER
           | LPAREN expression RPAREN
```

### Cómo funciona la animación

Cada producción de la gramática genera uno o más nodos en un grafo con **Graphviz**, y cada paso produce una imagen PNG que representa el estado del árbol de análisis en ese momento. La secuencia de imágenes forma una animación que muestra el recorrido del parser.

El proceso es el siguiente:

1. El lexer tokeniza la entrada (por ejemplo, `2 + 3 * 4` → `NUMBER(2) PLUS NUMBER(3) TIMES NUMBER(4)`).
2. El parser reduce los tokens aplicando las producciones de la gramática de abajo hacia arriba. Por ejemplo, primero reduce `NUMBER(2)` a `factor`, luego `factor` a `term`, luego `term` a `expression`.
3. Cada reducción crea nodos en el grafo y los conecta con sus hijos mediante edges, generando una imagen por cada paso.

### Mecanismo de conexión de nodos

Para que cada producción pueda conectar sus nodos con los nodos generados por sus producciones hijas, se utiliza una pila auxiliar (`node_stack`) que refleja la pila interna del parser:

- Cada producción hace **pop** de los IDs de nodo de sus hijos (los no-terminales del lado derecho).
- Crea su(s) propio(s) nodo(s) y los conecta con edges hacia los hijos.
- Hace **push** de su propio nodo interfaz para que la producción padre pueda encontrarlo.

De esta forma, cuando se reduce `term : term TIMES factor`, el parser sabe exactamente a qué nodos corresponden el `term` izquierdo y el `factor` derecho, y puede dibujar las aristas correctamente.

### Ejemplo: `2 + 3 * 4`

La animación muestra cómo el parser construye el árbol de abajo hacia arriba:

1. Primero se reducen los números individuales a `factor` → `term`.
2. Luego, por precedencia, `3 * 4` se reduce a un `term` con el operador `*`.
3. Finalmente, `2 + (3 * 4)` se reduce a la `expression` completa con el operador `+`.

Cada imagen `step_N.png` en el directorio `output/` captura el estado del grafo después de la N-ésima reducción, permitiendo visualizar el recorrido completo del parser LALR(1).