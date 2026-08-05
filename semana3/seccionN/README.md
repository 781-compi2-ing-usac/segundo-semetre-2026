# Análisis semántico mediante esquemas de traducción dirigidos por la sintaxis

## Objetivo

- Implementar el patrón visitor para facilitar el desplazamiento a través del árbol sintáctico. 
- Implementar la base del chequeo semántico de tipos. 

```bnf
init    → instruccion instruccion
        | instruccion

instruccion → asigna_valor

asigna_valor → 'let' ID = expresion ;
             | 'let' tipo ID = expresion ;

tipo → TIPOENTERO
            | FLOAT

expresion   → expresion + expresion
            | expresion - expresion
            | expresion * expresion
            | ENTERO
            | DECIMAL

```