# Análisis semántico mediante esquemas de traducción dirigidos por la sintaxis

## Objetivo semanal
- Implementar un parent-pointing tree para el manejo los ámbitos de los bloques de código
- Implementación de control de flujo con instruccion if
- Implementación de declaración de funciones sin parametros y llamada de las mismas.
- Implementación funcion print
- Implementación de definicion de un struct
- Implementación de inicialización de un struct




```bnf
    init : bloque

    bloque : bloque instruccion
           | instruccion

    instruccion : asigna_valor 
                   | condicional 
                   | imprimir
                   | funcion
                   | call_funcion

    campo : ID DOBDOT tipo
    
    campos_struct : campos_struct COMA campo
                  | campo

    struct_dcl : RESERVEDSTRUCT ID LLAVE_OPEN campos_struct LLAVE_CIERRA PUNTOCOMA

    init_campo : ID IGUAL expresion

    init_campos_struct : init_campos_struct COMA init_campo
                       | init_campo

    init_struct_dcl : ID LLAVE_OPEN init_campos_struct LLAVE_CIERRA

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
              | init_struct_dcl

```