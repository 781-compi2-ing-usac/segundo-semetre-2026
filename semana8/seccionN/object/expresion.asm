    .global main
    .extern printf

.section .data
f: .skip 8           // variable f, 8 bytes
numero: .skip 8           // variable numero, 8 bytes
x: .skip 8           // variable x, 8 bytes
Fc_0: .double 2.5  // literal float
Fc_1: .double 3.1  // literal float
fmt: .asciz "%d\n"
fmtf: .asciz "%f\n"

.section .text
main:
    stp x29, x30, [sp, #-16]! // push {fp, lr}, sp alineado a 16
    mov x29, sp               // nuevo frame pointer

    // ===== let numero = ... =====

    // ===== OP + =====

    // ===== OP * =====
    mov x9, #4 // VALOR int 4 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    mov x10, #5 // VALOR int 5 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    mul x13, x12, x11 // OP * (int) -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    mov x15, #6 // VALOR int 6 -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    add x11, x10, x9 // OP + (int) -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x12, =numero // ADDR: &numero para guardar numero
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    str x13, [x12] // LET numero = x13 (int)

    // ===== println!(...) =====
    ldr x15, =numero // ADDR: &numero para leer numero
    ldr x9, [x15] // VAR numero (int) -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w10 // PRINT: w1 = valor int
    bl printf // PRINT int (w1)

    // ===== let x = ... =====

    // ===== OP - =====
    mov x11, #20 // VALOR int 20 -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    mov x12, #6 // VALOR int 6 -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    sub x9, x15, x13 // OP - (int) -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, =x // ADDR: &x para guardar x
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    str x11, [x10] // LET x = x11 (int)

    // ===== println!(...) =====
    ldr x12, =x // ADDR: &x para leer x
    ldr x13, [x12] // VAR x (int) -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w15 // PRINT: w1 = valor int
    bl printf // PRINT int (w1)

    // ===== let f = ... =====

    // ===== OP + =====
    ldr x9, =Fc_0 // ADDR: &Fc_0 para literal 2.5
    ldr d8, [x9] // VALOR float 2.5 -> pila
    sub sp, sp, #8 // PUSH d8
    str d8, [sp, #0] // tope = d8
    ldr x10, =Fc_1 // ADDR: &Fc_1 para literal 3.1
    ldr d9, [x10] // VALOR float 3.1 -> pila
    sub sp, sp, #8 // PUSH d9
    str d9, [sp, #0] // tope = d9
    ldr d10, [sp, #0] // POP a d10
    add sp, sp, #8 // libera 8 B
    ldr d11, [sp, #0] // POP a d11
    add sp, sp, #8 // libera 8 B
    fadd d12, d11, d10 // OP + (float) -> pila
    sub sp, sp, #8 // PUSH d12
    str d12, [sp, #0] // tope = d12
    ldr x11, =f // ADDR: &f para guardar f
    ldr d13, [sp, #0] // POP a d13
    add sp, sp, #8 // libera 8 B
    str d13, [x11] // LET f = d13 (double)

    // ===== println!(...) =====
    ldr x12, =f // ADDR: &f para leer f
    ldr d8, [x12] // VAR f (double) -> pila
    sub sp, sp, #8 // PUSH d8
    str d8, [sp, #0] // tope = d8
    ldr d0, [sp, #0] // POP a d0
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmtf // PRINT: x0 = "%f\n"
    bl printf // PRINT float (d0)
    mov w0, #0              // retorno 0 a libc
    ldp x29, x30, [sp], #16 // pop {fp, lr}
    ret                     // vuelta a libc
