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
                | condicional | bucle | transferencia | funcion | call_funcion
    funcion : FUNCTION ID PARIZQ PARDER LLAVE_OPEN bloque LLAVE_CIERRA
    call_funcion : ID PARIZQ PARDER PUNTOCOMA
    imprimir : PRINT EXCLAMACION PARIZQ expresion PARDER PUNTOCOMA
    asigna_valor : LET ID IGUAL expresion PUNTOCOMA
                 | LET tipo ID IGUAL expresion PUNTOCOMA
    tipo : TIPOENTERO | FLOAT
    condicional : IF expresion LLAVE_OPEN bloque LLAVE_CIERRA
    bucle : WHILE expresion LLAVE_OPEN bloque LLAVE_CIERRA
    transferencia : BREAK PUNTOCOMA | CONTINUE PUNTOCOMA
                  | RETURN PUNTOCOMA | RETURN expresion PUNTOCOMA
    expresion : expresion DIGUAL expresion
              | expresion DIFERENTE expresion
              | expresion SUMA expresion
              | expresion RESTA expresion
              | expresion MULTIPLICACION expresion
              | ENTERO | DECIMAL | ID | ID PARIZQ PARDER
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
- `def id() { ... }` sin parametros: cuerpos tras el `ret` de `main` (opcion B,
  `parse()` en dos pasadas), etiqueta `_fn_<id>`.
- `return [expr];`: valor en `x0` (int) / `d0` (float, AAPCS64) + `b L_fn_fin_N`;
  tipo inferido por pre-barrido (`inferir_retornos`, primer return con valor manda).
  `f()` como expresion apila el retorno; void sigue apilando dummy 0. Bare `return;`
  deja cero del tipo inferido; fuera de funcion se ignora (como `break`/`continue`).
- `call()` con `sp` alineado a 16 (relleno dummy si la pila esta impar).
- `entrada.txt` (salida QEMU: `26 / 14 / 5.600000 / 1 / 23..1 / 17 / 0 / 4 / 3..1 /
  99 / 2..1 / 2..1 / 99 / 0 / 42 / 1 / 2 / 2.500000`): aritmetica, floats,
  `if` true/false, `while` con cuenta regresiva, `break`, `continue`, `if`/`while`
  con `==`/`!=`, `def`+calls (incluye `while` interno, call como expresion y
  `return` int/float/temprano).
- Pruebas:
  - `.venv/bin/python tests/test_compilador_minimo.py` (4 casos: precedencia, resta, float, pila).
  - `.venv/bin/python tests/test_compilador_control.py` (5 casos: `if`, `while`, `break`, `continue`).
  - `.venv/bin/python tests/test_compilador_comparacion.py` (6 casos: `==`/`!=` int y float, `if`/`while` con comparacion).
  - `.venv/bin/python tests/test_compilador_funciones.py` (5 casos: call, doble call, `while` interno, dummy-0, cuerpo tras `ret`).
  - `.venv/bin/python tests/test_compilador_return.py` (6 casos: int, temprano, float, bare-0, en `if`/`while`, top-level ignorado).

Pendiente (stubs `pass` en `Compilador`): structs.


## Instalar qemu

```bash
# debian/ubuntu/ mint
sudo apt-get install aarch64-linux-gnu-as aarch64-linux-gnu-ld qemu-aarch64   

# arch linux
pacman -Sy aarch64-linux-gnu-as aarch64-linux-gnu-ld qemu-aarch64   
```