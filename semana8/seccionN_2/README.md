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
                | condicional | bucle | transferencia
    imprimir : PRINT EXCLAMACION PARIZQ expresion PARDER PUNTOCOMA
    asigna_valor : LET ID IGUAL expresion PUNTOCOMA
                 | LET tipo ID IGUAL expresion PUNTOCOMA
    tipo : TIPOENTERO | FLOAT
    condicional : IF expresion LLAVE_OPEN bloque LLAVE_CIERRA
    bucle : WHILE expresion LLAVE_OPEN bloque LLAVE_CIERRA
    transferencia : BREAK PUNTOCOMA | CONTINUE PUNTOCOMA
    expresion : expresion DIGUAL expresion
              | expresion DIFERENTE expresion
              | expresion SUMA expresion
              | expresion RESTA expresion
              | expresion MULTIPLICACION expresion
              | ENTERO | DECIMAL | ID
```

Soportado y verificado en QEMU (`linked-build.sh`):
- Aritmetica `+ - *` con precedencia `*` > `+-`, modelo de pila (`PUSH/POP` en `sp`).
- Comparaciones `==`/`!=` (`cmp`/`fcmp` + `cset`, resultado int 0/1) usables en
  `println!`, `if` y `while`.
- `let [int|float] id = expr;` con tipos en `tablaSimbolos` (`insertar/buscar`).
- `println!(expr);` entero (`%d`/`w1`) y double (`%f`/`d0` + `.double`/`fmtf`).
- `if cond { ... }` (`cbz`/`fcmp+b.eq`, ambito hijo de tipos).
- `while cond { ... }` con `break`/`continue` (etiquetas `L_while_N`, pila de bucles
  para anidados).
- Registros scratch automaticos (`x9-x15`, `d8-d13` round-robin; solo `x0/w1/d0` fijos por ABI).
- `entrada.txt` (salida QEMU: `26 / 14 / 5.600000 / 1 / 23..1 / 17 / 0 / 4 / 3..1`):
  aritmetica, floats, `if` true/false, `while` con cuenta regresiva, `break`,
  `continue` e `if`/`while` con `==`/`!=`.

Pendiente (stubs `pass` en `Compilador`): funciones, structs.


## Instalar qemu

```bash
# debian/ubuntu/ mint
sudo apt-get install aarch64-linux-gnu-as aarch64-linux-gnu-ld qemu-aarch64   

# arch linux
pacman -Sy aarch64-linux-gnu-as aarch64-linux-gnu-ld qemu-aarch64   
```