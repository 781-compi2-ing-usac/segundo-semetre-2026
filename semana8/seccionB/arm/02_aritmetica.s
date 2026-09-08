// ===========================================================================
// 02_aritmetica.s — calcular 2 + 3 * 4 e imprimirlo, a mano.
//
// Este archivo es el DESTINO. Es, casi línea por línea, lo que
// minipascal/generador_arm.py produce hoy. Léanlo antes de leer el
// generador: es mucho más fácil entender un traductor cuando uno ya vio a
// dónde traduce.
//
//     ./build.sh 02_aritmetica.s
//
// Diferencia con 01_hola.s: aquí SÍ nos enlazamos con la biblioteca de C,
// para usar printf. Por eso el punto de entrada es `main` y no `_start`.
//
// ¿Por qué printf y no la syscall `write` de 01_hola.s? Porque `write`
// escribe BYTES. Para imprimir el número 14 con `write` habría que
// fabricar antes los caracteres '1' y '4': dividir entre 10 en un bucle,
// sumarle 48 a cada resto, guardarlos al revés en un buffer. Son unas 20
// líneas. printf ya trae eso hecho — y para `real` (los f64 del enunciado)
// la diferencia deja de ser comodidad y pasa a ser un muro.
// ===========================================================================

.section .data

fmt_entero:
    .asciz "%ld\n"
// `.asciz` = `.ascii` + un byte cero al final. printf lo necesita: así
// sabe dónde termina la cadena de formato.
// `%ld` imprime un entero de 64 bits con signo, que es el tamaño de los
// registros xN. Si usaran `%d` (32 bits) sobre un valor de 64, los
// números grandes saldrían mal.


.section .text
.global main

main:
    // --- Prólogo ---------------------------------------------------------
    stp x29, x30, [sp, #-16]!   // guardar frame pointer y dirección de retorno
    mov x29, sp
    // `stp` = STore Pair: guarda DOS registros de una vez. El `!` del
    // final significa "y además actualizá sp" (pre-index).
    //
    // Guardar x30 es obligatorio: `bl printf` va a pisar x30 con SU
    // dirección de retorno. Si no lo hubiéramos guardado, cuando main
    // haga `ret` volvería a un lugar equivocado. Este es EL error clásico
    // al generar funciones, y se manifiesta como un crash sin sentido.


    // --- Calcular 2 + 3 * 4 ----------------------------------------------
    // La regla del modelo: toda expresión deja su resultado en x0.
    //
    // El árbol es      Suma( 2 , Mult( 3 , 4 ) )
    // y se recorre en postorden: primero los hijos, después el padre.

    mov x0, #2                  // x0 = 2               (izquierdo de la suma)
    str x0, [sp, #-16]!         // pila: [2]            guardarlo, x0 se va a pisar

    mov x0, #3                  // x0 = 3               (izquierdo de la mult.)
    str x0, [sp, #-16]!         // pila: [2, 3]

    mov x0, #4                  // x0 = 4               (derecho de la mult.)
    mov x1, x0                  // x1 = 4
    ldr x0, [sp], #16           // x0 = 3   pila: [2]   recuperar el izquierdo
    mul x0, x0, x1              // x0 = 3 * 4 = 12

    mov x1, x0                  // x1 = 12              (derecho de la suma)
    ldr x0, [sp], #16           // x0 = 2   pila: []
    add x0, x0, x1              // x0 = 2 + 12 = 14

    // Empujar de 16 en 16 (y no de 8, que es lo que ocupa un entero) no es
    // desperdicio por descuido: AArch64 exige que sp esté alineado a 16
    // bytes siempre. Con sp desalineado, printf revienta.


    // --- Imprimir --------------------------------------------------------
    // printf(formato, valor): el formato va en x0, el primer valor en x1.
    mov x1, x0                  // x1 = 14   <- PRIMERO mover el valor...
    adrp x0, fmt_entero         // ...y DESPUÉS pisar x0 con el formato
    add  x0, x0, :lo12:fmt_entero
    bl printf
    // Invertir esas dos líneas es un error clásico y silencioso: no falla,
    // imprime basura. Si su compilador imprime números que no tienen
    // sentido, revisen este orden antes que nada.


    // --- Epílogo ---------------------------------------------------------
    mov w0, #0                  // valor de retorno de main = 0
    ldp x29, x30, [sp], #16     // restaurar lo del prólogo (LoaD Pair)
    ret                         // volver usando x30
