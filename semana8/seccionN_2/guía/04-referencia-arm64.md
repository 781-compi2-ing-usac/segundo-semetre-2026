# 06 — Referencia ARM64 (instrucciones + directivas + ABI)

## Registros y ABI (AAPCS64)

* `x0-x30` (64 b) / `w0-w30` (bajos 32 b). `sp`, `x29=fp`, `x30=lr`, `xzr/wzr`=0.
* Args en `x0-x7`, retorno en `x0`. Caller-saved `x0-x18`, callee-saved `x19-x28`.
* `sp` alineado a 16 antes de todo `bl`. `PUSH Rn = sub sp,sp,#8 + str Rn,[sp,#0]`, `POP Rn = ldr Rn,[sp,#0] + add sp,sp,#8`.

## Tabla completa usada en el proyecto

| Instrucción | Qué hace | Dónde se tilinga |
|---|---|---|
| `mov` | copia reg/imm | literales, `fp=sp`, retorno 0 |
| `ldr =sym` | dirección de símbolo (expande a `adrp+add`) | vars, `fmt`, `buffer` |
| `ldr/str` | memoria ↔ registro | vars, pila evaluadora, structs (`[base,#off]`) |
| `stp/ldp` | push/pop doble 16 B | prólogo/epílogo |
| `add/sub` | suma/resta | `+`, `-`, `push/pop`, `sp` |
| `mul` | mult 64 b (sin inmediato) | `*` |
| `sdiv/udiv` | división | `/` futuro, dígitos en `itoa` |
| `msub` | `Xm-(Xa*Xn)` | `%` como `sdiv+msub` |
| `neg` | `0-Xm` | negación, `itoa` |
| `and/orr/eor` | lógicas | chequeo alineación `sp&15` |
| `lsl/lsr` | shifts | optimización `*2^n` |
| `cmp` | fija `NZCV` | `if`, `==`, `!=`, signo |
| `b/bl/ret` | salto / llamada / retorno | funciones, `printf` |
| `cbz/cbnz` | salto si cero/no-cero | `if`, bucle `itoa` |
| `b.eq/ne/ge/...` | salto por flags | `if`, comparaciones |
| `cset` | `1` si cond else `0` | `==`/`!=` como valor |
| `svc #0` | syscall (`x8=64` write, `93` exit) | solo modelo `_start` |
| `scvtf/fadd/fmul` | int↔float, ops `d0-d31` | `float` futuro |

## Directivas

`.global main/_start`, `.extern printf`, `.text/.data/.bss/.rodata`, `.skip n`, `.word/.xword`, `.asciz`.

## Modelos de build

* `_start` bare-metal: `aarch64-linux-gnu-as + ld` (`build.sh`). Imprime con `itoa + svc`. Sin libc.
* `main` libc: `aarch64-linux-gnu-gcc -x assembler` (`linked-build.sh`). Imprime con `printf`. Requiere `qemu-aarch64 -L /usr/aarch64-linux-gnu`. No mezclar entry points.
