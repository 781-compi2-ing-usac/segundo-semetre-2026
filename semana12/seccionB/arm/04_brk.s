// ===========================================================================
// 04_brk.s — pedirle memoria al kernel: la syscall 214, `brk`.
//
//     ./build.sh 04_brk.s
//
// Hasta hoy, toda la memoria del programa vivía en el stack: se reservaba
// con `sub sp` y se soltaba con `mov sp, x29`. Eso sirve mientras uno sabe,
// al escribir el compilador, cuánto va a necesitar y cuánto va a durar.
// Para todo lo demás existe el HEAP: memoria que se le pide al sistema
// operativo mientras el programa corre.
//
// ¿Cómo se pide? Igual que se pidió `write` en 01_hola.s: con una syscall.
// Se pone el número en x8 y se ejecuta `svc #0` (SuperVisor Call: "kernel,
// haz esto por mí").
//
//     write  ->  64        (la vieron en 01_hola.s)
//     exit   ->  93
//     brk    ->  214       (la de hoy)
//
// ¿Qué hace brk?
// ---------------
// El kernel guarda, para cada programa, una dirección llamada PROGRAM
// BREAK: donde termina la memoria de datos que ese programa tiene. Todo lo
// que está debajo del break se puede usar; lo que está arriba, no.
//
//     brk(0)       ->  devuelve el break actual (no cambia nada)
//     brk(dir)     ->  mueve el break a `dir` y devuelve el break nuevo
//
// Pedir N bytes es, entonces: leer el break, pedir break + N, y usar lo que
// quedó entre los dos. Eso es TODO el heap. `malloc` es esto, con más
// contabilidad alrededor.
//
// Salida esperada:
//     64
//     42
//     7
// ===========================================================================

.section .data

fmt_entero:
    .asciz "%ld\n"


.section .text
.global main

main:
    // --- Prólogo (el de siempre) --------------------------------------------
    stp x29, x30, [sp, #-16]!
    mov x29, sp


    // --- 1. ¿Dónde empieza la memoria nueva?  brk(0) ------------------------
    mov x0, #0                   // argumento: 0 = "no muevas nada, solo dime"
    mov x8, #214                 // 214 = brk
    svc #0                       // x0 = el break actual
    sub sp, sp, #16              // una celda del frame para guardarlo
    str x0, [x29, #-16]          // inicio = x0       vive en [x29, #-16]
    // Fíjense en lo que acaba de pasar: 'inicio' es una variable más, con su
    // celda en el stack. Lo que guarda no es un número cualquiera sino una
    // DIRECCIÓN: la de un lugar que ni siquiera existía hace un instante.


    // --- 2. Pedir 64 bytes: brk(inicio + 64) --------------------------------
    add x0, x0, #64             // x0 = inicio + 64   (x0 todavía vale `inicio`)
    mov x8, #214
    svc #0                      // x0 = el break nuevo
    ldr x1, [x29, #-16]         // x1 = inicio
    sub x1, x0, x1              // x1 = break nuevo - inicio = cuánto creció

    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf                   // imprime 64


    // --- 3. Escribir dentro del bloque --------------------------------------
    // Los 64 bytes arrancan en `inicio`. Dos enteros caben en los primeros 16.
    ldr x1, [x29, #-16]         // x1 = inicio  (la celda guarda la dirección)
    mov x0, #42
    str x0, [x1]                // *inicio = 42         escribir A TRAVÉS del puntero
    mov x0, #7
    str x0, [x1, #8]            // *(inicio + 8) = 7    el siguiente entero: +8 bytes


    // --- 4. Leerlos de vuelta -----------------------------------------------
    // Dos `ldr` seguidos: el primero trae el puntero desde el stack, el
    // segundo trae el valor desde el heap. Es la novedad de hoy, y es todo.
    ldr x1, [x29, #-16]         // x1 = inicio   (leer el puntero, del stack)
    ldr x1, [x1]                // x1 = *inicio  (leer el valor, del heap)
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf                   // imprime 42

    ldr x1, [x29, #-16]
    ldr x1, [x1, #8]            // x1 = *(inicio + 8)
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf                   // imprime 7


    // --- Epílogo ------------------------------------------------------------
    mov w0, #0
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret

// ===========================================================================
// Cosas que conviene notar
// ---------------------------------------------------------------------------
//  * El heap NO se suelta con `mov sp, x29`. El epílogo de arriba solo
//    devuelve el stack; el break se queda donde lo dejamos. Cuando el
//    programa termina, el kernel recoge todo. Cuándo soltar un bloque
//    ANTES de eso es otra pregunta (y no la respondemos hoy).
//
//  * La memoria que entrega brk viene en CEROS. No es magia del lenguaje:
//    es que el kernel nunca le entrega a un programa páginas con datos de
//    otro. Por eso un arreglo recién reservado vale 0 en todas sus casillas
//    sin que el programa haya escrito nada.
//
//  * Si el kernel no puede darte la memoria, `brk` NO falla con un error:
//    devuelve el break de antes, sin moverlo. La única forma de enterarse
//    es comparar lo que devolvió con lo que pediste. Este archivo no lo
//    comprueba (LO QUE FALTA AQUÍ).
// ===========================================================================
