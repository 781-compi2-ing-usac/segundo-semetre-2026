    .global main
    .extern printf

.section .data
k: .skip 8           // variable k, 8 bytes
v: .skip 8           // variable v, 8 bytes
Fc_0: .double 2.5  // literal float
fmt: .asciz "%d\n"
fmtf: .asciz "%f\n"

.section .text
main:
    stp x29, x30, [sp, #-16]! // push {fp, lr}, sp alineado a 16
    mov x29, sp               // nuevo frame pointer

    // ===== call saluda() =====
    bl _fn_saluda // CALL _fn_saluda
    mov x9, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B

    // ===== call cuenta() =====
    bl _fn_cuenta // CALL _fn_cuenta
    mov x11, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B

    // ===== call cuenta() =====
    bl _fn_cuenta // CALL _fn_cuenta
    mov x13, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B

    // ===== let v = ... =====

    // ===== call saluda() =====
    bl _fn_saluda // CALL _fn_saluda
    mov x9, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, =v // ADDR: &v para guardar v
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    str x11, [x10] // LET v = x11 (int)

    // ===== println!(...) =====
    ldr x12, =v // ADDR: &v para leer v
    ldr x13, [x12] // VAR v (int) -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w15 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== println!(...) =====

    // ===== call dame() =====
    bl _fn_dame // CALL _fn_dame
    mov x9, x0 // CALL: retorno int (x0) -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w10 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== println!(...) =====

    // ===== call temprano() =====
    bl _fn_temprano // CALL _fn_temprano
    mov x11, x0 // CALL: retorno int (x0) -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w12 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== println!(...) =====

    // ===== call mitad() =====
    bl _fn_mitad // CALL _fn_mitad
    sub sp, sp, #8 // PUSH d0
    str d0, [sp, #0] // tope = d0
    ldr d0, [sp, #0] // POP a d0
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmtf // PRINT: x0 = "%f\n"
    bl printf // CALL printf
    mov w0, #0              // retorno 0 a libc
    ldp x29, x30, [sp], #16 // pop {fp, lr}
    ret                     // vuelta a libc

    // ===== def saluda() =====
_fn_saluda: // etiqueta _fn_saluda
    stp x29, x30, [sp, #-16]! // FN: push {fp, lr}
    mov x29, sp // FN: nuevo frame pointer

    // ===== println!(...) =====
    mov x13, #99 // VALOR int 99 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w15 // PRINT: w1 = valor int
    bl printf // CALL printf
L_fn_fin_0: // etiqueta L_fn_fin_0
    ldp x29, x30, [sp], #16 // FN: pop {fp, lr}
    ret // FN: vuelta al bl

    // ===== def cuenta() =====
_fn_cuenta: // etiqueta _fn_cuenta
    stp x29, x30, [sp, #-16]! // FN: push {fp, lr}
    mov x29, sp // FN: nuevo frame pointer

    // ===== let k = ... =====
    mov x9, #2 // VALOR int 2 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, =k // ADDR: &k para guardar k
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    str x11, [x10] // LET k = x11 (int)

    // ===== while cond {...} =====
L_while_2: // etiqueta L_while_2

    // ===== OP != =====
    ldr x12, =k // ADDR: &k para leer k
    ldr x13, [x12] // VAR k (int) -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    mov x15, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    cmp x11, x10 // CMP != (int)
    cset w9, ne // w9 = (e1 != e2)
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    cbz x12, L_while_fin_3 // salta si falso (0)

    // ===== println!(...) =====
    ldr x13, =k // ADDR: &k para leer k
    ldr x15, [x13] // VAR k (int) -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w9 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== let k = ... =====

    // ===== OP - =====
    ldr x10, =k // ADDR: &k para leer k
    ldr x11, [x10] // VAR k (int) -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    mov x12, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    sub x9, x15, x13 // OP - (int) -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, =k // ADDR: &k para guardar k
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    str x11, [x10] // LET k = x11 (int)
    b L_while_2 // WHILE: repetir
L_while_fin_3: // etiqueta L_while_fin_3
L_fn_fin_1: // etiqueta L_fn_fin_1
    ldp x29, x30, [sp], #16 // FN: pop {fp, lr}
    ret // FN: vuelta al bl

    // ===== def dame() =====
_fn_dame: // etiqueta _fn_dame
    stp x29, x30, [sp, #-16]! // FN: push {fp, lr}
    mov x29, sp // FN: nuevo frame pointer

    // ===== return ... =====
    mov x12, #6 // VALOR int 6 -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    mov x0, x13 // RETURN: x0 = valor int
    b L_fn_fin_4 // RETURN -> fin
L_fn_fin_4: // etiqueta L_fn_fin_4
    ldp x29, x30, [sp], #16 // FN: pop {fp, lr}
    ret // FN: vuelta al bl

    // ===== def temprano() =====
_fn_temprano: // etiqueta _fn_temprano
    stp x29, x30, [sp, #-16]! // FN: push {fp, lr}
    mov x29, sp // FN: nuevo frame pointer

    // ===== println!(...) =====
    mov x15, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w9 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== return ... =====
    mov x10, #2 // VALOR int 2 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    mov x0, x11 // RETURN: x0 = valor int
    b L_fn_fin_5 // RETURN -> fin

    // ===== println!(...) =====
    mov x12, #3 // VALOR int 3 -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w13 // PRINT: w1 = valor int
    bl printf // CALL printf
L_fn_fin_5: // etiqueta L_fn_fin_5
    ldp x29, x30, [sp], #16 // FN: pop {fp, lr}
    ret // FN: vuelta al bl

    // ===== def mitad() =====
_fn_mitad: // etiqueta _fn_mitad
    stp x29, x30, [sp, #-16]! // FN: push {fp, lr}
    mov x29, sp // FN: nuevo frame pointer

    // ===== return ... =====
    ldr x15, =Fc_0 // ADDR: &Fc_0 para literal 2.5
    ldr d8, [x15] // VALOR float 2.5 -> pila
    sub sp, sp, #8 // PUSH d8
    str d8, [sp, #0] // tope = d8
    ldr d9, [sp, #0] // POP a d9
    add sp, sp, #8 // libera 8 B
    fmov d0, d9 // RETURN: d0 = valor float
    b L_fn_fin_6 // RETURN -> fin
L_fn_fin_6: // etiqueta L_fn_fin_6
    ldp x29, x30, [sp], #16 // FN: pop {fp, lr}
    ret // FN: vuelta al bl
