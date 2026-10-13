# Heap y control de flujo en ARM64

Organización de Lenguajes y Compiladores 2 — Sección B · semana 12 (martes 13/10/2026)
Material de apoyo para el Proyecto 2 (**OxigenNative**) · **Entrega: viernes 23/10/2026**

Esta carpeta se va completando: cada parte trae sus propios archivos
numerados en `arm/`, `micro/` y `minipascal/ejemplos/`, y el generador
(`generador_arm.py`) va acumulando lo de todas. Léanla en orden.

---

## Qué hay en esta carpeta

```
segundo-semetre-2026/
└── semana12/seccionB/
    ├── arm/
    │   ├── 01_hola.s … 03_variables.s, build.sh   (sin cambios)
    │   ├── 04_brk.s              parte 1 — pedirle memoria al kernel
    │   ├── 05_alloc_tabla.s      parte 1 — una rutina alloc y su tabla
    │   └── 06_control_flujo.s    parte 2 — while, if, break, continue
    ├── micro/
    │   ├── 01 … 03               (sin cambios)
    │   ├── 04_heap_modelo.py     parte 1 — el heap modelado en Python
    │   └── 05_etiquetas.py       parte 2 — etiquetas únicas y pila de ciclos
    └── minipascal/
        ├── generador_arm.py      CAMBIÓ — arreglos en el heap, if, while
        ├── ejemplos/
        │   ├── 01 … 11           (sin cambios)
        │   ├── 12_heap.mpas          parte 1
        │   └── 13_control_flujo.mpas parte 2
        └── el resto — lexer, parser, ast_nodes, interprete, ... — sin cambios
```

Compruébenlo, igual que siempre:

```bash
diff -r semana10/seccionB semana12/seccionB
```

Tiene que mostrar los archivos nuevos de arriba y **un solo archivo de
código cambiado**, `generador_arm.py` (más retoques menores en
`.gitignore` y `requirements.txt`). Ni el AST ni el intérprete se
tocaron: el generador es el único que aprende algo nuevo.

---

## Cómo correrlo

```bash
cd semana12/seccionB
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 1. Ensamblador a mano — empiecen por aquí
cd arm
./build.sh 04_brk.s              # 64, 42, 7
./build.sh 05_alloc_tabla.s      # 50, 5, 2, 32, 16, 32
./build.sh 06_control_flujo.s    # 12

# 2. Los modelos, sin ensamblador
cd ../micro
python3 04_heap_modelo.py
python3 05_etiquetas.py

# 3. Los dos caminos sobre el mismo árbol
cd ../minipascal
python3 main.py            ejemplos/12_heap.mpas           # intérprete
python3 main.py --compilar ejemplos/12_heap.mpas           # ARM64 + QEMU
python3 main.py            ejemplos/13_control_flujo.mpas
python3 main.py --compilar ejemplos/13_control_flujo.mpas
```

Cada pareja de líneas (intérprete y `--compilar`) tiene que imprimir
exactamente lo mismo. `12_heap.mpas` imprime `50 5 0 25`, y
`13_control_flujo.mpas` imprime `1 0 1 2 3 4 12 6 1` (un número por línea).

Y, como siempre, comprueben que nada de lo anterior se rompió:

```bash
python3 main.py --compilar ejemplos/10_aritmetica.mpas
python3 main.py --compilar ejemplos/11_variables.mpas
```

---

# Parte 1 — El heap con `brk` y una tabla de bloques

## El problema

Hasta ahora, toda la memoria de sus programas vivía en el **stack**:
cada variable tiene su celda en el frame, y todo se suelta junto cuando
termina la función. Eso funciona mientras el compilador sepa, al generar
el código, cuánta memoria hace falta y cuánto va a durar.

El enunciado (sección 3.1.3) pide además un **heap**: memoria que el
programa le pide al sistema operativo mientras corre, para "cadenas y
arreglos de tamaño dinámico". Y dice que el modelo de memoria es
**explícito**: no vale llamar a `malloc` y olvidarse. Hay que construir
la reserva y llevar la cuenta de lo reservado.

> Una variable ya sabe vivir en una celda del stack. ¿Cómo hace una
> celda de 16 bytes para "tener" un arreglo de 1000 enteros?

Respuesta corta: **no lo tiene. Guarda la dirección de dónde está.**

## Las ideas

### 1. El heap es una zona que crece: `brk`

Pedirle algo al kernel es lo mismo que hicieron en `01_hola.s` con
`write`: el número de la syscall va en `x8` y se ejecuta `svc #0`
(*SuperVisor Call*: "kernel, haz esto por mí").

| Syscall | Número |
|---|---|
| `write` | 64 |
| `exit`  | 93 |
| `brk`   | **214** |

El kernel guarda, para cada programa, una dirección llamada **program
break**: donde termina la memoria de datos que le entregó. Lo que está
debajo se puede usar; lo que está arriba, no.

```
brk(0)     ->  devuelve el break actual (no cambia nada)
brk(dir)   ->  mueve el break a `dir` y devuelve el break nuevo
```

Reservar N bytes es: leer el break, pedir `break + N`, y usar lo que
quedó en medio. Eso es todo el heap. Está en `arm/04_brk.s`:

```asm
mov x0, #0          // brk(0)
mov x8, #214
svc #0              // x0 = el break actual: donde empieza el bloque nuevo
```

### 2. La celda guarda una dirección, no los datos

Una variable de tipo arreglo sigue teniendo su celda en el frame, con su
offset desde `x29`, igual que en la sesión de variables. Lo único
distinto es lo que se escribe en esa celda:

```
 STACK (el frame)                      HEAP (lo que pidió brk)
┌──────────────────┐                  ┌───┬───┬───┬───┐
│ [x29,#-16]  a ───┼─────────────────►│ 0 │ 0 │ 0 │ 0 │   32 bytes
├──────────────────┤                  ├───┼───┴───┴───┘
│ [x29,#-32]  b ───┼─────────────────►│ 0 │ 0 │             16 bytes
└──────────────────┘                  └───┴───┘
```

Leer `a[3]` pasa a ser **dos** lecturas, y no una:

```asm
ldr x1, [x29, #-16]     // 1. traer el PUNTERO, desde el stack
ldr x0, [x1, #24]       // 2. traer el VALOR, desde el heap  (3 * 8 = 24)
```

Es la única novedad a nivel de instrucciones. Todo lo demás es
contabilidad.

### 3. `alloc` y la tabla

Un programa pide memoria muchas veces, y necesita saber qué pidió. Hay
dos piezas:

- **`alloc`**: recibe cuántos bytes en `x0`, devuelve en `x0` la
  dirección del bloque.
- **La tabla**: por cada bloque que `alloc` entrega, una fila
  `[base][tamaño]`.

```
tabla_heap                    tabla_n
┌──────────┬────────┐        ┌───┐
│ base  a  │   32   │ fila 0 │ 2 │
├──────────┼────────┤        └───┘
│ base  b  │   16   │ fila 1
└──────────┴────────┘
```

La fila `i` empieza en `tabla_heap + i * 16`. Con `lsl #4` (desplazar 4
bits = multiplicar por 16) sale en una sola instrucción:

```asm
add x13, x13, x12, lsl #4     // x13 = tabla_heap + índice * 16
```

`arm/05_alloc_tabla.s` trae `alloc` completa, comentada, y al final
imprime la tabla para que la vean funcionando. Fíjense en el último
número que imprime: `32`. Es la distancia entre la base de `a` y la
base de `b`: **un bloque empieza exactamente donde termina el
anterior**. Esa observación vale oro en el ejercicio 3.

### 4. Copiar una variable copia la dirección

`micro/04_heap_modelo.py` modela el heap con objetos de Python. Lo
importante está al final: después de `b := a`, las dos celdas apuntan al
mismo bloque, y escribir por una cambia lo que lee la otra. Y el bloque
que `b` tenía antes sigue en la tabla, sin dueño.

Si el lenguaje de ustedes quiere que `b := a` **copie los datos**,
alguien tiene que pedir un bloque nuevo y copiar elemento por elemento.
Ese "alguien" es el compilador, y las instrucciones que hacen la copia
las tienen que generar ustedes.

### 5. El heap arranca en ceros, y no es casualidad

Un arreglo de `integer` recién declarado vale 0 en todas sus casillas, y
el generador no escribe ninguna instrucción para eso. Es el kernel:
nunca le entrega a un programa páginas con datos de otro, así que la
memoria que da `brk` viene limpia.

Eso coincide con el valor por defecto de `integer`. **No coincidiría**
con ningún otro valor por defecto: si su lenguaje define uno distinto,
hay que escribirlo.

### 6. Una advertencia sobre `printf` y el heap

El programa pide memoria con `brk` por su cuenta. La biblioteca de C,
que enlazamos para `printf`, tiene además su propio administrador
(`malloc`), que también usa `brk`. **No saben el uno del otro.**

Lo que probamos:

- `printf` y nuestro `alloc` en el mismo programa, 2000 reservas
  intercaladas con 2000 impresiones: ninguna celda alterada.
- Nuestro `alloc` mezclado con llamadas a `malloc`/`free` de la
  biblioteca de C: **más de la mitad de las celdas aparecieron
  alteradas**, sin ningún error. Los dos administradores se repartieron
  las mismas direcciones.

Regla para todo el proyecto: **o es el `alloc` de ustedes, o es el de la
biblioteca. Nunca los dos.** Por eso este generador usa de libc solo
`printf`, y por eso no aparece `malloc` en ningún archivo.

## Ejercicios de la parte 1

1. **Seguirlo con papel.** Abran `arm/05_alloc_tabla.s` y dibujen, línea
   por línea, tres cosas: el frame, el break del heap y la tabla.
   Anoten cuánto vale cada una después de cada `bl alloc`.

2. **Una fila más.** Agreguen a mano, en una copia de
   `05_alloc_tabla.s` llamada `07_prueba.s`, un tercer arreglo
   `c: array[3] of integer`. Antes de correrlo, predigan: ¿cuánto vale
   `tabla_n`? ¿En qué offset del frame queda `c`? ¿A qué distancia de la
   base de `b` queda la base de `c`? Después corran `./build.sh
   07_prueba.s` y comparen.

3. **El desborde que nadie avisa.** Corran esto por los dos caminos:

   ```pascal
   program Fuera;
   begin
     var a: array[4] of integer;
     var b: array[2] of integer;
     b[0] := 7;
     a[4] := 99;        { `a` solo tiene casillas 0 a 3 }
     writeln(b[0]);
   end.
   ```

   El intérprete imprime `7` y reporta un error semántico. El
   generador imprime **99**. Expliquen, con lo que aprendieron en la
   idea 3, por qué `a[4]` terminó siendo `b[0]`. Es otro caso de
   intérprete y generador en desacuerdo, y es de los más peligrosos: el
   programa "funciona".

4. **Ver la tabla desde MiniPascal.** El programa generado tiene una
   tabla, pero nunca la imprime. Agreguen al final de `ensamblar_archivo`
   (antes del epílogo) las instrucciones que impriman cuántas filas hay,
   usando como modelo lo que hace `05_alloc_tabla.s`. Ojo: el intérprete
   no sabe nada de esa tabla, así que la salida de los dos caminos
   **dejará de coincidir**. Decidan si eso es un problema o si esa
   salida debería ir por otro lado.

---

# Parte 2 — Control de flujo: etiquetas y saltos

## El problema

Hasta ahora el generador escribía las instrucciones en el mismo orden en
que el programa las enunciaba: de arriba hacia abajo, sin volver nunca.
Un `while` pide volver. Un `if` pide saltarse algo. Y no existe ninguna
instrucción ARM64 llamada `if` ni `while`.

> Si no hay instrucción `while`, ¿qué se escribe cuando el generador
> encuentra un nodo `While`?

Respuesta corta: **etiquetas y saltos.** Un `if` o un `while` son una
manera de acomodar etiquetas alrededor de otras instrucciones.

## Las ideas

### 7. `cmp` no devuelve nada: deja banderas

Hay cuatro instrucciones nuevas, y con ellas alcanza:

| Instrucción | Qué hace |
|---|---|
| `cmp a, b` | Resta `a - b`, tira el resultado, y **recuerda su signo** en cuatro banderas internas (NZCV). |
| `cset x0, lt` | Lee las banderas: `x0 = 1` si el último `cmp` dio "menor que", si no `0`. |
| `b.eq etiqueta` | Salta a `etiqueta` **si** el último `cmp` dio "igual". Si no, sigue con la siguiente línea. |
| `b etiqueta` | Salta siempre, sin mirar nada. |

Las condiciones son siempre las mismas seis, y cada una es una forma de
leer las banderas:

| MiniPascal | `eq` | `ne` | `lt` | `gt` | `le` | `ge` |
|---|---|---|---|---|---|---|
| operador | `==` | `!=` | `<` | `>` | `<=` | `>=` |

Una comparación en el generador es una operación binaria más: izquierdo,
empujar, derecho, recuperar. Lo único distinto es el último paso:

```asm
cmp  x0, x1          // en vez de `add x0, x0, x1`
cset x0, lt          // x0 = 1 si izquierdo < derecho, si no 0
```

### 8. `if` y `while` son etiquetas y saltos

Esta es la plantilla. Está comentada en `generador_arm.py`
(`visitar_If`, `visitar_While`) y completa en `arm/06_control_flujo.s`:

```
 if sin else          if con else           while

     <condición>          <condición>       inicio:
     si falso -> fin      si falso -> sino      <condición>
     <bloque>             <bloque_si>           si falso -> fin
 fin:                     saltar a fin          <cuerpo>
                      sino:                     saltar a inicio  <- el ciclo
                          <bloque_no>       fin:
                      fin:
```

El "si falso" son dos instrucciones, porque la condición ya es un 0 o un
1 en `x0`:

```asm
cmp  x0, #0
b.eq .Lfin           // falso: saltar
```

El salto hacia atrás, `b inicio`, **es** el ciclo. No hay nada más.

### 9. Cada etiqueta tiene que ser única, y `break` necesita una pila

Dos `if` en el mismo programa no pueden compartir el nombre de su
etiqueta final: el ensamblador responde `symbol '.Lfin' is already
defined`. La solución es un contador que solo sube, y el nombre sale de
ahí: `.Lif_fin_3`, `.Lwhile_fin_5`. El `.L` inicial le dice al
ensamblador que es una etiqueta local: sirve para saltar, pero no
aparece en la tabla de símbolos del binario.

`break` y `continue` tienen otro problema. No hay ninguna instrucción
llamada "break": es un `b` a la etiqueta de **fin** del ciclo (o a la de
**inicio**, si es un `continue`). Pero el nodo `Break` no sabe en qué
ciclo está. Lo sabe el generador, que lleva una **pila de ciclos
abiertos**:

```
al entrar a un while  ->  se apila  {inicio, fin}
al salir de un while  ->  se desapila
un break              ->  mira el tope de la pila
```

`micro/05_etiquetas.py` lo muestra con un árbol de juguete. Corranlo
antes de leer `visitar_While`.

### 10. El frame se reserva de una vez

En la semana de variables, cada `var` escribía su propio `sub sp, sp,
#16`. Funcionaba por una razón que no se veía: cada declaración se
ejecutaba exactamente **una** vez, en el orden en que aparecía.

Con saltos, eso deja de ser cierto. Dos programas cortos lo muestran:

```pascal
{ la variable `y` está en una rama que NO se toma }
program Cond;
begin
  var x: integer := 1;
  if x > 5 then begin
    var y: integer := 100;
    writeln(y);
  end;
  var z: integer := 42;
  writeln(z);
  writeln(x + z);
end.
```

```pascal
{ una declaración dentro de un ciclo largo }
program Fuga;
begin
  var i: integer := 0;
  while i < 3000000 do begin
    var t: integer := i;
    i := i + 1;
  end;
  writeln(i);
end.
```

Con un `sub sp` por declaración, el primero imprimía `42` y `2` (debía
ser `43`), y el segundo terminaba con `Segmentation fault`. Los dos
fallaban por la misma razón:

- **Una `var` en una rama no tomada** no ejecuta su `sub sp`, pero su
  offset ya se repartió al generar. La variable que sigue queda *por
  debajo* de `sp`, y el siguiente empujón de una expresión la pisa.
- **Una `var` en un ciclo** ejecuta su `sub sp` en cada vuelta, y nunca
  lo devuelve: tres millones de vueltas agotan el stack.

La solución es reservar el frame **completo** al entrar a la función, con
su tamaño final, y que cada `var` solo escriba en su celda. Pero el
tamaño final solo se conoce cuando el generador terminó de recorrer todo
el programa. Por eso la línea:

```asm
sub sp, sp, #32      // reservar el frame completo: 2 celdas de 16 bytes
```

se escribe en `ensamblar_archivo`, al final, y no en `visitar_Declaracion`.
Es el único cambio que tocó algo de la semana de variables, y está
explicado también al final de `arm/06_control_flujo.s`.

## Ejercicios de la parte 2

1. **Con papel.** Sigan `arm/06_control_flujo.s` y llenen una tabla:
   por cada vuelta del ciclo, cuánto valen `i` y `suma` al terminar. Las
   vueltas en las que `i` vale 3 y 6 son las interesantes: ¿qué salto
   se toma en cada una, y por qué `suma` no cambia?

2. **Romperlo a propósito.** En `generador_arm.py`, devuelvan a
   `visitar_Declaracion` su `self.emitir('sub sp, sp, #16', ...)` y
   quiten la línea `reserva` de `ensamblar_archivo`. Corran el programa
   `Cond` de la idea 10 con `--compilar`. Comprueben que imprime `2`, y
   expliquen con un dibujo del frame dónde quedó `z` respecto de `sp`.

3. **Tres desacuerdos entre los caminos.** Corran cada uno por los dos
   caminos y anoten qué imprime cada uno:

   ```pascal
   program A;  begin writeln(3 < 5); end.
   ```

   ```pascal
   program B;  begin if 5 + 3 then begin writeln(1); end; end.
   ```

   ```pascal
   program C;
   begin
     var i: integer := 0;
     while i < 100 do begin
       var a: array[2] of integer;   { ¿cuántos bloques reserva esto? }
       a[0] := i;
       i := i + 1;
     end;
     writeln(i);
   end.
   ```

   Los dos primeros se explican con el comentario `LO QUE FALTA AQUÍ`
   de `visitar_Comparacion` y `visitar_While`. El tercero, con lo que
   aprendieron en la parte 1: cada vuelta ejecuta un `bl alloc`.
   ¿Cuántas filas tiene la tabla y cuántas se usaron?

4. **`repeat ... until`.** Ahora mismo el generador responde "Todavía no
   sé qué hacer con: Repeat". Impleméntenlo en `generador_arm.py`. Pista: es
   un `while` con la condición **al final**, y el salto condicional
   vuelve al inicio si es falsa. Piensen adónde tiene que saltar un
   `continue` dentro de un `repeat`: no es la misma etiqueta que en un
   `while`. Pruébenlo con:

   ```pascal
   program R;
   begin
     var n: integer := 0;
     repeat
       n := n + 1;
     until n >= 3;
     writeln(n);          { 3 }
   end.
   ```

---

## Qué falta para tu proyecto

Todo lo de esta lista lo implementan **ustedes**. Que un mecanismo se
parezca a algo que hicimos en clase no lo resuelve: el ejemplo es
MiniPascal, va varios pasos atrás de OxigenNative, y traducirlo exige
entenderlo.

| Falta | Dónde lo pide el enunciado |
|---|---|
| Reservar y llevar la cuenta de bloques con los campos que **su** proyecto necesite (aquí solo hay base y tamaño) | 3.1.3 |
| `String` que crece: ¿qué pasa cuando el bloque ya no alcanza? | 3.3.11 |
| Arreglos multidimensionales en **un solo bloque** plano | 3.3.10 |
| Slices como un par (puntero, longitud) sobre un bloque que ya existe | 3.3.10 |
| Comprobar que un índice cae dentro del bloque | 3.3.10 |
| Soltar o reutilizar bloques que ya nadie usa | 3.1.3 |
| `&&` y `||` con corto circuito (saltos, no operaciones) | 3.3.7 |
| `match` / `case`: una cadena de `cmp` + `b.eq` | 3.3.8 |
| `loop` (ciclo sin condición) | 3.3.8 |
| `break` / `continue` con etiquetas de ciclo | 3.3.9 |
| Que una comparación se pueda guardar, pasar e imprimir como `bool` | 3.2.3 |
| Arreglos y variables de `f64`, `bool` o `char`: otro tamaño por celda | 3.2.3 |

Y huecos que se quedan abiertos a propósito (todos con un comentario
`LO QUE FALTA AQUÍ` en el código):

- `alloc` no comprueba que `brk` haya devuelto lo que se pidió. Si el
  kernel no puede dar la memoria, devuelve el break de antes sin avisar,
  y el programa seguiría escribiendo donde no debe.
- La tabla tiene 64 filas y nada revisa que no se pase.
- No hay verificación de límites en `a[i]` (ejercicio 3 de la parte 1).
- Una comparación deja 1 o 0, así que `writeln(3 < 5)` imprime `1`, no
  `true` (ejercicio 3 de la parte 2).
- La condición de un `if` o `while` no se revisa: cualquier valor
  distinto de cero cuenta como verdadero.
- `Repeat` y `Case` no están generados.
- Solo hay arreglos de `integer`, y `length` no está generado.
- Las variables de bloques anidados siguen compartiendo una sola tabla
  de offsets por programa (el hueco de shadowing de la semana de
  variables).

---

## Antes de irse

Dos cosas, las que más problemas evitan:

1. **Corran `./build.sh 04_brk.s` y comparen con la salida esperada**
   (`64`, `42`, `7`). Si imprime otra cosa, o si `build.sh` dice que le
   falta una herramienta, es mejor enterarse hoy. El toolchain es el
   mismo de la primera semana.
2. **Hagan el ejercicio 3 de la parte 1 y el 3 de la parte 2.** Los dos
   son el mismo tipo de bug: el programa corre, no falla, y el
   intérprete y el generador no están de acuerdo. Es la clase de error
   que más tiempo les va a quitar el día de la entrega.
