    .global main
    .extern printf

.section .data
a: .skip 8           // variable a, 8 bytes
b: .skip 8           // variable b, 8 bytes
c: .skip 8           // variable c, 8 bytes
e: .skip 8           // variable e, 8 bytes
f: .skip 8           // variable f, 8 bytes
j: .skip 8           // variable j, 8 bytes
n: .skip 8           // variable n, 8 bytes
numero: .skip 8           // variable numero, 8 bytes
x: .skip 8           // variable x, 8 bytes
z: .skip 8           // variable z, 8 bytes
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

    // ===== let a = ... =====
    mov x13, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, =a // ADDR: &a para guardar a
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    str x9, [x15] // LET a = x9 (int)

    // ===== if cond {...} =====
    ldr x10, =a // ADDR: &a para leer a
    ldr x11, [x10] // VAR a (int) -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    cbz x12, L_if_fin_0 // salta si falso (0)

    // ===== println!(...) =====
    ldr x13, =a // ADDR: &a para leer a
    ldr x15, [x13] // VAR a (int) -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w9 // PRINT: w1 = valor int
    bl printf // PRINT int (w1)
L_if_fin_0: // etiqueta L_if_fin_0

    // ===== let z = ... =====
    mov x10, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, =z // ADDR: &z para guardar z
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    str x12, [x11] // LET z = x12 (int)

    // ===== if cond {...} =====
    ldr x13, =z // ADDR: &z para leer z
    ldr x15, [x13] // VAR z (int) -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    cbz x9, L_if_fin_1 // salta si falso (0)

    // ===== println!(...) =====
    ldr x10, =z // ADDR: &z para leer z
    ldr x11, [x10] // VAR z (int) -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w12 // PRINT: w1 = valor int
    bl printf // PRINT int (w1)
L_if_fin_1: // etiqueta L_if_fin_1

    // ===== let j = ... =====
    mov x13, #23 // VALOR int 23 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, =j // ADDR: &j para guardar j
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    str x9, [x15] // LET j = x9 (int)

    // ===== while cond {...} =====
L_while_2: // etiqueta L_while_2
    ldr x10, =j // ADDR: &j para leer j
    ldr x11, [x10] // VAR j (int) -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    cbz x12, L_while_fin_3 // salta si falso (0)

    // ===== println!(...) =====
    ldr x13, =j // ADDR: &j para leer j
    ldr x15, [x13] // VAR j (int) -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w9 // PRINT: w1 = valor int
    bl printf // PRINT int (w1)

    // ===== let j = ... =====

    // ===== OP - =====
    ldr x10, =j // ADDR: &j para leer j
    ldr x11, [x10] // VAR j (int) -> pila
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
    ldr x10, =j // ADDR: &j para guardar j
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    str x11, [x10] // LET j = x11 (int)
    b L_while_2 // WHILE: repetir
L_while_fin_3: // etiqueta L_while_fin_3

    // ===== let b = ... =====
    mov x12, #17 // VALOR int 17 -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, =b // ADDR: &b para guardar b
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    str x15, [x13] // LET b = x15 (int)

    // ===== while cond {...} =====
L_while_4: // etiqueta L_while_4
    ldr x9, =b // ADDR: &b para leer b
    ldr x10, [x9] // VAR b (int) -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    cbz x11, L_while_fin_5 // salta si falso (0)

    // ===== println!(...) =====
    ldr x12, =b // ADDR: &b para leer b
    ldr x13, [x12] // VAR b (int) -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w15 // PRINT: w1 = valor int
    bl printf // PRINT int (w1)
    b L_while_fin_5 // BREAK -> fin del while
    b L_while_4 // WHILE: repetir
L_while_fin_5: // etiqueta L_while_fin_5

    // ===== let c = ... =====
    mov x9, #16 // VALOR int 16 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, =c // ADDR: &c para guardar c
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    str x11, [x10] // LET c = x11 (int)

    // ===== while cond {...} =====
L_while_6: // etiqueta L_while_6
    ldr x12, =c // ADDR: &c para leer c
    ldr x13, [x12] // VAR c (int) -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    cbz x15, L_while_fin_7 // salta si falso (0)

    // ===== let c = ... =====

    // ===== OP - =====
    ldr x9, =c // ADDR: &c para leer c
    ldr x10, [x9] // VAR c (int) -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    mov x11, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    sub x15, x13, x12 // OP - (int) -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, =c // ADDR: &c para guardar c
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    str x10, [x9] // LET c = x10 (int)

    // ===== if cond {...} =====
    ldr x11, =c // ADDR: &c para leer c
    ldr x12, [x11] // VAR c (int) -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    cbz x13, L_if_fin_8 // salta si falso (0)
    b L_while_6 // CONTINUE -> re-evaluar while
L_if_fin_8: // etiqueta L_if_fin_8

    // ===== println!(...) =====
    ldr x15, =c // ADDR: &c para leer c
    ldr x9, [x15] // VAR c (int) -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w10 // PRINT: w1 = valor int
    bl printf // PRINT int (w1)
    b L_while_6 // WHILE: repetir
L_while_fin_7: // etiqueta L_while_fin_7

    // ===== let e = ... =====
    mov x11, #4 // VALOR int 4 -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x12, =e // ADDR: &e para guardar e
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    str x13, [x12] // LET e = x13 (int)

    // ===== if cond {...} =====

    // ===== OP == =====
    ldr x15, =e // ADDR: &e para leer e
    ldr x9, [x15] // VAR e (int) -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    mov x10, #4 // VALOR int 4 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    cmp x13, x12 // CMP == (int)
    cset w11, eq // w11 = (e1 == e2)
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    cbz x15, L_if_fin_9 // salta si falso (0)

    // ===== println!(...) =====
    ldr x9, =e // ADDR: &e para leer e
    ldr x10, [x9] // VAR e (int) -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w11 // PRINT: w1 = valor int
    bl printf // PRINT int (w1)
L_if_fin_9: // etiqueta L_if_fin_9

    // ===== let n = ... =====
    mov x12, #3 // VALOR int 3 -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, =n // ADDR: &n para guardar n
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    str x15, [x13] // LET n = x15 (int)

    // ===== while cond {...} =====
L_while_10: // etiqueta L_while_10

    // ===== OP != =====
    ldr x9, =n // ADDR: &n para leer n
    ldr x10, [x9] // VAR n (int) -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    mov x11, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    cmp x15, x13 // CMP != (int)
    cset w12, ne // w12 = (e1 != e2)
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    cbz x9, L_while_fin_11 // salta si falso (0)

    // ===== println!(...) =====
    ldr x10, =n // ADDR: &n para leer n
    ldr x11, [x10] // VAR n (int) -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: x0 = "%d\n"
    mov w1, w12 // PRINT: w1 = valor int
    bl printf // PRINT int (w1)

    // ===== let n = ... =====

    // ===== OP - =====
    ldr x13, =n // ADDR: &n para leer n
    ldr x15, [x13] // VAR n (int) -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    mov x9, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    sub x12, x11, x10 // OP - (int) -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, =n // ADDR: &n para guardar n
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    str x15, [x13] // LET n = x15 (int)
    b L_while_10 // WHILE: repetir
L_while_fin_11: // etiqueta L_while_fin_11
    mov w0, #0              // retorno 0 a libc
    ldp x29, x30, [sp], #16 // pop {fp, lr}
    ret                     // vuelta a libc
