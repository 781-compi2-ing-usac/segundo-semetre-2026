# 04 — Funciones (`def` / llamada) → ARM64

```bnf
funcion ::= FUNCTION ID PARIZQ PARDER LLAVE_OPEN bloque LLAVE_CIERRA
call_funcion ::= ID PARIZQ PARDER PUNTOCOMA
expresion ::= ID PARIZQ PARDER
```

## 1. Instrucciones usadas aquí

| Instrucción | Uso | Funcionalidad |
|---|---|---|
| `stp x29,x30,[sp,#-16]!` | prólogo | Guarda `fp+lr` de una vez, `sp -= 16`. Mantiene alineación a 16 exigida por AAPCS64 antes de `bl`. |
| `mov x29, sp` | prólogo | Nuevo frame pointer. |
| `bl etiqueta` | `bl _fn_sum` / `bl f` | Llama: `x30 = pc+4, pc = etiqueta`. |
| `ldp x29,x30,[sp],#16` | epílogo | Restaura `fp+lr`, `sp += 16`. |
| `ret` | fin | `pc = x30`. |
| `mov w0/x0, #0` | retorno | Valor de retorno (hoy las funciones no retornan; se devuelve 0). |

## 2. Tiling

```asm
_f:                             // una etiqueta por función (ej. _fn_sum en main.asm)
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    <tiling bloque>
    mov x0, #0
    ldp x29, x30, [sp], #16
    ret
// llamada como instrucción o expresión:
bl _f
```

Notas: cada función/`if` abre ámbito hijo (`TablaSimbolo(padre)` en el intérprete); en ASM equivale a nuevo frame + etiquetas `L_n` únicas. En `main.asm` hay chequeo extra de alineación (`and x19,sp,#15`) antes del `bl`; con prólogo simétrico no hace falta.
