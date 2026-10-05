// hello.asm - Equivalente a hello.ll en ARM64

.global _start

.section .text
_start:
    // Prologo: guardar FP y RA, establecer frame pointer
    stp x29, x30, [sp, #-16]!
    mov x29, sp

    // Reservar espacio para 7 bytes en el stack:
    // H e l l o \n \0
    sub sp, sp, #16          // Reservar 16 bytes (alineado)

    // -------------------------
    // str[0] = 'H'
    // ASCII: 72
    // -------------------------
    mov w0, #72
    strb w0, [sp, #0]

    // -------------------------
    // str[1] = 'e'
    // ASCII: 101
    // -------------------------
    mov w0, #101
    strb w0, [sp, #1]

    // -------------------------
    // str[2] = 'l'
    // ASCII: 108
    // -------------------------
    mov w0, #108
    strb w0, [sp, #2]

    // -------------------------
    // str[3] = 'l'
    // ASCII: 108
    // -------------------------
    mov w0, #108
    strb w0, [sp, #3]

    // -------------------------
    // str[4] = 'o'
    // ASCII: 111
    // -------------------------
    mov w0, #111
    strb w0, [sp, #4]

    // -------------------------
    // str[5] = '\n'
    // ASCII: 10
    // -------------------------
    mov w0, #10
    strb w0, [sp, #5]

    // -------------------------
    // str[6] = '\0'
    // Terminador de la string
    // -------------------------
    mov w0, #0
    strb w0, [sp, #6]

    // Pasar a write el puntero
    // al primer caracter.
    // write(stdout, str, 6)
    mov x0, #1               // fd = stdout
    mov x1, sp               // buffer = puntero al stack
    mov x2, #6               // longitud = 6 (sin el \0)
    mov x8, #64              // syscall write
    svc #0

    // Restaurar stack pointer
    add sp, sp, #16

    // Epilogo: restaurar FP y RA
    ldp x29, x30, [sp], #16

    // Exit syscall
    mov x0, #0               // exit code 0
    mov x8, #93              // syscall exit
    svc #0
