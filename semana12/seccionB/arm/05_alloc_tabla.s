// ===========================================================================
// 05_alloc_tabla.s — una rutina `alloc` y una TABLA de bloques reservados.
//
//     ./build.sh 05_alloc_tabla.s
//
// 04_brk.s pidió memoria a mano, una vez. Un programa real pide muchas
// veces, y necesita saber qué pidió. Hoy hacemos dos cosas:
//
//   1. `alloc`: una rutina que recibe cuántos bytes en x0 y devuelve en x0
//      la dirección del bloque. Es lo que `malloc` hace de cara al usuario.
//   2. La TABLA: cada vez que `alloc` reserva algo, anota una fila
//      (dónde empieza, cuánto mide). Es la contabilidad del heap.
//
// En MiniPascal sería, más o menos:
//
//     var a: array[4] of integer;     // 32 bytes
//     var b: array[2] of integer;     // 16 bytes
//     a[0] := 10;  a[3] := 40;  b[1] := 5;
//     writeln(a[0] + a[3]);           // 50
//     writeln(b[1]);                  // 5
//
// Y después de eso, para ver la tabla, imprimimos: cuántas filas hay, y el
// tamaño de cada una.
//
// Salida esperada:
//     50      a[0] + a[3]
//     5       b[1]
//     2       filas en la tabla
//     32      tamaño del bloque 0
//     16      tamaño del bloque 1
//     32      distancia entre el bloque 0 y el bloque 1
// ===========================================================================

.section .data

fmt_entero:
    .asciz "%ld\n"


// La tabla vive en .bss: memoria que existe desde que el programa arranca,
// ya en ceros, sin ocupar espacio en el archivo ejecutable.
.section .bss
.balign 8

tabla_heap:                      // 64 filas de 16 bytes: [base][tamaño]
    .skip 1024
tabla_n:                         // cuántas filas hay ocupadas
    .skip 8


.section .text
.global main

main:
    stp x29, x30, [sp, #-16]!
    mov x29, sp


    // --- var a: array[4] of integer; ----------------------------------------
    sub sp, sp, #16              // celda del frame para el PUNTERO de 'a'
    mov x0, #32                  // 4 enteros x 8 bytes
    bl alloc                     // x0 = dirección del bloque
    str x0, [x29, #-16]          // a = x0     la celda guarda una dirección

    // --- var b: array[2] of integer; ----------------------------------------
    sub sp, sp, #16
    mov x0, #16                  // 2 enteros x 8 bytes
    bl alloc
    str x0, [x29, #-32]          // b = x0


    // --- a[0] := 10;  a[3] := 40;  b[1] := 5; ------------------------------
    // Siempre dos pasos: traer el puntero del stack, y escribir a través de él.
    ldr x1, [x29, #-16]          // x1 = a  (el puntero)
    mov x0, #10
    str x0, [x1, #0]             // a[0] = 10      posición 0 * 8 = 0
    mov x0, #40
    str x0, [x1, #24]            // a[3] = 40      posición 3 * 8 = 24

    ldr x1, [x29, #-32]          // x1 = b
    mov x0, #5
    str x0, [x1, #8]             // b[1] = 5       posición 1 * 8 = 8


    // --- writeln(a[0] + a[3]); ----------------------------------------------
    ldr x1, [x29, #-16]
    ldr x0, [x1, #0]            // x0 = a[0]
    ldr x2, [x1, #24]           // x2 = a[3]
    add x1, x0, x2              // x1 = 50 (printf pide el valor en x1)
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf

    // --- writeln(b[1]); -----------------------------------------------------
    ldr x1, [x29, #-32]
    ldr x1, [x1, #8]
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf


    // --- Ver la tabla -------------------------------------------------------
    // Esto es lo que NO hace un programa MiniPascal por sí solo: la tabla
    // existe en el binario, pero nadie la imprime a menos que lo pidamos.
    adrp x2, tabla_n
    add  x2, x2, :lo12:tabla_n
    ldr  x1, [x2]                // x1 = tabla_n
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf                    // 2

    adrp x2, tabla_heap
    add  x2, x2, :lo12:tabla_heap
    ldr  x1, [x2, #8]            // fila 0, campo tamaño   (base en +0, tamaño en +8)
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf                    // 32

    adrp x2, tabla_heap
    add  x2, x2, :lo12:tabla_heap
    ldr  x1, [x2, #24]           // fila 1, campo tamaño   (cada fila mide 16)
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf                    // 16

    // Distancia entre bases: base de la fila 1 - base de la fila 0.
    adrp x2, tabla_heap
    add  x2, x2, :lo12:tabla_heap
    ldr  x3, [x2, #0]            // fila 0, base
    ldr  x4, [x2, #16]           // fila 1, base
    sub  x1, x4, x3
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf                    // 32: el bloque b empieza justo donde acaba a


    // --- Epílogo ------------------------------------------------------------
    mov w0, #0
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret


// ===========================================================================
// alloc — reservar x0 bytes en el heap y anotarlos en la tabla.
//
//   entrada:  x0 = cuántos bytes
//   salida:   x0 = dirección del bloque
//   pisa:     x1 .. x13 y x8 (no guarda nada en el stack; es una rutina
//             hoja: no llama a nadie, así que no toca x30)
//
// Los registros que usa son todos "de trabajo": por convención una función
// puede pisar x0-x15 sin avisar. Quien llame a alloc y necesite un valor
// después, lo guarda en el stack ANTES (el modelo de pila de siempre ya lo
// hace con los temporales de una expresión).
// ===========================================================================
alloc:
    mov x9, x0                   // x9 = n          (x0 se va a pisar con brk)

    mov x0, #0
    mov x8, #214
    svc #0                       // x0 = break actual = donde empieza el bloque
    mov x10, x0                  // x10 = base

    add x0, x10, x9              // x0 = base + n
    mov x8, #214
    svc #0                       // brk(base + n): el heap creció n bytes

    // --- anotar la fila en la tabla -----------------------------------------
    adrp x11, tabla_n
    add  x11, x11, :lo12:tabla_n
    ldr  x12, [x11]              // x12 = índice de la fila nueva

    adrp x13, tabla_heap
    add  x13, x13, :lo12:tabla_heap
    add  x13, x13, x12, lsl #4   // x13 = tabla_heap + índice * 16
    str  x10, [x13]              // fila.base   = base
    str  x9,  [x13, #8]          // fila.tamaño = n

    add  x12, x12, #1
    str  x12, [x11]              // tabla_n += 1

    mov x0, x10                  // el resultado: la base del bloque
    ret

    // ------------------------------------------------------------------
    // LO QUE FALTA AQUÍ:
    //   * Comprobar que brk devolvió base + n. Si no, x0 debería salir 0.
    //   * Qué pasa con la fila 65: la tabla tiene 64 y nada lo revisa.
    //   * Qué más debería saber la tabla de cada bloque (¿de qué tipo es?
    //     ¿sigue en uso?). Dos campos alcanzan para entender el mecanismo;
    //     no necesariamente alcanzan para su proyecto.
    // ------------------------------------------------------------------
