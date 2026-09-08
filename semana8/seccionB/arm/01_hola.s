// ===========================================================================
// 01_hola.s — imprimir texto en ARM64, hablándole al kernel directamente.
//
// Este archivo es para LEER, no para generar. Son seis instrucciones y
// explican el modelo completo de cómo un programa saca algo por pantalla
// en Linux. Sin esto, `bl printf` es magia; con esto, es una comodidad.
//
//     ./build.sh 01_hola.s
// ===========================================================================

// --- La sección de datos ---------------------------------------------------
// Aquí van las cosas que tienen que existir en memoria ANTES de que el
// programa arranque. `mensaje:` es una ETIQUETA: un nombre para una
// dirección. El ensamblador la sustituye por el número real.
.section .data

mensaje:
    .ascii "Hola desde ARM64\n"
// `.ascii` pone los bytes tal cual, SIN terminador. Al kernel no le hace
// falta: a `write` se le dice cuántos bytes escribir, no dónde termina.
// (`printf`, en cambio, sí necesita el cero final — para eso está `.asciz`,
// que es lo que usa el código generado por MiniPascal.)

longitud = . - mensaje
// `.` significa "la dirección de aquí mismo". Restándole la dirección de
// `mensaje` sale el tamaño en bytes, calculado por el ensamblador. Así no
// hay que contarlos a mano ni actualizarlo si cambia el texto.


// --- La sección de código --------------------------------------------------
.section .text
.global _start
// `_start` es donde el sistema operativo empieza a ejecutar. Ojo: aquí NO
// usamos `main`, porque este programa no se enlaza con la biblioteca de C
// (no hay printf). Sin libc no hay nadie que prepare las cosas y después
// llame a `main`: entramos directo.

_start:
    // ---------------------------------------------------------------
    // write(1, mensaje, longitud)
    //
    // Una syscall es una petición al kernel. Se piden poniendo los
    // argumentos en registros y ejecutando `svc`. En AArch64/Linux:
    //
    //     x0..x5  ->  los argumentos
    //     x8      ->  QUÉ syscall se pide (64 = write, 93 = exit)
    //     svc #0  ->  ejecutarla
    // ---------------------------------------------------------------
    mov x0, #1                  // x0 = 1  -> stdout (la pantalla)

    adrp x1, mensaje            // x1 = dirección de la PÁGINA de `mensaje`
    add  x1, x1, :lo12:mensaje  // x1 += los 12 bits bajos -> dirección exacta
    // ¿Por qué dos instrucciones para una dirección? Porque en ARM64 toda
    // instrucción mide exactamente 4 bytes, y una dirección de 64 bits no
    // cabe adentro de ninguna. Así que se arma en dos pasos: `adrp` trae
    // la página (múltiplo de 4 KB) y `add :lo12:` le suma el
    // desplazamiento dentro de esa página.
    //
    // Este par adrp/add les va a aparecer en TODA dirección que carguen.
    // Aparece también en el código que genera MiniPascal, para llegar a
    // la cadena de formato de printf. Vale la pena reconocerlo.

    mov x2, #longitud           // x2 = cuántos bytes escribir
    mov x8, #64                 // x8 = 64 -> la syscall `write`
    svc #0                      // pedírselo al kernel

    // ---------------------------------------------------------------
    // exit(0)
    //
    // Obligatorio. Sin esto el procesador sigue ejecutando lo que haya
    // en la memoria de después, que no es código, y el programa muere
    // con "Illegal instruction". Pruébenlo: comenten las dos líneas.
    // ---------------------------------------------------------------
    mov x0, #0                  // código de salida 0 = todo bien
    mov x8, #93                 // x8 = 93 -> la syscall `exit`
    svc #0
