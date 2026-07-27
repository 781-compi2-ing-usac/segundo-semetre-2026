# Análisis semántico mediante esquemas de traducción dirigidos por la sintaxis

## Objetivo

Verificar semánticamente instrucciones y expresiones mediante reglas de tipos y esquemas de traducción dirigidos por la sintaxis.

## Gramática

```bnf
S → type id = E

type → int | float | bool

E → E + T
   | E - T
   | T

T → T * F
   | T / F
   | F

F → id
   | num
   | real
   | true
   | false
   | ( E )
```

## Instrucciones

Para cada caso:

1. Determinar el tipo resultante de la expresión.
2. Verificar la compatibilidad entre el tipo declarado y el tipo de la expresión.
3. Identificar si existe algún error semántico.
4. Dibujar el árbol de análisis sintáctico.
5. Explicar brevemente el resultado obtenido.

## Casos a evaluar

### Caso 1

```c
int x = 3 + 5 * 2;
```

### Caso 2

```c
bool bandera = 4 + 2;
```