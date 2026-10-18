# 02 — Variables y asignación (`let`) → ARM64

```bnf
asigna_valor ::= LET ID IGUAL expresion PUNTOCOMA
               | LET tipo ID IGUAL expresion PUNTOCOMA
expresion ::= ENTERO | DECIMAL | ID
```

## 1. Instrucciones usadas aquí

| Instrucción | Uso | Funcionalidad |
|---|---|---|
| `ldr Xt, =var` | `ldr x14, =numero` | Dirección de la variable global (pseudo-instrucción → `adrp+add`). |
| `str Xs, [Xn]` | `str x13, [x14]` | Guarda el valor evaluado en la variable. Base de `let`. |
| `ldr Xd, [Xn]` / `ldr Wd,[Xn]` | `ldr x9, [x14]` | Lee variable (`x` 64 b, `w` para `%d`). Tiling de `ID` como expresión. |
| `mov` | `mov x9, #n` | Tiling de `ENTERO`. |
| `.skip 8` | `numero: .skip 8` | Reserva 8 bytes en `.data` por cada `int`. |

## 2. Tiling

```
// LET ID = expr  →  <expr> deja valor en Xt (o en pila)
ldr x14, =id            // x14 = &id
str Xt, [x14]           // id = Xt
// modelo pila: POP x0 + ldr x14,=id + str x0,[x14]

// ID como expresión (leer)
ldr x14, =id
ldr x9, [x14]           // x9 = id (w si int32)
```

`let int/float id = ...` genera lo mismo hoy; el chequeo de tipos es semántico (`interprete.py:visit_asignacion`), no emite código distinto. `DECIMAL` queda pendiente (banco `d`, `scvtf/fmov`, ver 06).
