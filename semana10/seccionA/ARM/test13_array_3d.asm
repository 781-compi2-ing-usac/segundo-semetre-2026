.global _start
.section .bss
buffer: .skip 32
.section .text
_start:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    mov x9, #1
    str x9, [x29, #-8]
    mov x10, #2
    str x10, [x29, #-16]
    mov x11, #3
    str x11, [x29, #-24]
    mov x12, #4
    str x12, [x29, #-32]
    mov x13, #5
    str x13, [x29, #-40]
    mov x14, #6
    str x14, [x29, #-48]
    mov x15, #7
    str x15, [x29, #-56]
    mov x16, #8
    str x16, [x29, #-64]
    mov x17, #0
    mov x9, #0
    mov x10, #2
    mul x11, x17, x10
    add x12, x11, x9
    mov x13, #0
    mov x14, #2
    mul x15, x12, x14
    add x16, x15, x13
    mov x9, #-8
    lsl x10, x16, #3
    sub x9, x9, x10
    ldr x17, [x29, x9]
    // Print int
    mov x0, x17
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
    mov x11, #0
    mov x12, #1
    mov x13, #2
    mul x14, x11, x13
    add x15, x14, x12
    mov x16, #1
    mov x17, #2
    mul x9, x15, x17
    add x10, x9, x16
    mov x12, #-8
    lsl x13, x10, #3
    sub x12, x12, x13
    ldr x11, [x29, x12]
    // Print int
    mov x0, x11
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
    mov x14, #1
    mov x15, #0
    mov x16, #2
    mul x17, x14, x16
    add x9, x17, x15
    mov x10, #0
    mov x11, #2
    mul x12, x9, x11
    add x13, x12, x10
    mov x15, #-8
    lsl x16, x13, #3
    sub x15, x15, x16
    ldr x14, [x29, x15]
    // Print int
    mov x0, x14
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
    mov x17, #1
    mov x9, #1
    mov x10, #2
    mul x11, x17, x10
    add x12, x11, x9
    mov x13, #1
    mov x14, #2
    mul x15, x12, x14
    add x16, x15, x13
    mov x9, #-8
    lsl x10, x16, #3
    sub x9, x9, x10
    ldr x17, [x29, x9]
    // Print int
    mov x0, x17
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