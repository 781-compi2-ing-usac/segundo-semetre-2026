# El heap con `brk` y una tabla de bloques

Organización de Lenguajes y Compiladores 2 — Sección B · martes 13/10/2026
Material de apoyo para el Proyecto 2 (**OxigenNative**) · **Entrega: viernes 23/10/2026**

---

## El problema de hoy

Hasta ahora, toda la memoria de sus programas vivía en el **stack**:
cada variable tiene su celda en el frame, y todo se suelta junto cuando
termina la función. Eso funciona mientras el compilador sepa, al
generar el código, cuánta memoria hace falta y cuánto va a durar.

El enunciado (sección 3.1.3) pide además un **heap**: memoria que el
programa le pide al sistema operativo mientras corre, para "cadenas y
arreglos de tamaño dinámico". Y dice que el modelo de memoria es
**explícito**: no vale llamar a `malloc` y olvidarse. Hay que construir
la reserva y llevar la cuenta de lo reservado.

La pregunta de hoy:

> Una variable ya sabe vivir en una celda del stack. ¿Cómo hace una
> celda de 16 bytes para "tener" un arreglo de 1000 enteros?

Respuesta corta: **no lo tiene. Guarda la dirección de dónde está.**

---

## Qué hay en esta carpeta

```
segundo-semetre-2026/
└── semana12/seccionB/
    ├── arm/
    │   ├── 01_hola.s … 03_variables.s, build.sh   (sin cambios)
    │   ├── 04_brk.s            NUEVO — pedirle memoria al kernel
    │   └── 05_alloc_tabla.s    NUEVO — una rutina alloc y su tabla
    ├── micro/
    │   ├── 01 … 03             (sin cambios)
    │   └── 04_heap_modelo.py   NUEVO — el heap modelado en Python
    └── minipascal/
        ├── generador_arm.py    CAMBIÓ — arreglos en el heap
        ├── ejemplos/12_heap.mpas   NUEVO
        └── el resto — lexer, parser, ast_nodes, interprete, ... — sin cambios
```

Compruébenlo, igual que siempre:

```bash
diff -r semana10/seccionB semana12/seccionB
```

Tiene que mostrar: este `README.md`, `04_brk.s`, `05_alloc_tabla.s`,
`04_heap_modelo.py`, `12_heap.mpas` y un solo archivo de código
cambiado, `generador_arm.py` (más dos retoques menores en `.gitignore`
y `requirements.txt`). Ni el AST ni el intérprete se tocaron: **el
generador es el único que aprendió algo nuevo.**

---

## Cómo correrlo

```bash
cd semana12/seccionB
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 1. Ensamblador a mano — empiecen por aquí
cd arm
./build.sh 04_brk.s            # 64, 42, 7
./build.sh 05_alloc_tabla.s    # 50, 5, 2, 32, 16, 32

# 2. El modelo, sin ensamblador
cd ../micro
python3 04_heap_modelo.py

# 3. Los dos caminos sobre el mismo árbol
cd ../minipascal
python3 main.py            ejemplos/12_heap.mpas   # intérprete
python3 main.py --compilar ejemplos/12_heap.mpas   # ARM64 + QEMU
```

Las dos últimas líneas tienen que imprimir exactamente:

```
50
5
0
25
```

Y, como siempre, comprueben que nada de lo anterior se rompió:

```bash
python3 main.py --compilar ejemplos/10_aritmetica.mpas
python3 main.py --compilar ejemplos/11_variables.mpas
```

---

## Las ideas de hoy

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
offset desde `x29`, exactamente igual que en la sesión de variables. Lo
único distinto es lo que se escribe en esa celda:

```
 STACK (el frame)                      HEAP (lo que pidió brk)
┌──────────────────┐                  ┌───┬───┬───┬───┐
│ [x29,#-16]  a ───┼─────────────────►│ 0 │ 0 │ 0 │ 0 │   32 bytes
├──────────────────┤                  ├───┼───┘   ...
│ [x29,#-32]  b ───┼───────┐          │
└──────────────────┘       └─────────►│ 0 │ 0 │             16 bytes
                                      └───┴───┘
```

Leer `a[3]` pasa a ser **dos** lecturas, y no una:

```asm
ldr x1, [x29, #-16]     // 1. traer el PUNTERO, desde el stack
ldr x0, [x1, #24]       // 2. traer el VALOR, desde el heap  (3 * 8 = 24)
```

Es la única novedad de la sesión a nivel de instrucciones. Todo lo demás
es contabilidad.

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
base de `b`, o sea que **un bloque empieza exactamente donde termina el
anterior**. Esa observación vale oro en el ejercicio 3.

### 4. Copiar una variable copia la dirección

`micro/04_heap_modelo.py` modela el heap con objetos de Python. Lo
importante está al final: después de `b := a`, las dos celdas apuntan
al mismo bloque, y escribir por una cambia lo que lee la otra. Y el
bloque que `b` tenía antes sigue en la tabla, sin dueño.

Si el lenguaje de ustedes quiere que `b := a` **copie los datos**,
alguien tiene que pedir un bloque nuevo y copiar elemento por elemento.
Ese "alguien" es el compilador, y las instrucciones que hacen la copia
las tienen que generar ustedes.

### 5. El heap arranca en ceros, y no es casualidad

Un arreglo de `integer` recién declarado vale 0 en todas sus casillas,
y el generador no escribe ninguna instrucción para eso. Es el kernel:
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
  intercaladas con 2000 impresiones: ninguna celda alterada. `printf`
  pide un solo buffer y listo.
- Nuestro `alloc` mezclado con llamadas a `malloc`/`free` de la
  biblioteca de C: **más de la mitad de las celdas aparecieron
  alteradas**, sin ningún error. Los dos administradores se repartieron
  las mismas direcciones.

Regla para todo el proyecto: **o es el `alloc` de ustedes, o es el de
la biblioteca. Nunca los dos.** Por eso este generador usa de libc solo
`printf`, y por eso no aparece `malloc` en ningún archivo de hoy.

---

## Ejercicios

1. **Seguirlo con papel.** Abran `arm/05_alloc_tabla.s` y dibujen, línea
   por línea, tres cosas: el frame, el break del heap y la tabla.
   Anoten cuánto vale cada una después de cada `bl alloc`.

2. **Una fila más.** Agreguen a mano, en una copia de
   `05_alloc_tabla.s` llamada `06_prueba.s`, un tercer arreglo
   `c: array[3] of integer`. Antes de correrlo, predigan: ¿cuánto vale
   `tabla_n`? ¿En qué offset del frame queda `c`? ¿A qué distancia de la
   base de `b` queda la base de `c`? Después corran `./build.sh
   06_prueba.s` y comparen.

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
   intérprete y generador en desacuerdo, y es uno de los más
   peligrosos: el programa "funciona".

4. **Ver la tabla desde MiniPascal.** El programa generado tiene una
   tabla, pero nunca la imprime. Agreguen al final de `ensamblar_archivo`
   (antes del epílogo) las instrucciones que impriman cuántas filas hay,
   usando como modelo lo que hace `05_alloc_tabla.s`. Ojo: el intérprete
   no sabe nada de esa tabla, así que la salida de los dos caminos
   **dejará de coincidir**. Decidan si eso es un problema o si esa
   salida debería ir por otro lado.

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
| Arreglos de `f64`, `bool` o `char`: otro tamaño por casilla | 3.2.3 |
| Soltar o reutilizar bloques que ya nadie usa | 3.1.3 |

Y de hoy, huecos que se quedan abiertos a propósito (todos con un
comentario `LO QUE FALTA AQUÍ` en el código):

- `alloc` no comprueba que `brk` haya devuelto lo que se pidió. Si el
  kernel no puede dar la memoria, devuelve el break de antes sin
  avisar, y el programa seguiría escribiendo donde no debe.
- La tabla tiene 64 filas y nada revisa que no se pase.
- No hay verificación de límites en `a[i]` (ejercicio 3).
- Solo hay arreglos de `integer`.
- `length` no está generado.

---

## Antes de irse

Una sola cosa: **corran `./build.sh 04_brk.s` y comparen con la salida
esperada** (`64`, `42`, `7`). Si les imprime otra cosa, o si
`build.sh` dice que le falta una herramienta, es mejor enterarse hoy. El
toolchain es el mismo de la primera semana.
