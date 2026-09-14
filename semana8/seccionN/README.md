# Análisis semántico mediante esquemas de traducción dirigidos por la sintaxis

## Objetivo semanal
- Implementar la logica de declaracion de variables y resolución de expresiones.
- Implementar el reconocimiento diferenciado de INT y FLOAT.
- Implementar resolución de variables.
- Implementación funcion print

## Herramientas en el repo
- sh para la compilación del código
- logica para el guardado y ejecución del archivos ASM




## Compilador (`gramatica_compilador.py`) — implementado

```bnf
    init : bloque
    bloque : bloque instruccion | instruccion
    instruccion : asigna_valor | imprimir | expresion
    imprimir : PRINT EXCLAMACION PARIZQ expresion PARDER PUNTOCOMA
    asigna_valor : LET ID IGUAL expresion PUNTOCOMA
                 | LET tipo ID IGUAL expresion PUNTOCOMA
    tipo : TIPOENTERO | FLOAT
    expresion : expresion SUMA expresion
              | expresion RESTA expresion
              | expresion MULTIPLICACION expresion
              | ENTERO | DECIMAL | ID
```

Soportado y verificado en QEMU (`linked-build.sh` -> `26 / 14 / 2.500000`):
- Aritmetica `+ - *` con precedencia `*` > `+-`, modelo de pila (`PUSH/POP` en `sp`).
- `let [int|float] id = expr;` con tipos en `tablaSimbolos` (`insertar/buscar`).
- `println!(expr);` entero (`%d`/`w1`) y double (`%f`/`d0` + `.double`/`fmtf`).
- Registros scratch automaticos (`x9-x15`, `d8-d13` round-robin; solo `x0/w1/d0` fijos por ABI).
- `entrada.txt` valida actual:
  `let numero = 4*5+6; println!(numero); let x = 20-6; println!(x); let f = 2.5; println!(f);`
- Pruebas: `.venv/bin/python tests/test_compilador_minimo.py` (4 casos).

Pendiente (stubs `pass` en `Compilador`): `if/while`, `==/!=`, funciones, structs.


## Instalar qemu

```bash
# debian/ubuntu/ mint
sudo apt-get install aarch64-linux-gnu-as aarch64-linux-gnu-ld qemu-aarch64   

# arch linux
pacman -Sy aarch64-linux-gnu-as aarch64-linux-gnu-ld qemu-aarch64   
```