# ARM64 de bolsillo — guía de lectura y ejercicios para hacer solos

Organización de Lenguajes y Compiladores 2 — Sección B · semana del 15/09/2026
Material de apoyo para el Proyecto 2 (**OxigenNative**)

---

## Por qué esta semana es distinta

El martes 15 es asueto (Día de la Independencia) y no hay clase. Pero el
Proyecto 2 no espera, así que en vez de una sesión nueva esta semana trae
una **tarjeta de referencia** de lo que ya vieron en `semana8/seccionB` y
tres ejercicios para comprobar, ustedes mismos, que lo que creen haber
entendido realmente lo entendieron.

`arm/`, `micro/` y `minipascal/` son copia exacta de `semana8/seccionB`:
ni una línea cambió. Compruébenlo con `diff -r semana8/seccionB semana9/seccionB`
— la única diferencia debe ser este README.

---

## La tarjeta de bolsillo

Todo esto ya lo usaron en `01_hola.s` y `02_aritmetica.s`. Aquí está
junto, para no tener que rearmarlo de memoria cada vez.

**Registros**

| Registro | Para qué lo usaron |
|---|---|
| `x0` | resultado de toda expresión (la regla de la Sesión 1); también el primer argumento de una llamada (`printf`, `write`) |
| `x1`, `x2` | segundo y tercer argumento de una llamada |
| `x8` | número de syscall, solo cuando se habla con el kernel directo (`svc #0`) |
| `x29` | frame pointer — dónde empieza el marco de la función actual |
| `x30` | link register — a dónde volver con `ret` |
| `sp` | tope de la pila; en AArch64 siempre alineado a 16 bytes |
| `wN` | la mitad baja (32 bits) del mismo registro `xN` — es el mismo banco, dos nombres |

**Modos de direccionamiento**

| Forma | Significa | Dónde la vieron |
|---|---|---|
| `mov x0, #2` | un valor inmediato, escrito en la instrucción misma | cargar constantes |
| `adrp x1, mensaje` seguido de `add x1, x1, :lo12:mensaje` | dirección de una etiqueta, en dos pasos | `.data`, `01_hola.s` |
| `[sp, #-16]!` | pre-index: primero mover `sp`, después usar la dirección nueva | empujar a la pila |
| `[sp], #16` | post-index: primero usar la dirección actual, después mover `sp` | sacar de la pila |

**Instrucciones**

| Instrucción | Qué hace |
|---|---|
| `mov` | copiar un valor (inmediato o de otro registro) a un registro |
| `add` / `sub` / `mul` | aritmética entre registros |
| `str` / `ldr` | guardar / leer un registro en memoria |
| `stp` / `ldp` | lo mismo que `str`/`ldr` pero con DOS registros de una vez |
| `bl` | llamar una función: salta y guarda la dirección de retorno en `x30` |
| `ret` | volver a la dirección que hay en `x30` |
| `svc #0` | pedirle algo al kernel (la syscall que esté en `x8`) |

Un dato que ya vieron pero vale la pena volver a decir: **toda instrucción
ARM64 mide exactamente 4 bytes**. Por eso una dirección de 64 bits nunca
cabe en una sola instrucción, y por eso `adrp`/`add :lo12:` son siempre
dos.

---

## Cómo seguir leyendo solos

Dos herramientas del propio toolchain que ya instalaron sirven para
comprobar todo esto sin depender de que alguien se los explique.

**`objdump -d`** — muestra lo que el ensamblador produjo realmente,
instrucción por instrucción, con su codificación en hexadecimal:

```bash
cd semana9/seccionB/arm
./build.sh 02_aritmetica.s
aarch64-linux-gnu-objdump -d 02_aritmetica | less
```

Busquen la función `main` en la salida. Cada línea trae la dirección, los
4 bytes en hexadecimal y la instrucción tal como la escribieron ustedes.
Confirmen con sus propios ojos que ninguna línea mide otra cosa que 4
bytes.

**`gcc -S`** — les deja ver cómo traduce un compilador de verdad la MISMA
idea, para comparar contra lo que escribieron a mano:

```bash
cat > prueba.c << 'EOF'
#include <stdio.h>
int main(int argc, char **argv) {
    printf("%d\n", argc + argc * 4);
    return 0;
}
EOF
aarch64-linux-gnu-gcc -S -O0 prueba.c -o prueba.s
cat prueba.s
```

(Usen `argc` y no un literal como `2 + 3 * 4`: gcc calcula los literales en
tiempo de compilación y el `.s` les sale sin una sola cuenta, que no deja
nada que comparar.)

No esperen que se parezca línea a línea a `02_aritmetica.s` — gcc no usa
el modelo de pila de la Sesión 1, y con `-O0` igual toma decisiones raras.
La pregunta que vale la pena es la del ejercicio 2.

---

## Ejercicios

1. **Contar bytes.** Corran `objdump -d` sobre `02_aritmetica` como arriba
   y anoten, para cada instrucción de la sección "Calcular 2 + 3 * 4" del
   archivo fuente, su dirección y su codificación en hex. Confirmen que
   todas miden 4 bytes — incluida `adrp`, que a algunos les da la
   impresión de "hacer más" que las demás.

2. **Leer a gcc.** Generen `prueba.s` como arriba y busquen, en la salida
   de gcc, alguna instrucción que **no** esté en la tarjeta de esta
   guía. Anótenla y, con el manual de referencia de ARM64
   (<https://developer.arm.com/documentation/ddi0487/latest/>), averigüen
   qué hace. No hace falta entenderla a fondo — solo confirmar que pueden
   buscarla sin que nadie se las explique primero.

3. **La tarjeta a ciegas.** Sin mirar la sección "La tarjeta de bolsillo"
   de arriba, escriban de memoria — en papel o en un `.md` — qué hace cada
   instrucción de la tabla. Después comparen. Cualquiera que fallen o
   duden es la que hay que releer en `semana8/seccionB/README.md` antes
   del martes 22.

4. **Deuda pendiente.** Si todavía no resolvieron el ejercicio 3 de la
   semana pasada (el `sdiv` entero que no coincide con la división de
   Python), resuélvanlo ahora. No depende de nada nuevo de esta guía, y
   conviene no acumularlo.

---

## Antes de irse

Nos vemos el martes 22 de septiembre. Si `./build.sh` todavía no les
corre en su máquina, ese es el pendiente más urgente de esta semana —
revisen la sección de toolchain en `semana8/seccionB/README.md` y
búsquenme antes de esa fecha si nada funciona.
