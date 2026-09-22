# Sesión 2 — Variables en el stack

Organización de Lenguajes y Compiladores 2 — Sección B · martes 22/09/2026
Material de apoyo para el Proyecto 2 (**OxigenNative**) · **Entrega: viernes 23/10/2026**

---

## El problema de hoy

La Sesión 1 generó `2 + 3 * 4` — una expresión que no necesitaba recordar
nada entre una instrucción y la siguiente. Hoy aparece esto:

```pascal
var a: integer := 10;
writeln(a);
a := a + 1;
writeln(a);
```

`a` tiene que sobrevivir entre la línea que la declara y la que la usa
tres líneas después. El intérprete resuelve esto con un diccionario en
memoria (`Entorno`, de la Sesión 2 del Proyecto 1). El generador no puede
usar un diccionario de Python: cuando el binario ARM64 corra, Python ya
terminó de correr hace rato. `a` tiene que vivir en algún lugar que siga
existiendo **dentro del binario**.

Ese lugar es el **stack frame**: una región de memoria que cada función
reserva para sí misma al entrar, y suelta al salir. Hoy solo hay una
función (`main`), así que el stack frame es del tamaño del programa
entero — pero el mecanismo es el mismo que van a usar en la Sesión 4 para
cada función que llamen.

Una pregunta para empezar, y es la que separa hoy de la Sesión 1:

> Cuando el generador ve `a`, ¿qué necesita saber — el VALOR de `a`, o la
> DIRECCIÓN donde `a` va a estar cuando el programa corra?

Es la segunda. El generador nunca sabe cuánto vale `a`. Ni falta que le
hace.

---

## Qué hay en esta carpeta

```
segundo-semetre-2026/
└── semana10/seccionB/
    ├── arm/
    │   ├── 01_hola.s, 02_aritmetica.s, build.sh   (Sesión 1, sin cambios)
    │   └── 03_variables.s      NUEVO — dos variables, a mano
    ├── micro/
    │   ├── 01_por_que_visitor.py, 02_visitor.py   (Sesión 1, sin cambios)
    │   └── 03_entorno_compilacion.py   NUEVO — nombre->offset vs nombre->valor
    └── minipascal/
        ├── generador_arm.py     CAMBIÓ — Declaracion, Asignacion, Variable
        ├── ejemplos/
        │   ├── 01_hola.mpas ... 10_aritmetica.mpas   (sin cambios)
        │   └── 11_variables.mpas   NUEVO
        └── el resto — lexer.py, parser.py, ast_nodes.py, interprete.py,
            entorno.py, valores.py, visitante.py, ensamblar.py, main.py —
            IDÉNTICO a semana9/seccionB. Compruébenlo:

              diff -r semana9/seccionB/minipascal semana10/seccionB/minipascal
```

`diff` va a mostrar exactamente un archivo cambiado (`generador_arm.py`)
y uno nuevo (`11_variables.mpas`). Ni `ast_nodes.py` ni `entorno.py` ni
`interprete.py` se tocaron. La razón es la misma de la Sesión 1: **el
generador es el único que aprendió algo nuevo hoy**, y el AST es el mismo
para los dos caminos.

---

## Cómo correrlo

```bash
cd semana10/seccionB
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 1. Ensamblador a mano — empiecen por aquí, es el destino de hoy
cd arm
./build.sh 03_variables.s    # 30

# 2. El entorno de compilación, aislado, sin PLY
cd ../micro
python3 03_entorno_compilacion.py

# 3. Los dos caminos sobre el mismo árbol
cd ../minipascal
python3 main.py            ejemplos/11_variables.mpas   # intérprete
python3 main.py --compilar ejemplos/11_variables.mpas   # ARM64 + QEMU
```

Las dos últimas líneas tienen que imprimir exactamente:

```
10
0
20
30
11
100
```

Y, como siempre, comprueben que nada de la Sesión 1 se rompió:

```bash
python3 main.py --compilar ejemplos/10_aritmetica.mpas
python3 main.py            ejemplos/09_slices.mpas
```

---

## Las ideas de hoy

### 1. Dos entornos, dos preguntas

```
EntornoDeEjecucion    (interprete.py, entorno.py)    nombre -> valor
EntornoDeCompilacion  (generador_arm.py, self.offsets) nombre -> offset
```

El primero contesta "¿cuánto vale `a` ahora mismo?" — y por eso solo
existe mientras el programa corre. El segundo contesta "¿en qué
dirección va a vivir `a`?" — y esa pregunta se responde leyendo el texto
del programa, **antes** de ejecutar ni una instrucción. `micro/03_entorno_compilacion.py`
corre el mismo programa por los dos caminos, uno al lado del otro.

Fíjense en el nombre del atributo en `generador_arm.py`: `self.offsets`,
no `self.entorno`. No es casualidad — es para que no se confundan ni
ustedes ni quien lea el código después.

### 2. Declarar reserva memoria; asignar la reutiliza

```python
def visitar_Declaracion(self, nodo):
    self.proximo_offset += 16
    offset = self.proximo_offset
    self.emitir('sub sp, sp, #16', ...)     # RESERVAR — pasa una vez
    self.offsets[nodo.nombre] = offset
    ...
    self.emitir(f'str x0, [x29, #-{offset}]', ...)   # llenar

def visitar_Asignacion(self, nodo):
    offset = self.offsets[nodo.nombre]      # ya existía, NO se reserva de nuevo
    ...
    self.emitir(f'str x0, [x29, #-{offset}]', ...)
```

`sub sp, sp, #16` solo aparece en `visitar_Declaracion`. Si lo ven
aparecer en una reasignación, algo está mal: cada `var` reserva su celda
una sola vez, y de ahí en adelante `nombre := expr` solo la reescribe.

### 3. `x29` no se mueve; `sp` sí — y por eso las direcciones no se
   despistan

En el prólogo, `x29` (el **frame pointer**) se fija una sola vez:

```asm
stp x29, x30, [sp, #-16]!
mov x29, sp
```

Después de esa línea, `x29` no vuelve a cambiar hasta el epílogo. Cada
`var` mueve `sp` (con `sub sp, sp, #16`) para reservar su celda, pero
todos los offsets de variables se miden **desde `x29`**, no desde `sp`.
Por eso `a` sigue siendo `[x29, #-16]` sin importar cuánto se haya movido
`sp` mientras tanto.

Y `sp` sí se mueve por otra razón, dentro de una expresión — la del
modelo de pila de la Sesión 1 (`str x0, [sp, #-16]!` / `ldr x0, [sp],
#16`). Las dos cosas conviven porque esos empujones de expresión siempre
son un préstamo que se devuelve en la misma instrucción: entran y salen
balanceados, así que cuando termina una expresión, `sp` vuelve exactamente
adonde estaba. `x29` nunca se entera de que pasaron por ahí.

```
      x29 ──────────────────────────►  fijo desde el prólogo
       │
       │  -16   a                       reservado UNA vez por 'var a'
       │  -32   b                       reservado UNA vez por 'var b'
       │
      sp ──┬───────────────────────►  baja con cada 'var'...
            │  temporal de expresión     ...y sube y baja aquí también,
            │  (entra y sale balanceado)  pero siempre vuelve a donde
            ▼                             estaba al terminar la expresión
```

Abran `arm/03_variables.s` y sigan la nota del final del archivo — ahí
está esta misma idea, aplicada a un ejemplo concreto, instrucción por
instrucción.

### 4. El epílogo necesitó una línea nueva

`02_aritmetica.s` (Sesión 1) restauraba `sp` así:

```asm
ldp x29, x30, [sp], #16
```

Eso asume que `sp` está exactamente donde quedó después del `stp` del
prólogo. Hoy ya no es cierto: cada `var` lo movió con `sub sp, sp, #16` y
nunca lo devolvió. Si el epílogo de hoy hiciera `ldp` directamente,
leería el par `(x29, x30)` de un lugar que ya no es el correcto — muy
probablemente de dos celdas de variables — y `ret` saltaría a cualquier
lado.

La solución es una línea, y es el patrón que van a repetir en cada
función a partir de la Sesión 4:

```asm
mov sp, x29              // devolver sp a donde x29 lo dejó en el prólogo
ldp x29, x30, [sp], #16  // AHORA sí lee lo que guardamos
```

No hace falta deshacer cada `sub sp` uno por uno — `mov sp, x29` los
suelta todos de un golpe, sin importar cuántas variables hubo.

### 5. Por qué 16 bytes por variable, no 8

Un `integer` en MiniPascal ocupa 8 bytes (el tamaño de un registro `x`).
Reservar 16 por variable, no 8, es la misma regla de alineación de la
Sesión 1: `sp` tiene que estar siempre alineado a 16 bytes en AArch64. Es
desperdicio a propósito — la mitad de cada celda de variable queda sin
usar — y el `//` que lo explica en `generador_arm.py` está ahí para que
no parezca un descuido.

Un compilador de verdad empaquetaría varias variables por celda de 16
bytes, o alinearía solo el frame completo en vez de cada variable por
separado. Eso es una optimización real y no cabe en este curso —
funcionar primero.

---

## Ejercicios

1. **Seguirlo a mano.** Abran `salida.s` que genera
   `ejemplos/11_variables.mpas` y, para cada `var`, anoten su nombre y su
   offset. Confirmen que ninguno se repite y que van de 16 en 16.

2. **Romperlo a propósito.** Corran esto con `--compilar`:

   ```pascal
   program Fantasma;
   begin
     writeln(y);
   end.
   ```

   Tiene que fallar con un mensaje que menciona "entorno de compilación".
   Ese es el mismo error semántico de "variable no declarada" que ya
   detecta `interprete.py` — pero hoy lo están viendo desde el otro lado:
   como una entrada que falta en un diccionario, no como una excepción de
   dominio.

3. **La regla de `x29` vs `sp`, puesta a prueba.** Escriban a mano, en
   `arm/`, un archivo `04_prueba.s` que declare tres variables, haga una
   expresión con paréntesis anidados que use varias de ellas (algo como
   `(a + b) * (a - b)`), y las imprima. Antes de correrlo, predigan en
   papel qué offset le va a tocar a cada variable y qué valor va a
   imprimir cada `writeln`. Después corran `./build.sh 04_prueba.s` y
   comparen.

4. **El hueco del shadowing.** Este programa:

   ```pascal
   program Sombra;
   begin
     var x: integer := 1;
     begin
       var x: integer := 2;
       writeln(x);
     end;
     writeln(x);
   end.
   ```

   Corran los dos caminos y comparen. El intérprete distingue las dos `x`
   porque cada `begin...end` abre un `Entorno` nuevo, con su propio
   padre. El generador de hoy no — `self.offsets` es uno solo para todo
   el programa, así que la segunda declaración de `x` **pisa** la entrada
   de la primera en el diccionario. Expliquen, mirando `visitar_Bloque`,
   por qué pasa eso y qué le faltaría para no pasar. (No hace falta
   arreglarlo: es la lista de "Qué falta para tu proyecto".)

---

## Qué falta para tu proyecto

Como siempre: nada de esto lo resuelve el ejemplo por ustedes. MiniPascal
sigue varios pasos atrás de OxigenNative y sus nombres de nodo no
calzan con los suyos.

| Falta | Dónde lo pide el enunciado |
|---|---|
| Ámbito real: que un `begin...end` anidado (o una función) no pise offsets de afuera | 3.1.3, 3.3.2 |
| `mut` / shadowing de verdad, distinguiendo dos variables con el mismo nombre | 3.3.2, 3.3.3 |
| `bool` en registros (hoy solo hay `integer`) | 3.2.3 |
| `f64` completo: registros `d0`–`d31`, `scvtf`, `%f` | 3.2.3 |
| Control de flujo: `if`, `while`, `loop`, `match` | 3.3.8 |
| Funciones: parámetros, convención de llamadas, cada una con SU PROPIO stack frame | 3.3.12 |
| Arreglos y structs: offsets calculados, no uno por nombre | 3.3.10, 3.3.12 |

Y de hoy, huecos que se quedan abiertos a propósito (todos con un
comentario `LO QUE FALTA AQUÍ` en `generador_arm.py`):

- Una sola tabla de offsets para todo el programa — el ejercicio 4 de
  arriba es justo este hueco.
- `const` se reserva y se llena exactamente igual que `var`: nada en el
  generador impide reasignarla.
- Sigue habiendo solo `integer`: `real`, `boolean` y `string` en una
  declaración caen en el mismo mensaje de `visitar_Literal` de la Sesión
  1.
- La división entera de la Sesión 1 sigue sin coincidir con la de Python
  (ejercicio 3 del README de `semana8/seccionB`, todavía pendiente si no
  lo resolvieron).

---

## Antes de irse

Nos vemos el martes 29 de septiembre. Si algo de `arm/03_variables.s` no
les quedó claro, es más fácil de seguir con papel y lápiz, offset por
offset, que leyéndolo de corrido — el ejercicio 1 de arriba está pensado
exactamente para eso.
