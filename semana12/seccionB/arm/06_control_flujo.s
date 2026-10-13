// ===========================================================================
// 06_control_flujo.s — un ciclo, dos condicionales, un break y un continue.
//
//     ./build.sh 06_control_flujo.s
//
// Este archivo es el DESTINO de la semana, igual que 03_variables.s lo fue
// de la de variables. Léanlo antes de leer visitar_If y visitar_While en
// generador_arm.py.
//
// En MiniPascal sería esto:
//
//     var i: integer := 0;
//     var suma: integer := 0;
//     while i < 10 do begin
//       i := i + 1;
//       if i == 3 then begin continue; end;   // saltarse el 3
//       if i > 5 then begin break; end;       // cortar al pasar de 5
//       suma := suma + i;
//     end;
//     writeln(suma);                          // 1 + 2 + 4 + 5 = 12
//
// Salida esperada:
//     12
//
// La idea de todo el archivo, en una frase:
//
//     un `if` y un `while` NO son instrucciones. Son una forma de
//     acomodar etiquetas y saltos alrededor de otras instrucciones.
//
// Hay tres piezas nuevas, y solo tres:
//
//     cmp  a, b        comparar. NO devuelve nada: deja el resultado en
//                      cuatro banderas internas del procesador (NZCV).
//     cset x0, lt      leer esas banderas: x0 = 1 si "menor que", si no 0.
//     b.eq etiqueta    saltar si la última comparación dio "igual".
//     b    etiqueta    saltar siempre (el `b` solo, sin condición).
// ===========================================================================

.section .data

fmt_entero:
    .asciz "%ld\n"


.section .text
.global main

main:
    // --- Prólogo -----------------------------------------------------------
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    sub sp, sp, #32              // el frame ENTERO, de una vez: 2 variables
    // CAMBIÓ frente a 03_variables.s: allá cada `var` hacía su propio
    // `sub sp, sp, #16`. Aquí no. Ver la nota "por qué el frame se reserva
    // de una vez" al final del archivo.


    // --- var i: integer := 0; ----------------------------------------------
    mov x0, #0
    str x0, [x29, #-16]          // i = 0       i vive en [x29, #-16]

    // --- var suma: integer := 0; -------------------------------------------
    mov x0, #0
    str x0, [x29, #-32]          // suma = 0    suma vive en [x29, #-32]


    // =======================================================================
    // while i < 10 do begin ... end;
    //
    //   inicio:
    //       <condicion>
    //       si es falso -> fin
    //       <cuerpo>
    //       saltar a inicio          <- ESTE salto hacia atrás es el ciclo
    //   fin:
    // =======================================================================
.Lmientras_inicio:

    // --- condición: i < 10 --------------------------------------------------
    // El mismo modelo de pila de siempre: izquierdo, empujar, derecho...
    ldr x0, [x29, #-16]          // x0 = i
    str x0, [sp, #-16]!          // empujar el izquierdo
    mov x0, #10                  // x0 = 10
    mov x1, x0                   // x1 = el derecho
    ldr x0, [sp], #16            // x0 = el izquierdo (de vuelta)
    // ...y aquí, en vez de `add`, la comparación:
    cmp x0, x1                   // i - 10, y recordar el signo en las banderas
    cset x0, lt                  // x0 = 1 si i < 10, si no 0

    // La condición ya es un 0 o un 1 en x0. Saltar si es 0:
    cmp x0, #0
    b.eq .Lmientras_fin          // falso: salir del ciclo

    // Un humano escribiría solo esto en lugar de las cinco líneas de arriba:
    //
    //     cmp x0, x1
    //     b.ge .Lmientras_fin    // "si i >= 10, salir"
    //
    // Es más corto, pero ya no deja la comparación como un valor que se
    // pueda guardar o imprimir. El generador prefiere que una comparación
    // sea una expresión más, igual que `a + b`.


    // --- i := i + 1; -------------------------------------------------------
    ldr x0, [x29, #-16]
    str x0, [sp, #-16]!
    mov x0, #1
    mov x1, x0
    ldr x0, [sp], #16
    add x0, x0, x1
    str x0, [x29, #-16]


    // --- if i == 3 then begin continue; end; ------------------------------
    //
    //       <condicion>
    //       si es falso -> fin_si
    //       <bloque>                  (aquí, un continue)
    //   fin_si:
    ldr x0, [x29, #-16]
    str x0, [sp, #-16]!
    mov x0, #3
    mov x1, x0
    ldr x0, [sp], #16
    cmp x0, x1
    cset x0, eq                  // x0 = 1 si i == 3
    cmp x0, #0
    b.eq .Lfin_si_a              // falso: saltarse el bloque

    b .Lmientras_inicio          // continue: volver a evaluar la condición
.Lfin_si_a:


    // --- if i > 5 then begin break; end; ----------------------------------
    ldr x0, [x29, #-16]
    str x0, [sp, #-16]!
    mov x0, #5
    mov x1, x0
    ldr x0, [sp], #16
    cmp x0, x1
    cset x0, gt                  // x0 = 1 si i > 5
    cmp x0, #0
    b.eq .Lfin_si_b

    b .Lmientras_fin             // break: salir del ciclo
.Lfin_si_b:


    // --- suma := suma + i; -------------------------------------------------
    ldr x0, [x29, #-32]
    str x0, [sp, #-16]!
    ldr x0, [x29, #-16]
    mov x1, x0
    ldr x0, [sp], #16
    add x0, x0, x1
    str x0, [x29, #-32]

    b .Lmientras_inicio          // fin del cuerpo: otra vuelta
.Lmientras_fin:


    // --- writeln(suma); ----------------------------------------------------
    ldr x1, [x29, #-32]
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf


    // --- Epílogo -----------------------------------------------------------
    mov w0, #0
    mov sp, x29
    ldp x29, x30, [sp], #16
    ret

// ===========================================================================
// `break` y `continue` son un `b` y nada más
// ---------------------------------------------------------------------------
// Fíjense que no hay ninguna instrucción llamada "break". Un break es un
// salto a la etiqueta de FIN del ciclo; un continue es un salto a la
// etiqueta de INICIO. Lo único que el compilador tiene que saber es cuáles
// son esas dos etiquetas para el ciclo en el que está parado: por eso
// `generador_arm.py` lleva una pila de ciclos abiertos (`self.ciclos`).
//
// ---------------------------------------------------------------------------
// Por qué el frame se reserva de una vez
// ---------------------------------------------------------------------------
// En la semana de variables, cada `var` escribía su propio `sub sp, sp,
// #16`. Funcionaba por una razón que no se veía: cada declaración se
// ejecutaba exactamente UNA vez, en el orden en que aparecía.
//
// Con saltos eso deja de ser cierto:
//
//   * Una `var` dentro de un `if` que no se toma NO se ejecuta, pero su
//     offset ya se repartió al generar. La variable siguiente queda
//     por debajo de `sp`, y el siguiente empujón de una expresión la pisa.
//   * Una `var` dentro de un `while` se ejecuta en cada vuelta: cada vuelta
//     mueve `sp` 16 bytes más y no los devuelve.
//
// Las dos fallas se comprueban: un programa corto con cada una da un
// resultado equivocado (imprime 2 donde debía imprimir 43) y el otro,
// con una declaración dentro de un ciclo de 3 millones de vueltas, termina
// con "Segmentation fault". La solución es reservar el frame ENTERO al entrar a la función,
// con el tamaño final, y dejar que cada `var` solo escriba en su celda. Eso
// es lo que ven en el prólogo de arriba.
// ===========================================================================
