# 01 — Print y operaciones aritméticas → ARM64

> Alcance estricto: SOLO `println!(expr);` y `e1 + e2 | e1 - e2 | e1 * e2` con `ENTERO`.
> Nada de `let`, `if`, `def`, `struct` aquí (ver archivos 02-05).
> Target: `aarch64-linux-gnu-gcc -x assembler` + `qemu-aarch64 -L /usr/aarch64-linux-gnu`.

Gramática cubierta aquí:

```bnf
imprimir ::= PRINT EXCLAMACION PARIZQ expresion PARDER PUNTOCOMA
expresion ::= expresion SUMA expresion
            | expresion RESTA expresion
            | expresion MULTIPLICACION expresion
            | ENTERO
```

## 1. Instrucciones usadas (solo las necesarias aquí)

| Instrucción | Formato real usado | Funcionalidad |
|---|---|---|
| `mov Xd, #imm` | `mov x9, #4` | Copia inmediato a registro. No toca flags. Sin forma `mul` con inmediato, por eso todo operando se carga primero con `mov`. |
| `mul Xd, Xn, Xm` | `mul x11, x9, x10` | `Xd = Xn * Xm` (64 b bajos). Tiling de `*`. |
| `add Xd, Xn, Xm` | `add x13, x11, x12` | `Xd = Xn + Xm`. Tiling de `+`. |
| `sub Xd, Xn, Xm` | `sub x9, x0, x1` | `Xd = Xn - Xm`. Tiling de `-`. |
| `ldr Xd, =sym` | `ldr x0, =fmt` | Pseudo-instrucción: carga la **dirección** del símbolo (el ensamblador genera `adrp+add`). Se usa para `fmt` y para el valor a imprimir. |
| `ldr Wd, [Xn]` | `ldr w1, [x14]` | Carga 32 b de memoria. Se usa con `w` porque `%d` espera `int`. |
| `bl sym` | `bl printf` | Llama con link (`x30 = retorno`). Requiere `sp` alineado a 16. |
| `stp/ldp`, `mov x29,sp`, `ret` | prólogo/epílogo de `main` | Solo armazón mínimo para poder llamar a libc (detalle completo en 04 y 06). |

## 2. Tiling aritmético (modelo registros, como `object/expresion.asm`)

Precedencia: `*` antes que `+`/`-`, asociatividad izquierda. El árbol `4*5+6` se tilinga como `(4*5)+6`:

```asm
mov x9, #4              // e1
mov x10, #5             // e2
mul x11, x9, x10        // x11 = 20  (nodo *)
mov x12, #6             // e3
add x13, x11, x12       // x13 = 26  (nodo +)
```

Reglas:

```
ENTERO n    →  mov Xt, #n
e1 + e2     →  <e1> → Xa ; <e2> → Xb ; add Xd, Xa, Xb
e1 - e2     →  <e1> → Xa ; <e2> → Xb ; sub Xd, Xa, Xb
e1 * e2     →  <e1> → Xa ; <e2> → Xb ; mul Xd, Xa, Xb
```

Modelo pila alternativo (como `object/main.asm`, útil si el generador es recursivo):

```asm
<tiling e1>             // PUSH e1: sub sp,sp,#8 + str Xa,[sp,#0]
<tiling e2>             // PUSH e2
ldr x1, [sp,#0]         // POP x1 = e2
add sp, sp, #8
ldr x0, [sp,#0]         // POP x0 = e1
add sp, sp, #8
add x9, x0, x1          // sub/mul según operador
sub sp, sp, #8          // PUSH x9
str x9, [sp,#0]
```

## 3. Tiling print (solo libc, modelo actual)

```asm
// println!(26);  — fmt en .data como .asciz "%d\n"
ldr x0, =fmt            // x0 = 1er arg AAPCS64: puntero al formato
mov w1, w13             // w1 = 2do arg: entero a imprimir (w por %d)
// si el valor viene de memoria: ldr w1, [x14]
// si viene de pila: ldr x0,[sp,#0] + add sp,sp,#8 + mov w1,w0
bl printf               // imprime "26\n"
```

`.data` mínimo:

```asm
.section .data
fmt: .asciz "%d\n"
```

## 4. Mini-ejemplo completo (sin variables)

```asm
.global main
.extern printf
.section .data
fmt: .asciz "%d\n"
.section .text
main:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    mov x9, #4
    mov x10, #5
    mul x11, x9, x10
    mov x12, #6
    add w1, w11, w12    // w1 directo como arg de printf
    ldr x0, =fmt
    bl printf
    mov w0, #0
    ldp x29, x30, [sp], #16
    ret
```
