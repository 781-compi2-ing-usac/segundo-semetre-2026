# 03 — Condicionales y comparaciones → ARM64

```bnf
condicional ::= IF expresion LLAVE_OPEN bloque LLAVE_CIERRA
expresion ::= expresion DIGUAL expresion | expresion DIFERENTE expresion
```

## 1. Instrucciones usadas aquí

| Instrucción | Uso | Funcionalidad |
|---|---|---|
| `cmp Xn, Xm/#imm` | `cmp x9, #0` | Resta fantasma que fija flags `NZCV`. Base de todo `if`/`==`/`!=`. |
| `cbz Xt, L` / `cbnz Xt, L` | `cbz x9, L_fin` | Salta si registro es cero / no-cero, sin tocar flags. Tiling directo de `if (expr)` (0 = falso, como `visit_condicional`). |
| `b.eq/ne` (y `b.ge/lt/...`) | `beq L_fin` | Salta según flags tras `cmp`. Alternativa a `cbz`. |
| `cset Wd, cond` | `cset w9, eq` | `Wd = 1` si condición else `0`. Tiling de `==`/`!=` cuando producen un valor. |
| `b L` | `b L_fin` | Salto incondicional para cerrar bloques. |

## 2. Tiling

```asm
// if expr { bloque }
<tiling expr>           // x9 o POP x9
cbz x9, L_fin           // o: cmp x9,#0 + beq L_fin
<tiling bloque>
L_fin:                  // etiqueta única por if (contador L_n)

// e1 == e2 como valor
<e1> → x0 ; <e2> → x1
cmp x0, x1
cset w9, eq             // ne para !=

// if (e1 == e2) { ... } directo (sin cset)
<e1> → x0 ; <e2> → x1
cmp x0, x1
b.ne L_fin
<bloque>
L_fin:
```
