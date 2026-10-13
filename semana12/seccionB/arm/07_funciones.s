// ===========================================================================
// 07_funciones.s — dos funciones: una con dos parámetros y una recursiva.
//
//     ./build.sh 07_funciones.s
//
// Este archivo es el DESTINO de la semana. Léanlo antes de leer
// visitar_Funcion, visitar_Llamada y visitar_Return en generador_arm.py.
//
// En MiniPascal sería esto:
//
//     function suma(a: integer, b: integer): integer;
//     begin
//       return a + b;
//     end;
//
//     function factorial(n: integer): integer;
//     begin
//       if n <= 1 then begin return 1; end;
//       return n * factorial(n - 1);
//     end;
//
//     writeln(suma(2, 3));         // 5
//     writeln(factorial(5));       // 120
//
// Salida esperada:
//     5
//     120
//
// Lo que cambia frente a todo lo anterior: hasta hoy había UN frame, el
// de main. Ahora cada llamada crea el suyo, y lo suelta al volver. El
// mecanismo es el mismo del prólogo y el epílogo de main, repetido.
//
// Cuatro ideas, y solo cuatro:
//
//   1. Los argumentos viajan en x0, x1, x2... (hasta 8). Es una
//      CONVENCIÓN: nada en el procesador obliga a eso, pero quien llama
//      y quien es llamado tienen que ponerse de acuerdo.
//   2. El valor devuelto viaja en x0. Es la misma regla de siempre
//      ("toda expresión deja su resultado en x0") y por eso una llamada
//      se puede usar en cualquier lugar donde cabe una expresión.
//   3. `bl` salta y deja en x30 la dirección de retorno; `ret` salta a
//      esa dirección.
//   4. Como `bl` PISA x30, una función que llama a otra tiene que
//      guardar el suyo antes. Por eso TODAS guardan x29 y x30.
// ===========================================================================

.section .data

fmt_entero:
    .asciz "%ld\n"


.section .text
.global main

main:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    // main no declara variables, así que no hace falta `sub sp`.


    // =======================================================================
    // writeln(suma(2, 3));
    // =======================================================================
    //
    // Primero se calculan los argumentos, y CADA UNO se empuja a la pila.
    // ¿Por qué no dejar el 2 en x0 y el 3 en x1 directamente? Porque en un
    // caso real un argumento es una expresión cualquiera, y calcularla
    // usa x0 y x1 (el modelo de pila de siempre). El 2 se perdería. La pila
    // es lo único que sobrevive a eso.
    mov x0, #2
    str x0, [sp, #-16]!          // argumento 1 a la pila
    mov x0, #3
    str x0, [sp, #-16]!          // argumento 2 a la pila

    // Y recién cuando ya se calcularon todos, se sacan hacia los registros
    // en orden INVERSO: el último que entró es el argumento 2.
    ldr x1, [sp], #16            // x1 = argumento 2
    ldr x0, [sp], #16            // x0 = argumento 1

    bl fn_suma                   // x30 = dirección de la línea de abajo
    // Al volver, x0 trae el resultado: 5.

    mov x1, x0                   // x1 = el valor a imprimir
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf


    // =======================================================================
    // writeln(factorial(5));
    // =======================================================================
    mov x0, #5
    str x0, [sp, #-16]!
    ldr x0, [sp], #16            // x0 = argumento 1   (con UN solo argumento
                                 // el empujar y sacar es redundante; se deja
                                 // porque el generador no distingue casos)
    bl fn_factorial              // x0 = 120

    mov x1, x0
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf


    // --- Epílogo de main ---------------------------------------------------
    mov w0, #0
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret


// ===========================================================================
// suma(a, b) — la función más sencilla que hay
// ===========================================================================
fn_suma:
    // --- Prólogo: lo MISMO que main, ahora una vez por llamada -------------
    stp x29, x30, [sp, #-16]!    // guardar el fp y el lr de QUIEN LLAMÓ
    mov x29, sp                  // fp de ESTA llamada
    sub sp, sp, #32              // el frame: 2 celdas, una por parámetro

    // Los parámetros llegaron en registros; se copian a sus celdas, igual
    // que una `var` con valor inicial. A partir de aquí `a` y `b` son
    // variables comunes con su offset desde x29.
    str x0, [x29, #-16]          // a = x0
    str x1, [x29, #-32]          // b = x1

    // --- return a + b; -----------------------------------------------------
    ldr x0, [x29, #-16]          // x0 = a
    str x0, [sp, #-16]!
    ldr x0, [x29, #-32]          // x0 = b
    mov x1, x0
    ldr x0, [sp], #16
    add x0, x0, x1               // x0 = a + b
    b .Lsalida_suma              // return: un salto al epílogo

    mov x0, #0                   // (si el cuerpo terminara sin return)
.Lsalida_suma:
    // --- Epílogo -----------------------------------------------------------
    mov sp, x29                  // soltar el frame de esta llamada
    ldp x29, x30, [sp], #16      // restaurar el fp y el lr de quien llamó
    ret                          // saltar a x30


// ===========================================================================
// factorial(n) — una función que se llama a sí misma
// ===========================================================================
fn_factorial:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    sub sp, sp, #16              // el frame: 1 celda, para n
    str x0, [x29, #-16]          // n = x0

    // --- if n <= 1 then begin return 1; end; -------------------------------
    ldr x0, [x29, #-16]          // x0 = n
    str x0, [sp, #-16]!
    mov x0, #1
    mov x1, x0
    ldr x0, [sp], #16
    cmp x0, x1
    cset x0, le                  // x0 = 1 si n <= 1
    cmp x0, #0
    b.eq .Lfin_si                // falso: saltarse el bloque
    mov x0, #1                   // return 1
    b .Lsalida_factorial
.Lfin_si:

    // --- return n * factorial(n - 1); --------------------------------------
    ldr x0, [x29, #-16]          // x0 = n          (operando izquierdo)
    str x0, [sp, #-16]!          // empujarlo: la llamada de abajo va a pisar x0

    // El argumento: n - 1
    ldr x0, [x29, #-16]
    str x0, [sp, #-16]!
    mov x0, #1
    mov x1, x0
    ldr x0, [sp], #16
    sub x0, x0, x1               // x0 = n - 1
    str x0, [sp, #-16]!          // argumento 1 a la pila
    ldr x0, [sp], #16            // x0 = argumento 1

    bl fn_factorial              // LA LLAMADA RECURSIVA: x0 = factorial(n - 1)

    mov x1, x0                   // x1 = factorial(n - 1)   (operando derecho)
    ldr x0, [sp], #16            // x0 = n                  (de vuelta de la pila)
    mul x0, x0, x1               // x0 = n * factorial(n - 1)
    b .Lsalida_factorial

    mov x0, #0
.Lsalida_factorial:
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret


// ===========================================================================
// Qué pasa en la pila cuando se llama factorial(3)
// ---------------------------------------------------------------------------
// Cada llamada guarda SU n en SU frame, y por eso la n de factorial(3) no se
// confunde con la de factorial(2) aunque existan a la vez:
//
//     direcciones altas
//     ┌───────────────────────────┐
//     │ fp y lr de main           │  <- lo guardó main al entrar
//     ├───────────────────────────┤
//     │ fp y lr (de main)         │  <- prólogo de factorial(3)
//     │ n = 3                     │
//     │ [temporal: n = 3]         │  <- el operando izquierdo de n * ...
//     ├───────────────────────────┤
//     │ fp y lr (de factorial(3)) │  <- prólogo de factorial(2)
//     │ n = 2                     │
//     │ [temporal: n = 2]         │
//     ├───────────────────────────┤
//     │ fp y lr (de factorial(2)) │  <- prólogo de factorial(1)
//     │ n = 1                     │       aquí `n <= 1` es verdad y vuelve
//     └───────────────────────────┘
//     direcciones bajas   <- sp
//
// Cuando una llamada termina (`mov sp, x29` + `ldp`), `sp` vuelve
// EXACTAMENTE a donde estaba justo antes del `bl` que la creó. Y el
// temporal que empujó quien llamó está ahí, esperando. Por eso
// `ldr x0, [sp], #16` lo encuentra donde lo dejó.
//
// La línea que hace posible todo esto es `stp x29, x30, [sp, #-16]!`.
// Sin ella, factorial(2) pisaría el x30 de factorial(3) con su propio
// `bl`, y al volver `ret` saltaría a un lugar equivocado.
// ===========================================================================
