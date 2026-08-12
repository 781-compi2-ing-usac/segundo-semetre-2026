# Análisis semántico mediante esquemas de traducción dirigidos por la sintaxis

## Objetivo semanal
- Implementar un parent-pointing tree para el manejo los ámbitos de los bloques de código
- Implementación de control de flujo con instruccion if
- Implementación de declaración de funciones sin parametros y llamada de las mismas.
- Implementación funcion print




```bnf
    init : bloque

    bloque : bloque instruccion
           | instruccion

    instruccion : asigna_valor 
                   | condicional 
                   | imprimir
                   | funcion
                   | call_funcion

    imprimir : PRINT PARIZQ expresion PARDER PUNTOCOMA

    condicional : IF expresion LLAVE_OPEN bloque LLAVE_CIERRA

    funcion : FUNCTION ID PARIZQ PARDER LLAVE_OPEN bloque LLAVE_CIERRA'

    call_funcion : ID PARIZQ PARDER PUNTOCOMA

    asigna_valor : LET ID IGUAL expresion PUNTOCOMA
                 | LET tipo ID IGUAL expresion PUNTOCOMA

    tipo : TIPOENTERO
            | FLOAT

    expresion : expresion SUMA expresion
              | expresion RESTA expresion
              | expresion MULTIPLICACION expresion
              | ENTERO
              | DECIMAL
              | ID
              | ID PARIZQ PARDER

```