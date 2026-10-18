    .global main
    .extern printf

.section .data
i: .skip 8           // variable i, 8 bytes
j: .skip 8           // variable j, 8 bytes
k: .skip 8           // variable k, 8 bytes
fmt: .asciz "%d\n"
fmtf: .asciz "%f\n"
fmtsp: .asciz "%d "
fmtfsp: .asciz "%f "
fmtnl: .asciz "\n"

.section .bss
__heap_base: .skip 65536  // heap bump, 65536 B
__heap_end:  // fin del heap (x21)
.section .text
main:
    stp x29, x30, [sp, #-16]! // push {fp, lr}, sp alineado a 16
    mov x29, sp               // nuevo frame pointer
    ldr x20, =__heap_base     // HEAP: bump ptr
    ldr x21, =__heap_end      // HEAP: fin del heap
    sub sp, sp, #48        // FRAME main: reserva 48 B
    str x20, [x29, #-8]       // FRAME: guarda mark (off 8)
    str xzr, [x29, #-16] // AMBITO: slot a = 0
    str xzr, [x29, #-24] // AMBITO: slot b = 0
    str xzr, [x29, #-32] // AMBITO: slot m = 0

    // ===== call saluda() =====
    bl _fn_saluda // CALL _fn_saluda
    mov x9, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B

    // ===== array a[3] = ... =====
    ldr x11, [x29, #-16] // HEAP: ptr = slot
    cbnz x11, L_heap_done_0 // HEAP: guard, ya asignado
    mov x12, #3 // HEAP: N elementos
    lsl x12, x12, #3 // HEAP: * 8
    add x12, x20, x12 // HEAP: nuevo tope
    cmp x12, x21 // HEAP: contra fin
    b.hi L_heap_oom // HEAP: sin memoria -> exit(1)
    mov x11, x20 // HEAP: base del bloque
    mov x20, x12 // HEAP: avanza bump
    str x11, [x29, #-16] // HEAP: publica puntero
L_heap_done_0: // etiqueta L_heap_done_0
    mov x13, #7 // VALOR int 7 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [x29, #-16] // ARRAY: base heap
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    str x9, [x15, #0] // ARRAY [0] (int)
    mov x10, #7 // VALOR int 7 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [x29, #-16] // ARRAY: base heap
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    str x12, [x11, #8] // ARRAY [1] (int)
    mov x13, #7 // VALOR int 7 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [x29, #-16] // ARRAY: base heap
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    str x9, [x15, #16] // ARRAY [2] (int)

    // ===== println!(...) =====

    // ===== idx a[...] =====
    mov x10, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    lsl x11, x11, #3 // IDX: lineal * 8
    ldr x12, [x29, #-16] // IDX: base heap (a)
    add x12, x12, x11 // IDX: &a[...]
    ldr x13, [x12] // IDX a[...] (int) -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: formato
    mov w1, w15 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== println!(...) =====

    // ===== idx a[...] =====
    mov x9, #2 // VALOR int 2 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    lsl x10, x10, #3 // IDX: lineal * 8
    ldr x11, [x29, #-16] // IDX: base heap (a)
    add x11, x11, x10 // IDX: &a[...]
    ldr x12, [x11] // IDX a[...] (int) -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: formato
    mov w1, w13 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== array b[3] = ... =====
    ldr x15, [x29, #-24] // HEAP: ptr = slot
    cbnz x15, L_heap_done_1 // HEAP: guard, ya asignado
    mov x9, #3 // HEAP: N elementos
    lsl x9, x9, #3 // HEAP: * 8
    add x9, x20, x9 // HEAP: nuevo tope
    cmp x9, x21 // HEAP: contra fin
    b.hi L_heap_oom // HEAP: sin memoria -> exit(1)
    mov x15, x20 // HEAP: base del bloque
    mov x20, x9 // HEAP: avanza bump
    str x15, [x29, #-24] // HEAP: publica puntero
L_heap_done_1: // etiqueta L_heap_done_1
    mov x10, #4 // VALOR int 4 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [x29, #-24] // ARRAY: base heap
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    str x12, [x11, #0] // ARRAY [0] (int)
    mov x13, #5 // VALOR int 5 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [x29, #-24] // ARRAY: base heap
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    str x9, [x15, #8] // ARRAY [1] (int)
    mov x10, #6 // VALOR int 6 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [x29, #-24] // ARRAY: base heap
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    str x12, [x11, #16] // ARRAY [2] (int)

    // ===== idx b[...] = ... =====
    mov x13, #9 // VALOR int 9 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    mov x15, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    lsl x9, x9, #3 // IDX: lineal * 8
    ldr x10, [x29, #-24] // IDX: base heap (b)
    add x10, x10, x9 // IDX: &b[...]
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    str x11, [x10] // IDX b[...] = x11 (int)

    // ===== println!(...) =====

    // ===== idx b[...] =====
    mov x12, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    lsl x13, x13, #3 // IDX: lineal * 8
    ldr x15, [x29, #-24] // IDX: base heap (b)
    add x15, x15, x13 // IDX: &b[...]
    ldr x9, [x15] // IDX b[...] (int) -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: formato
    mov w1, w10 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== array m[2, 3] = ... =====
    ldr x11, [x29, #-32] // HEAP: ptr = slot
    cbnz x11, L_heap_done_2 // HEAP: guard, ya asignado
    mov x12, #6 // HEAP: N elementos
    lsl x12, x12, #3 // HEAP: * 8
    add x12, x20, x12 // HEAP: nuevo tope
    cmp x12, x21 // HEAP: contra fin
    b.hi L_heap_oom // HEAP: sin memoria -> exit(1)
    mov x11, x20 // HEAP: base del bloque
    mov x20, x12 // HEAP: avanza bump
    str x11, [x29, #-32] // HEAP: publica puntero
L_heap_done_2: // etiqueta L_heap_done_2
    mov x13, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [x29, #-32] // ARRAY: base heap
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    str x9, [x15, #0] // ARRAY [0] (int)
    mov x10, #2 // VALOR int 2 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [x29, #-32] // ARRAY: base heap
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    str x12, [x11, #8] // ARRAY [1] (int)
    mov x13, #3 // VALOR int 3 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [x29, #-32] // ARRAY: base heap
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    str x9, [x15, #16] // ARRAY [2] (int)
    mov x10, #4 // VALOR int 4 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [x29, #-32] // ARRAY: base heap
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    str x12, [x11, #24] // ARRAY [3] (int)
    mov x13, #5 // VALOR int 5 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [x29, #-32] // ARRAY: base heap
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    str x9, [x15, #32] // ARRAY [4] (int)
    mov x10, #6 // VALOR int 6 -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [x29, #-32] // ARRAY: base heap
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    str x12, [x11, #40] // ARRAY [5] (int)

    // ===== println!(...) =====

    // ===== idx m[...] =====
    mov x13, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    mov x15, #2 // VALOR int 2 -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    mov x11, #3 // IDX: stride[0]=3
    mul x12, x10, x11 // IDX: i0*stride
    add x13, x9, x12 // IDX: acum + i0*s
    lsl x13, x13, #3 // IDX: lineal * 8
    ldr x15, [x29, #-32] // IDX: base heap (m)
    add x15, x15, x13 // IDX: &m[...]
    ldr x9, [x15] // IDX m[...] (int) -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: formato
    mov w1, w10 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== println!(...) =====

    // ===== idx m[...] =====
    mov x11, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    mov x12, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    mov x9, #3 // IDX: stride[0]=3
    mul x10, x15, x9 // IDX: i0*stride
    add x11, x13, x10 // IDX: acum + i0*s
    lsl x11, x11, #3 // IDX: lineal * 8
    ldr x12, [x29, #-32] // IDX: base heap (m)
    add x12, x12, x11 // IDX: &m[...]
    ldr x13, [x12] // IDX m[...] (int) -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: formato
    mov w1, w15 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== println!(...) =====
    ldr x9, [x29, #-32] // PRINT-ARR: base heap (m)
    ldr x10, [x9, #0] // PRINT-ARR [0] (int)
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmtsp // PRINT: formato
    mov w1, w11 // PRINT: w1 = valor int
    bl printf // CALL printf
    ldr x12, [x29, #-32] // PRINT-ARR: base heap (m)
    ldr x13, [x12, #8] // PRINT-ARR [1] (int)
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmtsp // PRINT: formato
    mov w1, w15 // PRINT: w1 = valor int
    bl printf // CALL printf
    ldr x9, [x29, #-32] // PRINT-ARR: base heap (m)
    ldr x10, [x9, #16] // PRINT-ARR [2] (int)
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmtsp // PRINT: formato
    mov w1, w11 // PRINT: w1 = valor int
    bl printf // CALL printf
    ldr x0, =fmtnl // PRINT-ARR: fin de fila
    bl printf // CALL printf
    ldr x12, [x29, #-32] // PRINT-ARR: base heap (m)
    ldr x13, [x12, #24] // PRINT-ARR [3] (int)
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmtsp // PRINT: formato
    mov w1, w15 // PRINT: w1 = valor int
    bl printf // CALL printf
    ldr x9, [x29, #-32] // PRINT-ARR: base heap (m)
    ldr x10, [x9, #32] // PRINT-ARR [4] (int)
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmtsp // PRINT: formato
    mov w1, w11 // PRINT: w1 = valor int
    bl printf // CALL printf
    ldr x12, [x29, #-32] // PRINT-ARR: base heap (m)
    ldr x13, [x12, #40] // PRINT-ARR [5] (int)
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmtsp // PRINT: formato
    mov w1, w15 // PRINT: w1 = valor int
    bl printf // CALL printf
    ldr x0, =fmtnl // PRINT-ARR: fin de fila
    bl printf // CALL printf

    // ===== let i = ... =====
    mov x9, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, =i // ADDR: &i para guardar i
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    str x11, [x10] // LET i = x11 (int)

    // ===== while cond {...} =====
L_while_3: // etiqueta L_while_3

    // ===== OP != =====
    ldr x12, =i // ADDR: &i para leer i
    ldr x13, [x12] // VAR i (int) -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    mov x15, #2 // VALOR int 2 -> pila
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
    cbz x12, L_while_fin_4 // salta si falso (0)
    str x20, [x29, #-40] // AMBITO: guarda mark

    // ===== let j = ... =====
    mov x13, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, =j // ADDR: &j para guardar j
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    str x9, [x15] // LET j = x9 (int)

    // ===== while cond {...} =====
L_while_5: // etiqueta L_while_5

    // ===== OP != =====
    ldr x10, =j // ADDR: &j para leer j
    ldr x11, [x10] // VAR j (int) -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    mov x12, #3 // VALOR int 3 -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    cmp x9, x15 // CMP != (int)
    cset w13, ne // w13 = (e1 != e2)
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    cbz x10, L_while_fin_6 // salta si falso (0)
    str x20, [x29, #-48] // AMBITO: guarda mark

    // ===== println!(...) =====

    // ===== idx m[...] =====
    ldr x11, =i // ADDR: &i para leer i
    ldr x12, [x11] // VAR i (int) -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, =j // ADDR: &j para leer j
    ldr x15, [x13] // VAR j (int) -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    mov x11, #3 // IDX: stride[0]=3
    mul x12, x10, x11 // IDX: i0*stride
    add x13, x9, x12 // IDX: acum + i0*s
    lsl x13, x13, #3 // IDX: lineal * 8
    ldr x15, [x29, #-32] // IDX: base heap (m)
    add x15, x15, x13 // IDX: &m[...]
    ldr x9, [x15] // IDX m[...] (int) -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: formato
    mov w1, w10 // PRINT: w1 = valor int
    bl printf // CALL printf

    // ===== let j = ... =====

    // ===== OP + =====
    ldr x11, =j // ADDR: &j para leer j
    ldr x12, [x11] // VAR j (int) -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    mov x13, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    add x10, x9, x15 // OP + (int) -> pila
    sub sp, sp, #8 // PUSH x10
    str x10, [sp, #0] // tope = x10
    ldr x11, =j // ADDR: &j para guardar j
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    str x12, [x11] // LET j = x12 (int)
    ldr x20, [x29, #-48] // AMBITO: restaura mark
    b L_while_5 // WHILE: repetir
L_while_fin_6: // etiqueta L_while_fin_6

    // ===== let i = ... =====

    // ===== OP + =====
    ldr x13, =i // ADDR: &i para leer i
    ldr x15, [x13] // VAR i (int) -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    mov x9, #1 // VALOR int 1 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    add x12, x11, x10 // OP + (int) -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, =i // ADDR: &i para guardar i
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    str x15, [x13] // LET i = x15 (int)
    ldr x20, [x29, #-40] // AMBITO: restaura mark
    b L_while_3 // WHILE: repetir
L_while_fin_4: // etiqueta L_while_fin_4

    // ===== call cuenta() =====
    bl _fn_cuenta // CALL _fn_cuenta
    mov x9, #0 // VALOR int 0 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, [sp, #0] // POP a x10
    add sp, sp, #8 // libera 8 B

    // ===== println!(...) =====

    // ===== call dame() =====
    bl _fn_dame // CALL _fn_dame
    mov x11, x0 // CALL: retorno int (x0) -> pila
    sub sp, sp, #8 // PUSH x11
    str x11, [sp, #0] // tope = x11
    ldr x12, [sp, #0] // POP a x12
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: formato
    mov w1, w12 // PRINT: w1 = valor int
    bl printf // CALL printf
    add sp, sp, #48        // FRAME: libera 48 B
    mov w0, #0              // retorno 0 a libc
    ldp x29, x30, [sp], #16 // pop {fp, lr}
    ret                     // vuelta a libc
L_heap_oom: // etiqueta L_heap_oom
    mov x8, #93 // HEAP OOM: exit
    mov x0, #1 // HEAP OOM: codigo 1
    svc #0 // HEAP OOM: termina

    // ===== def saluda() =====
_fn_saluda: // etiqueta _fn_saluda
    stp x29, x30, [sp, #-16]! // FN: push {fp, lr}
    mov x29, sp // FN: nuevo frame pointer
    sub sp, sp, #16 // FN: frame 16 B
    str x20, [x29, #-8] // FN: guarda mark (off 8)

    // ===== println!(...) =====
    mov x13, #99 // VALOR int 99 -> pila
    sub sp, sp, #8 // PUSH x13
    str x13, [sp, #0] // tope = x13
    ldr x15, [sp, #0] // POP a x15
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: formato
    mov w1, w15 // PRINT: w1 = valor int
    bl printf // CALL printf
L_fn_fin_7: // etiqueta L_fn_fin_7
    ldr x20, [x29, #-8] // FN: restaura mark
    add sp, sp, #16 // FN: libera frame
    ldp x29, x30, [sp], #16 // FN: pop {fp, lr}
    ret // FN: vuelta al bl

    // ===== def cuenta() =====
_fn_cuenta: // etiqueta _fn_cuenta
    stp x29, x30, [sp, #-16]! // FN: push {fp, lr}
    mov x29, sp // FN: nuevo frame pointer
    sub sp, sp, #16 // FN: frame 16 B
    str x20, [x29, #-8] // FN: guarda mark (off 8)

    // ===== let k = ... =====
    mov x9, #2 // VALOR int 2 -> pila
    sub sp, sp, #8 // PUSH x9
    str x9, [sp, #0] // tope = x9
    ldr x10, =k // ADDR: &k para guardar k
    ldr x11, [sp, #0] // POP a x11
    add sp, sp, #8 // libera 8 B
    str x11, [x10] // LET k = x11 (int)

    // ===== while cond {...} =====
L_while_9: // etiqueta L_while_9

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
    cbz x12, L_while_fin_10 // salta si falso (0)
    str x20, [x29, #-16] // AMBITO: guarda mark

    // ===== println!(...) =====
    ldr x13, =k // ADDR: &k para leer k
    ldr x15, [x13] // VAR k (int) -> pila
    sub sp, sp, #8 // PUSH x15
    str x15, [sp, #0] // tope = x15
    ldr x9, [sp, #0] // POP a x9
    add sp, sp, #8 // libera 8 B
    ldr x0, =fmt // PRINT: formato
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
    ldr x20, [x29, #-16] // AMBITO: restaura mark
    b L_while_9 // WHILE: repetir
L_while_fin_10: // etiqueta L_while_fin_10
L_fn_fin_8: // etiqueta L_fn_fin_8
    ldr x20, [x29, #-8] // FN: restaura mark
    add sp, sp, #16 // FN: libera frame
    ldp x29, x30, [sp], #16 // FN: pop {fp, lr}
    ret // FN: vuelta al bl

    // ===== def dame() =====
_fn_dame: // etiqueta _fn_dame
    stp x29, x30, [sp, #-16]! // FN: push {fp, lr}
    mov x29, sp // FN: nuevo frame pointer
    sub sp, sp, #16 // FN: frame 16 B
    str x20, [x29, #-8] // FN: guarda mark (off 8)

    // ===== return ... =====
    mov x12, #6 // VALOR int 6 -> pila
    sub sp, sp, #8 // PUSH x12
    str x12, [sp, #0] // tope = x12
    ldr x13, [sp, #0] // POP a x13
    add sp, sp, #8 // libera 8 B
    mov x0, x13 // RETURN: x0 = valor int
    b L_fn_fin_11 // RETURN -> fin
L_fn_fin_11: // etiqueta L_fn_fin_11
    ldr x20, [x29, #-8] // FN: restaura mark
    add sp, sp, #16 // FN: libera frame
    ldp x29, x30, [sp], #16 // FN: pop {fp, lr}
    ret // FN: vuelta al bl
