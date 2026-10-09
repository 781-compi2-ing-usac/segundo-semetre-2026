# 09 — Variables locales y recursión → ARM64 (diseño, NO implementado)

> Alcance: cómo pasar de variables globales (`.data`, ver 02) a locales por
> función usando el frame (`fp`), sin romper el modelo de pila ni `call()`.
> Solo diseño: no hay cambios de código asociados todavía.

```bnf
asigna_valor ::= LET ID IGUAL expresion PUNTOCOMA   // igual que hoy
funcion ::= FUNCTION ID PARIZQ PARDER LLAVE_OPEN bloque LLAVE_CIERRA
```

## 1. Punto de partida (lo que hay hoy)

- Todo `let` reserva en `.data` (`nombre: .skip 8`) y se accede con
  `ldr Xt, =nombre` + `ldr/str` (`_push_var`/`_store` en `compilador.py`).
- El frame de función existe (`stp x29,x30 / mov x29,sp … ldp / ret`, ver 04)
  pero sin área de locales (ver 08 §1: el `sub sp` está comentado).
- Los ámbitos hijo de `TablaSimbolo` solo aíslan tipos; dos `x` en ámbitos
  distintos aliasan el mismo slot `.data`.

## 2. Instrucciones usadas aquí (nada nuevo, solo `fp` + aritmética de `sp`)

| Instrucción | Uso | Funcionalidad |
|---|---|---|
| `sub sp, sp, #N` | `sub sp, sp, #16` | Reserva `N` bytes de locales tras el prólogo. `N` múltiplo de 16 (alineación AAPCS64). |
| `ldr/str Xt, [x29, #-off]` | `ldr x9, [x29, #-8]` | Lee/escribe el local a `off` bytes bajo `fp`. `fp` no se mueve: el offset es estable aunque `sp` suba/baje con temporales. |
| `ldr/str Dt, [x29, #-off]` | `str d8, [x29, #-16]` | Igual para `double` (8 B por slot, igual que `.data`). |
| `add sp, sp, #N` | antes del `ldp` | Libera los locales. Simétrico al `sub`; va entre `L_fn_fin` y el epílogo para que `return` también limpie. |

## 3. Tiling propuesto

```
// Frame FIJO pre-calculado: N locales → TOTAL = redondeo16(N*8)
_fn_f:
    stp x29, x30, [sp, #-16]! // prólogo (igual que 04)
    mov x29, sp
    sub sp, sp, #TOTAL        // reserva de locales (0 si no hay)
    ...cuerpo...              // lets → [x29, #-8], [x29, #-16], ...
L_fn_fin_N:
    add sp, sp, #TOTAL        // libera locales (return cae aquí)
    ldp x29, x30, [sp], #16   // epílogo (igual)
    ret

// let x = expr  (x es local con offset 8)
<pila: expr deja tope>
    ldr x0, [sp, #0]          // POP a temporal (vía pop_auto_x)
    add sp, sp, #8
    str x0, [x29, #-8]        // x = tope

// x como expresión (local)
    ldr x9, [x29, #-8]        // x9 = x
    sub sp, sp, #8            // PUSH x9
    str x9, [sp, #0]
```

## 4. Dónde vive cada cosa (mapa de memoria en una llamada)

```
direcciones altas
    [fp+...]  marco del llamante (intocable)
    [x29]     fp salvado | [x29,#8]  lr salvado   (stp del prólogo)
    [x29,#-8]   local 1
    [x29,#-16]  local 2
    ...       locales (zona fija, TOTAL bytes)
    [sp]      temporales de expresión (zona móvil, múltiplos de 8)
direcciones bajas
```

Reglas:
1. Locales bajo `fp` fijo; temporales sobre `sp` móvil. Nunca se mezclan.
2. `TOTAL % 16 == 0` siempre (aunque `N*8` no lo sea) → `sp` sigue alineado
   ante cada `bl`; el relleno de `call()` y `_depth` no cambian.
3. `return`/`b` no tocan `sp`: a nivel sentencia la pila está balanceada,
   así que saltar a `L_fn_fin` nunca deja basura.

## 5. Resolución de nombres (visibilidad)

Orden de búsqueda en `_push_var`/`_store`, únicos dos puntos de acceso:

1. Mapa de locales de la función activa (`fn → {var: offset}`), si lo hay.
2. Símbolo global `.data` (ruta actual: `ldr Xt, =nombre`).

Efectos:
- Un `let` dentro de `def` crea local y **sombrea** a la global homónima.
- Sin local, la global sigue visible (compatibilidad con `entrada.txt` actual).
- Nombres repetidos en la misma función reutilizan slot (re-`let` = asignación,
  idéntica semántica a la global actual; ver 02).
- `main` y `if/while` top-level siguen en `.data` (cambio mínimo).

## 6. De dónde salen los offsets (pre-barrido, no adivinanza)

`parse()` ya hace dos pasadas (opción B, ver 04). Se añade una recolección por
`funcion`, junto a `inferir_retornos`, que recorre el subárbol del cuerpo
(incluidos `if/while` anidados) en orden y asigna `8, 16, 24…` a cada `let`
con nombre no visto. Sin gramática nueva: el `let` ya existe donde hace falta.

## 7. Recursión: qué queda garantizado y qué no

Garantizado por construcción (mecánica segura):
- Cada `bl` crea un frame fresco: los locales de un nivel nunca aliasan los de
  otro; la cuenta `TOTAL` es estática por función, así que la profundidad solo
  consume `16 + TOTAL` bytes por nivel.
- Los temporales del llamante sobreviven: están en memoria bajo `sp` y el
  callee restaura `sp` simétricamente (`add` + `ldp`).
- El retorno (`x0`/`d0` + `b L_fn_fin`) propaga el valor nivel por nivel.

Límite real (de la gramática, no del frame):
- Las funciones son `paramless`: sin parámetros, toda invocación recursiva es
  idéntica (locales re-inicializados igual, globales constantes durante la
  llamada). El caso base o se cumple al primer nivel o nunca (→ stack overflow,
  sin guardia). Un factorial o una cuenta-regresiva genuinos exigen parámetros.
- Prueba honesta cuando se implemente: autollamada con base inmediata
  (verifica no-corrupción del frame + propagación del retorno) y llamadas
  anidadas `a()→b()→c()` (locales de cada nivel intactos).

## 8. Puente hacia parámetros (extensión futura, fuera de alcance)

El diseño ya es compatible: los argumentos serían más slots `[x29, #+off]`
(sobre `fp`, convención AAPCS64) o los primeros bajo `fp`, evaluados en el
call-site (`x0-x7`/`d0-d7`) y guardados al entrar. Requiere gramática
(`def f(x, ...)` + args en la llamada) y precede a cualquier recursión útil.
