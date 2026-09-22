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
    mov x14, #0
    mov x15, #-8
    lsl x16, x14, #3
    sub x15, x15, x16
    mov x17, #10
    str x17, [x29, x15]
    mov x9, #2
    mov x10, #-8
    lsl x11, x9, #3
    sub x10, x10, x11
    mov x12, #30
    str x12, [x29, x10]
    mov x13, #4
    mov x14, #-8
    lsl x15, x13, #3
    sub x14, x14, x15
    mov x16, #50
    str x16, [x29, x14]
    mov x17, #0
    mov x10, #-8
    lsl x11, x17, #3
    sub x10, x10, x11
    ldr x9, [x29, x10]
    // Print int
    mov x0, x9
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
    mov x12, #2
    mov x14, #-8
    lsl x15, x12, #3
    sub x14, x14, x15
    ldr x13, [x29, x14]
    // Print int
    mov x0, x13
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
    mov x16, #4
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