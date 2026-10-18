# 10 — Arrays (`let`, `a[i]`, N-D row-major) → ARM64

```bnf
asigna_valor ::= LET ID DOBDOT tipo_array IGUAL inst_array PUNTOCOMA
tipo_array ::= BRACK_OPEN tipo PUNTOCOMA ENTERO BRACK_CIERRA
             | BRACK_OPEN tipo_array PUNTOCOMA ENTERO BRACK_CIERRA
inst_array ::= BRACK_OPEN lista_init BRACK_CIERRA
lista_init ::= lista_init COMA elem_init | elem_init
elem_init ::= expresion | inst_array
asigna_indice ::= expresion BRACK_OPEN expresion BRACK_CIERRA IGUAL expresion PUNTOCOMA
expresion ::= ... | expresion BRACK_OPEN expresion BRACK_CIERRA
```

Declaración estilo Rust con los tipos de la gramática (`int`/`float`):
`let m : [[int; 3]; 2] = [[1, 2, 3], [4, 5, 6]];`. Las dims salen del tipo
(externo → interno = `[d0, d1, ...]`); el literal anidado se aplana row-major.
Literal corto → zero-fill, largo → se trunca (ambos con `// ARRAY ERROR`).

## 1. Instrucciones usadas aquí

| Instrucción | Uso | Funcionalidad |
|---|---|---|
| `.skip N*8` | `m: .skip 48` | Bloque contiguo en `.data` (`declare_array`, ver 02 §2). |
| `lsl Xt, Xt, #3` | `lsl x11, x11, #3` | Índice lineal → bytes (slot 8 B, int y double). |
| `mul Xt, Xs, Xn` | `mul x13, x12, x11` | Horner row-major (sin inmediato: `mov` previo del stride/dim). |
| `add Xt, Xn, #k*8` / `str Xt,[Xn,#k*8]` | init desenrollado | Relleno/literal sin bucle (N estática). |
| `ldr/str Xt, [Xb]` | `ldr x15, [x9]` | Elemento en la dirección calculada por `_addr_idx`. |

## 2. Tiling

```
// let a : [int; 3] = [7,7,7]  (literal aplanado: eval+store por slot)
<eval 7> + ldr xB, =a + pop + str [xB,#0] + <eval 7> + ... str [xB,#8] ...

// READ a[i][j], dims [d0,d1]  (strides: lineal = i0*s0 + i1*s1, s1 = 1)
<eval i0, push> <eval i1, push>
pop ri1 (=tope, stride 1, sin mul) + pop ri0 + mul(i0,s0) + add ... lsl #3
ldr xB, =a + add xB, xB, rLin + ldr rR, [xB] + push rR

// WRITE a[i][j] = v  (valor PRIMERO al fondo de la pila, a salvo en memoria)
<eval v, push> <eval i0, push> <eval i1, push>
<Horner + base> + pop rv + str rv, [xB]
```

## 3. Heap con lifetime por ámbito (modelo puro)

Cero bytes de arrays en `.data`: todo array vive en el heap bump (`x20`/`x21`,
región `.bss` de 64 KiB) y muere con su ámbito. Leer fuera del ámbito
(otra función, `def` anidado) → `// IDX ERROR` + dummy 0.

```
// Frame fp por función (pre-pass disponer_frames, off 8 = mark del prólogo)
_fn_f: stp x29,x30 + mov x29,sp + sub sp,#P + str x20,[x29,#-8]
...
L_fn_fin: ldr x20,[x29,#-8] + add sp,#P + ldp + ret

// Nivel if/while: guarda mark + slots a 0 a la entrada, restaura a la salida
str x20, [x29,#-mark] + str xzr, [x29,#-slot] ... ldr x20, [x29,#-mark]

// Declaración: guard cbnz + carve (una vez por activación)
ldr xH, [x29,#-slot] + cbnz xH, L_done + mov+lsl+add vs x20
+ cmp x21 + b.hi L_heap_oom + mov xH,x20 + mov x20,xT + str xH,[x29,#-slot]
```

## 4. Impresión (`println!(m)` con el id pelado)

Desenrollado en orden de memoria (== row-major): cada elemento con `fmtsp`
(`"%d "`) / `fmtfsp` (`"%f "`) y `fmtnl` (`"\n"`) al cerrar cada fila
(`dims[-1]` elementos). 1-D = una sola fila.

```
println!(m);  // m : [[int; 3]; 2] = [[1,2,3],[4,5,6]]
1 2 3
4 5 6
```

## 5. Reglas

1. Row-major por strides estáticos: `lineal = Σ i_k·s_k` con `s_k = Π dims tras k`;
   1-D y último eje tienen stride 1 (sin `mul`).
2. Acumulación desde el tope (`k = n-1..0`): conjunto vivo ≤ 5 registros → el pool
   round-robin de 6 jamás pisa un valor vivo, para cualquier n (ver 07).
3. La base (`ldr xH, [x29,#-slot]`) se adquiere **después** de evaluar; el valor
   a guardar se evalúa **antes** que los índices (queda al fondo de la pila).
4. Registro: layouts fp por función (`scope_id → {nombre: (elem, dims, off)}`) +
   marcador `"array"` en la tabla de tipos; leer el array pelado (`a` sin `[i]`)
   emite `// IDX ERROR` + dummy 0 (pila balanceada). Aridad distinta → igual.
   Sin chequeo de bounds (estilo C). Recursión: cada activación tiene sus slots
   (offsets fp distintos) — verificado con desenrollado `2/1/0`.
5. Conversiones int↔float como `_store` (`_pop_como`); `return a[i];` usa el tipo
   del elemento (`_tipo_ret_sintactico`, heurístico global solo en inferencia).
6. Protocolo: toda `_fn_` preserva `x20` (prólogo/epílogo); `x20/x21` fuera del
   pool. OOM = `exit(1)` (`L_heap_oom`). Programas sin arrays generan el `.asm`
   idéntico al de antes (header condicional).
