// ===========================================================================
// 03_variables.s — dos variables en el stack: reservarlas, leerlas,
// reasignarlas.
//
// Este archivo es el DESTINO de hoy, igual que 02_aritmetica.s lo fue de
// la Sesión 1. Léanlo antes de leer generador_arm.py.
//
//     ./build.sh 03_variables.s
//
// Lo que hace, en MiniPascal, sería esto:
//
//     var a: integer := 10;
//     var b: integer := 20;
//     a := a + b;
//     writeln(a);            // 30
//
// La novedad frente a 02_aritmetica.s: ahí `sp` solo se movía DENTRO de
// una expresión, y siempre volvía a su lugar (cada `str ... [sp,#-16]!`
// tenía su `ldr ... [sp],#16`). Hoy, además, `sp` se mueve una vez por
// cada `var` y NO vuelve — porque una variable, a diferencia de un
// resultado intermedio, tiene que seguir viva después de la instrucción
// que la creó. Las dos cosas conviven en el mismo archivo sin pisarse:
// ver la nota "por qué no chocan" más abajo.
// ===========================================================================

.section .data

fmt_entero:
    .asciz "%ld\n"


.section .text
.global main

main:
    // --- Prólogo -----------------------------------------------------------
    stp x29, x30, [sp, #-16]!   // guardar frame pointer y dirección de retorno
    mov x29, sp
    // x29 queda apuntando AQUÍ, al borde de arriba del stack frame, y no se
    // mueve más hasta el epílogo. Todo offset de variable se mide desde
    // este punto fijo — por eso conviene llamarlo el FRAME POINTER: un
    // punto de referencia que no cambia aunque sp sí lo haga.


    // --- var a: integer := 10; ----------------------------------------------
    sub sp, sp, #16              // reservar la celda de 'a'  (16, no 8: alineación)
    mov x0, #10                  // x0 = 10          (valor inicial)
    str x0, [x29, #-16]          // a = x0            'a' vive en [x29, #-16]
    // A PARTIR DE AQUÍ, 'a' es el nombre que el COMPILADOR le da a la
    // dirección [x29, #-16]. Esa asociación — nombre → offset — no existe
    // en tiempo de ejecución: el procesador no sabe que hay una variable
    // llamada 'a', solo sabe que hay un entero en esa dirección de memoria.
    // "a" es información que solo existió mientras generábamos este
    // archivo, y quedó congelada en el número -16.

    // --- var b: integer := 20; ----------------------------------------------
    sub sp, sp, #16              // reservar la celda de 'b'
    mov x0, #20
    str x0, [x29, #-32]          // b = x0            'b' vive en [x29, #-32]
    // Offset -32, no -16: la celda de 'a' ya ocupaba [x29, #-16]. Cada
    // variable nueva recibe el SIGUIENTE offset libre, igual que un
    // programa en Python le daría la siguiente casilla libre de una lista.


    // --- a := a + b; ---------------------------------------------------------
    // Esto es el modelo de pila de la Sesión 1, SIN cambios: leer dos
    // valores, sumarlos, y el resultado queda en x0. Lo único nuevo es de
    // DÓNDE salen esos valores: ya no son literales (mov x0, #N), son
    // lecturas de memoria (ldr x0, [x29, #-offset]).
    ldr x0, [x29, #-16]          // x0 = a  (leer la variable, no mov)
    str x0, [sp, #-16]!          // empujarlo — esto SÍ es temporal, va y viene
    ldr x0, [x29, #-32]          // x0 = b
    mov x1, x0                   // x1 = b
    ldr x0, [sp], #16            // x0 = a   (recuperar de la pila)
    add x0, x0, x1                // x0 = a + b = 30
    str x0, [x29, #-16]          // a = x0   (reasignación: MISMO offset de siempre)
    // 'a := ...' nunca reserva una celda nueva ni cambia su offset. Solo
    // sobrescribe lo que ya había en [x29, #-16]. Declarar reserva
    // memoria UNA vez; asignar solo la vuelve a llenar.


    // --- writeln(a); -----------------------------------------------------
    ldr x0, [x29, #-16]          // x0 = a  (30)
    mov x1, x0
    adrp x0, fmt_entero
    add  x0, x0, :lo12:fmt_entero
    bl printf


    // --- Epílogo -----------------------------------------------------------
    mov w0, #0
    mov sp, x29                  // NUEVO: soltar TODO lo reservado con 'sub sp' de
                                  // una sola vez, devolviendo sp a donde x29 lo
                                  // dejó en el prólogo. Sin esta línea, 'ldp' de
                                  // abajo leería del lugar equivocado — no del
                                  // par (x29, x30) que guardamos al empezar, sino
                                  // de dos celdas de variables.
    ldp x29, x30, [sp], #16
    ret

// ===========================================================================
// Por qué el stack de variables y el stack de expresiones no chocan
// ---------------------------------------------------------------------------
// Dos usos de sp conviven en este archivo y no se pisan, por una sola
// razón: las variables se DIRIGEN por x29 (que nunca se mueve), y el
// modelo de pila de expresiones siempre deja sp exactamente donde lo
// encontró (cada empujón tiene su saque, en el mismo bloque). Por eso da
// igual cuántas veces empuje y saque una expresión: cuando termina, sp
// vuelve a estar donde estaba, y [x29, #-16] sigue siendo 'a' pase lo que
// pase adentro de esa expresión.
// ===========================================================================
