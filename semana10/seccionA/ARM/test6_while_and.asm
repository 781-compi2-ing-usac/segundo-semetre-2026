.global _start
.section .bss
buffer: .skip 32
.section .text
_start:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    mov x9, #10
    str x9, [x29, #-8]
    mov x10, #5
    str x10, [x29, #-16]
    b L1
L1:
    ldr x11, [x29, #-8]
    cmp x11, 0
    cset x12, gt
    cmp x12, #0
    b.ne L2
    b L3
L2:
    ldr x13, [x29, #-16]
    cmp x13, 0
    cset x14, gt
    cmp x14, #0
    b.ne L4
    b L5
L4:
    ldr x15, [x29, #-8]
    // Print int
    mov x0, x15
    bl itoa
    // write(stdout, buffer, len)
    mov x2, x1
    mov x1, x0
    mov x0, #1
    mov x8, #64
    svc #0
    // Print newline
    mov x0, #1
    ldr x1, =newline
    mov x2, #1
    mov x8, #64
    svc #0
    ldr x16, [x29, #-8]
    sub x17, x16, 1
    str x17, [x29, #-8]
    ldr x9, [x29, #-16]
    sub x10, x9, 1
    str x10, [x29, #-16]
    b L1
L3:
L5:
    // Exit syscall
    mov x0, #0
    mov x8, #93
    svc #0

itoa:
    // x0 = integer
    // returns: x0 = buffer ptr, x1 = length
    ldr x2, =buffer
    add x2, x2, #31
    mov w3, #0
    strb w3, [x2]
    mov x5, x0
    mov x4, #10
    mov x10, #0
    cmp x5, #0
    bge itoa_loop
    neg x5, x5
    mov x10, #1
itoa_loop:
    udiv x6, x5, x4
    msub x7, x6, x4, x5
    add x7, x7, #48
    sub x2, x2, #1
    strb w7, [x2]
    mov x5, x6
    cbnz x6, itoa_loop
    cmp x10, #0
    beq itoa_done
    sub x2, x2, #1
    mov w7, #45
    strb w7, [x2]
itoa_done:
    ldr x3, =buffer
    add x3, x3, #31
    sub x1, x3, x2
    mov x0, x2
    ret

.section .rodata
newline: .asciz "\n"