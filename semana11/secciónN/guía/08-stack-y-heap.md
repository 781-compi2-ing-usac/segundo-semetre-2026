# 08 — Stack y heap en ARM64 (guía corta)

> Ver diagrama: `08-stack-y-heap.puml` / `.svg`.
> Ejemplos reales: `object/main.asm` (stack-VM + heap bump) y `object/expresion.asm` (solo stack-frame + libc).

## 1. Stack (pila): LIFO, crece hacia abajo, 16 B alineado

Usos: temporales de expresión, `push/pop`, frames (`fp/lr`, locales), args extra y dirección de retorno.

```asm
// PUSH x9 (8 B) — como main.asm
sub sp, sp, #8
str x9, [sp, #0]

// POP x1
ldr x1, [sp, #0]
add sp, sp, #8

// Frame estándar (como expresion.asm / _fn_sum)
main:
    stp x29, x30, [sp, #-16]!  // guarda FP+LR, sp -= 16
    mov x29, sp                // nuevo FP
    // sub sp, sp, #16          // solo si hay locales
    ...
    // add sp, sp, #16          // liberar locales
    ldp x29, x30, [sp], #16    // restaura, sp += 16
    ret
```

Reglas:
1. Todo `sub/ldp` simétrico; `sp % 16 == 0` antes de cada `bl`.
2. Temporales en `x9-x15`; lo que sobrevive a `bl` va a `x19-x28` (salvados con `stp`).
3. No mezclar `w/x` en el mismo slot; un `int` en pila ocupa 8 B aunque imprimas con `w`.

## 2. Heap: bump allocator de `main.asm` vs `malloc` con libc

Modelo bare-metal (`_start`, sin libc) de `object/main.asm`:

```asm
.section .bss
heap_base: .skip 1048576   // 1 MiB reservado
heap_end:

_start:
    ldr x20, =heap_base    // x20 = heap_ptr (bump)
    ldr x21, =heap_end     // x21 = límite
```

Allocar N bytes (pseudo-tiling para un futuro `alloc n`):

```asm
// x0 = n bytes, retorna x0 = ptr
add x9, x20, x0            // nuevo tope
cmp x9, x21
b.hi _panic_oom            // sin espacio → exit(1)
mov x0, x20                // ptr = tope actual
mov x20, x9                // heap_ptr += n
```

Modelo libc (`main` + `bl printf`, como `expresion.asm`): no gestiones heap a mano; usa `bl malloc` (`x0=n → x0=ptr`) y `bl free` (`x0=ptr`). El linker (`linked-build.sh`) ya provee el heap.

| Decisión | Stack | Heap |
|---|---|---|
| Tamaño fijo/pequeño, vida = función/expresión | ✅ `sub sp` | ❌ |
| Vida larga, tamaño dinámico, structs grandes | ❌ | ✅ bump o `malloc` |
| Olvidas liberar | se libera con `ldp/ret` | leak (bump nunca libera; `malloc` pide `free`) |
| Te pasas del límite | stack overflow (choque) | `_panic_oom` / `NULL` de `malloc` |

Checklist: 1 etiqueta `heap_base/end` por programa, 2 registros dedicados (`x20=ptr`, `x21=end`, callee-saved), nunca usar `x20/x21` como temporales.
