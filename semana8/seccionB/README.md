# Sesión 1 — El patrón Visitor y el primer binario ARM64

Organización de Lenguajes y Compiladores 2 — Sección B · martes 08/09/2026
Material de apoyo para el Proyecto 2 (**OxigenNative**) · **Entrega: viernes 23/10/2026**

---

## El problema de hoy

Su intérprete del Proyecto 1 funciona. Ahora el enunciado pide algo más:
a partir del mismo árbol, **generar ensamblador ARM64**, ensamblarlo,
enlazarlo y ejecutarlo con QEMU.

Y ejecutar sigue haciendo falta: los reportes lo usan, y es la forma más
rápida de comprobar si lo que generaron está bien.

Dos preguntas para empezar:

- Su AST tiene ~30 clases y cada una lleva su `evaluar()` adentro. Ahora
  necesita también `generar()`, y muy probablemente `verificar_tipos()`.
  ¿Le agregan dos métodos a cada una de las 30 clases? ¿Qué pasa con ese
  archivo a las 90 funciones?
- Cuando su compilador vea `2 + 3 * 4`, **no puede calcular 14**. Tiene
  que escribir instrucciones para que un procesador lo calcule después.
  ¿Qué significa exactamente "no puede calcular"? ¿Dónde se guarda un
  resultado intermedio si todavía no existe ningún resultado?

La segunda es la que conviene entender antes de programar. Es la
diferencia entre los dos proyectos, en una frase:

> **Un intérprete calcula el resultado. Un compilador escribe las
> instrucciones para que otro lo calcule más tarde.**

---

## Qué hay en esta carpeta

```
segundo-semetre-2026/
└── semana8/seccionB/
    ├── arm/                 NUEVO — ensamblador a mano, para LEER
    │   ├── 01_hola.s        .data, adrp/:lo12:, y la syscall write
    │   ├── 02_aritmetica.s  2 + 3 * 4 con printf — el destino del generador
    │   └── build.sh         ensambla, enlaza y ejecuta
    ├── micro/
    │   ├── 01_por_que_visitor.py   el dolor: 30 clases x 3 recorridos
    │   └── 02_visitor.py           la salida: cortar por columnas
    └── minipascal/
        ├── ast_nodes.py         CAMBIÓ — nodos sin lógica, solo aceptar()
        ├── valores.py           NUEVO — lo que existe en tiempo de EJECUCIÓN
        ├── visitante.py         NUEVO — la interfaz, con sus 30 metodos
        ├── interprete.py        NUEVO — el intérprete de siempre, ahora visitante
        ├── generador_arm.py     NUEVO — el backend ARM64
        ├── ensamblar.py         NUEVO — gcc + QEMU
        ├── main.py              CAMBIÓ — ahora hay bandera --compilar
        ├── dot.py               una línea: `formatear` se mudó a valores.py
        ├── lexer.py, parser.py, entorno.py, errores.py,
        │   tabla_simbolos.py, senales.py, reportes.py   (sin cambios)
        └── ejemplos/
            ├── 01_hola.mpas ... 09_slices.mpas   (Proyecto 1, siguen igual)
            └── 10_aritmetica.mpas   NUEVO — el que recorre toda la cadena
```

Que `lexer.py` y `parser.py` no hayan cambiado **ni una línea** no es
casualidad: es la noticia de la semana. **Todo lo nuevo del Proyecto 2
pasa a la derecha del AST.**

De los ocho archivos que venían del Proyecto 1, siete quedaron idénticos.
El único que se tocó fue `dot.py`, y solo su línea de `import`, porque
`formatear` se mudó a `valores.py`. Compruébenlo ustedes:

```bash
diff -r semana6/seccionB/minipascal semana8/seccionB/minipascal
```

## Instalar el toolchain

Hacen falta dos cosas: un **ensamblador cruzado** (corre en su máquina,
produce código ARM64) y **QEMU en modo usuario** (ejecuta ese código).

Háganlo hoy. Es lo único de todo el proyecto que no se puede resolver a
última hora.

### Ubuntu, Debian o WSL

```bash
sudo apt update
sudo apt install binutils-aarch64-linux-gnu gcc-aarch64-linux-gnu qemu-user
```

> **Ojo con esto**, es el error más común: el paquete se llama
> `qemu-user`, **no** `qemu-user-static`. El segundo ya no existe en las
> versiones recientes de Ubuntu y `apt` responde "no hay candidato".

Comprobación:

```bash
cd semana8/seccionB/arm
./build.sh 01_hola.s      # debe imprimir: Hola desde ARM64
```

### Mac con chip M1, M2 o M3

Su procesador **ya es ARM64**: no necesitan QEMU ni compilador cruzado.
Usen las herramientas nativas y corran el binario directo.

```bash
clang 02_aritmetica.s -o 02_aritmetica
./02_aritmetica
```

Dos diferencias con Linux que los van a morder:

- macOS antepone un guión bajo a los símbolos: es `_main`, no `main`, y
  `_printf`, no `printf`.
- Los argumentos variádicos de `printf` van **en la pila**, no en los
  registros. En Linux van en `x1`–`x7`. Es una diferencia real de ABI, no
  un detalle.

Por eso, si su máquina es una Mac ARM, **conviene igual trabajar dentro de
Docker o de una VM Linux**: su proyecto se va a calificar en Linux, y
estas dos diferencias hacen que un `.s` que corre en macOS no corra allá.

`--platform linux/arm64` es la clave: el contenedor entero es ARM64, así
que adentro `gcc` es nativo y no hace falta ni compilador cruzado ni
invocar QEMU a mano.

### Si nada les funciona

Búsquenme esta semana, no la de la entrega. Sin toolchain no hay
Proyecto 2.

---

## Cómo correrlo

Con el toolchain ya instalado:

```bash
cd semana8/seccionB
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 1. Ensamblador a mano — empiecen por aquí
cd arm
./build.sh 01_hola.s          # Hola desde ARM64
./build.sh 02_aritmetica.s    # 14

# 2. El patrón, aislado
cd ../micro
python 01_por_que_visitor.py
python 02_visitor.py

# 3. Los dos caminos sobre el mismo árbol
cd ../minipascal
python main.py            ejemplos/10_aritmetica.mpas   # intérprete
python main.py --compilar ejemplos/10_aritmetica.mpas   # ARM64 + QEMU
```

Las dos últimas líneas tienen que imprimir **exactamente los mismos
números**. Uno lo calcula Python en su máquina; el otro lo calcula un
procesador ARM64 emulado, ejecutando instrucciones que escribió su
compilador.

Y comprueben que el intérprete no se rompió:

```bash
python main.py ejemplos/06_funciones.mpas
python main.py ejemplos/09_slices.mpas
```

Misma salida que en `semana6/seccionB`. Ese es el criterio de que el
refactor salió bien.

---

## Las ideas de hoy

### 1. El problema no es el patrón, es la tabla

Tienen 30 clases de nodo y van a tener 3 recorridos. Eso es una tabla de
30 × 3 métodos, y la única pregunta es por cuál eje se corta:

```
                evaluar    generar    verificar_tipos
   Literal         .          .              .
   Aritmetica      .          .              .
   While           .          .              .
   ...
                 ^^^^
        el Proyecto 1 cortaba por FILAS (todo lo de While junto)
        el Proyecto 2 necesita cortar por COLUMNAS
```

Cortar por filas es el patrón Intérprete: cada clase se lleva sus tres
métodos. Cortar por columnas es el patrón Visitor: cada recorrido se
lleva sus 30 métodos, en su propio archivo.

Corran `micro/01_por_que_visitor.py` antes de seguir. Está escrito para
que el problema se sienta, no para que se lea.

### 2. `aceptar` es una línea, y es doble despacho

```python
class Literal(Expresion):
    def aceptar(self, v):
        return v.visitar_Literal(self)
```

Eso es todo lo que hay en cada nodo. La pregunta razonable es por qué no
se escribe `v.visitar(self)` y que el visitante averigüe el tipo.

Porque escribir `visitar_Literal` **dentro de** `Literal` deja el nombre
del método resuelto sin ningún `if` ni ningún `isinstance`. La clase ya
se conoce a sí misma. A eso se le llama **doble despacho**:

```
1. nodo.aceptar(visitante)   ->  el primer despacho elige el NODO
2. v.visitar_Literal(nodo)   ->  el segundo despacho elige el VISITANTE
```

Dos decisiones, una por eje de la tabla. Por eso se pueden agregar
visitantes sin tocar nodos.

### 3. El precio: agregar nodos se vuelve más caro

Esto también hay que decirlo, porque si no el patrón parece gratis y no
lo es.

```
agregar un RECORRIDO   ->  un archivo nuevo, cero cambios en los nodos
agregar un NODO        ->  la clase nueva Y todos los visitantes
```

El Visitor no es "mejor". Es un intercambio, y conviene cuando uno agrega
recorridos seguido y nodos casi nunca — que es exactamente su situación:
la gramática ya está fija en el enunciado, y recorridos van a necesitar
dos o tres.

Si su proyecto fuera al revés, el patrón del Proyecto 1 sería la mejor
opción. Elegir un patrón es elegir **qué cambio quieren que sea barato**.

### 4. Un nodo no debe recordar nada de haberse ejecutado

Al refactorizar apareció un detalle que en el Proyecto 1 pasaba
desapercibido. El nodo `Funcion` guardaba esto:

```python
self.entorno_definicion = None   # lo llena ejecutar()
```

Con un solo recorrido no molestaba. Con dos, sí: el generador va a
recorrer el mismo árbol, y un nodo que guarda resultados de la ejecución
anterior ya no describe el programa — describe una ejecución.

Ahora el nodo volvió a ser datos puros, y el intérprete guarda un
`FuncionValor` (declaración + entorno) en el entorno. Es la misma idea de
un cierre en Python o JavaScript. Está en `valores.py`.

> **Regla para todo el Proyecto 2:** un nodo del AST nunca debe guardar
> nada que dependa de haberse ejecutado.

### 5. Compilación y ejecución son dos momentos distintos

Por eso `valores.py` existe. Hasta la Sesión 5 del Proyecto 1, los nodos
y los valores vivían juntos en `ast_nodes.py` y nadie extrañaba la
separación. Ahora sí:

```
ast_nodes.py  ->  lo que existe en tiempo de COMPILACIÓN   (la forma)
valores.py    ->  lo que existe en tiempo de EJECUCIÓN     (los datos)
```

`interprete.py` importa `valores.py` entero. `generador_arm.py` **no
importa nada de ahí**, y no es un descuido: cuando se genera código, el
programa todavía no corrió. No hay ningún valor en ningún lado. Solo hay
forma.

Si esa distinción les queda clara hoy, se ahorran la confusión más común
del proyecto: intentar calcular cosas mientras generan código.

### 6. Cómo se imprime en ARM64, de verdad

En Linux, lo único que hace aparecer texto en pantalla es pedírselo al
kernel con la syscall `write`. Se ponen los argumentos en registros y se
ejecuta `svc #0`. Eso es `arm/01_hola.s`, y son seis instrucciones:

```asm
mov x0, #1                  // fd = 1, stdout
adrp x1, mensaje            // dirección de la página...
add  x1, x1, :lo12:mensaje  // ...más el desplazamiento dentro de ella
mov x2, #longitud           // cuántos bytes
mov x8, #64                 // 64 = write
svc #0                      // pedírselo al kernel
```

Ese par `adrp`/`add :lo12:` les va a aparecer en toda dirección que
carguen — también en el código que genera MiniPascal. Van dos
instrucciones porque en ARM64 toda instrucción mide 4 bytes y una
dirección de 64 bits no cabe adentro de ninguna.

**Pero `write` solo escribe bytes que ya existen.** Para imprimir el
número 14 hay que fabricar antes los caracteres `'1'` y `'4'`: dividir
entre 10 en un bucle, sumarle 48 a cada resto, guardarlos al revés en un
buffer. Unas 20 líneas.

Por eso, a partir del generador, nos enlazamos con la biblioteca de C y
usamos `printf`, que ya trae eso hecho:

```asm
mov x1, x0                  // PRIMERO el valor a x1...
adrp x0, fmt_entero         // ...y DESPUÉS el formato a x0
add  x0, x0, :lo12:fmt_entero
bl printf
```

No es hacer trampa: el enunciado dice que el enlace sirve para
"combinarlo con los recursos necesarios", y todo compilador de verdad
enlaza con una biblioteca de runtime — `rustc` y `gcc` incluidos. Y
cuando lleguen a `f64`, escribir un formateador de flotantes a mano deja
de ser incómodo y pasa a ser un muro.

Invertir esas dos líneas es un error clásico y **silencioso**: no falla,
imprime basura. Si su compilador imprime números sin sentido, revisen ese
orden antes que nada.

### 7. El modelo de pila, y por qué no usamos registros

Una sola regla, y con ella se generan expresiones de cualquier tamaño:

> **Toda expresión deja su resultado en `x0`.**

Con eso, una operación binaria se arma sola:

```asm
    mov x0, #2            // izquierdo         x0=2
    str x0, [sp, #-16]!   // empujarlo         pila: [2]
    mov x0, #3            // derecho...        x0=3
    str x0, [sp, #-16]!   //                   pila: [2, 3]
    mov x0, #4            //                   x0=4
    mov x1, x0            // el derecho a x1   x1=4
    ldr x0, [sp], #16     // recuperar         x0=3  pila: [2]
    mul x0, x0, x1        //                   x0=12
    mov x1, x0            //                   x1=12
    ldr x0, [sp], #16     //                   x0=2  pila: []
    add x0, x0, x1        //                   x0=14
```

El paso que suele costar es el `str`: **¿por qué guardar el izquierdo si
ya está en x0?** Porque generar el operando derecho puede ser una
expresión enorme, con sus propias operaciones anidadas, que va a usar x0
mil veces. El izquierdo se perdería. La pila es lo único que sobrevive a
eso.

Los empujones son de 16 bytes aunque un entero ocupe 8, porque AArch64
exige que `sp` esté alineado a 16 siempre. Con `sp` desalineado, `printf`
revienta sin explicar por qué.

¿Es eficiente? No. Un compilador de verdad haría **asignación de
registros** y usaría `x0`–`x7` en vez de tocar memoria a cada paso. Pero
eso es un algoritmo de coloreo de grafos y no cabe en este curso. El
modelo de pila tiene la propiedad que sí nos importa: **funciona para
cualquier anidamiento sin cambiar nada**. Empiecen aquí. Optimizar es
opcional; funcionar no.

---

## Ejercicios

1. **Un recorrido nuevo, sin tocar los nodos.** Escriban un visitante
   `ContadorDeNodos` que devuelva cuántos nodos tiene el AST. Cuando
   terminen, comprueben con `git diff` que `ast_nodes.py` quedó intacto.
   Si lo tuvieron que tocar, algo se salió del patrón.

2. **El menos unario, a mano.** Abran `salida.s` para
   `writeln(-7 + 10);` y sigan las instrucciones con papel, registro por
   registro. Después háganlo al revés: escriban a mano el ensamblador de
   `writeln((8 - 3) * 2);` y córranlo con `arm/build.sh`. Comparen con lo
   que genera el compilador.

3. **El bug de la división.** Corran esto por los dos caminos:

   ```pascal
   program Division;
   begin
     writeln(7 / 2);
   end.
   ```

   El intérprete imprime `3.5` y el generador `3`. Los dos "funcionan" y
   dan resultados distintos: `sdiv` es división entera y el `/` de Python
   no. Esta familia de bugs —el intérprete y el generador en desacuerdo—
   es la más difícil de encontrar en el Proyecto 2, porque nada falla.

   Decidan qué debería pasar y arréglenlo. Hay dos respuestas defendibles
   y ninguna es obviamente mejor; elijan una y sepan por qué.

4. **Un nodo nuevo, para sentir el precio.** Agreguen `mod` (el módulo) a
   MiniPascal: lexer, parser, nodo, y los dos visitantes. En ARM64 no hay
   instrucción de módulo — se arma con `sdiv` y `msub`, búsquenlo. Cuenten
   cuántos archivos tuvieron que tocar y compárenlo con el ejercicio 1.
   Esa diferencia **es** el intercambio del que habla la idea 3.

---

## Qué falta para tu proyecto

Todo lo de esta lista lo implementan **ustedes**. Que algún mecanismo se
parezca a algo que veamos en clase no cambia eso: el ejemplo va a estar
siempre en MiniPascal y varios pasos atrás de OxigenNative, así que
traducirlo es trabajo suyo, y traducirlo exige entenderlo.

El orden en que aparecen es una sugerencia razonable de por dónde
empezar, no un cronograma. **Nada de esto conviene dejarlo para después.**

| Falta | Dónde lo pide el enunciado |
|---|---|
| Variables: reservar y usar espacio en el stack frame | 3.1.3 |
| `bool` y `char` en registros | 3.2.3 |
| `f64` completo: registros `d0`–`d31`, `scvtf`, `%f` | 3.2.3 |
| Control de flujo: `if`, `while`, `loop`, `match` | 3.3.8 |
| `&&` y `\|\|` con corto circuito | 3.3.7 |
| `break`/`continue` con etiquetas | 3.3.9 |
| Funciones, convención de llamadas, `return` | 3.3.12 |
| Arreglos, aplanamiento row-major, slices | 3.3.10 |
| Arreglos multidimensionales de N dimensiones | 3.3.10 |
| Justificar row-major vs column-major en el manual técnico | 3.3.10 |
| Structs y sus campos en memoria | 3.3.12 |
| `String`, escapes, raw strings, métodos | 3.3.11 |
| Funciones embebidas (`typeof`, `random`, `len`, ...) | 3.3.13 |
| Mutabilidad (`mut`), shadowing, inferencia de tipos | 3.3.2, 3.3.3 |
| Matriz completa de promoción de tipos | 3.3.5, 3.3.6 |
| Reportes: errores, tabla de símbolos, AST | 3.5 |
| GUI completa con panel de ARM64 y consola | 3.1.2 |

Y de hoy, huecos que se quedan abiertos a propósito:

- El generador solo maneja **enteros**. Un literal `real` o `string` da un
  mensaje de "todavía no sé generar esto", que es la lista de tareas.
- La división no coincide entre los dos caminos (ejercicio 3).
- Sigue sin haber tabla de tipos para `-`, `*`, `/` ni para los operadores
  relacionales salvo `<` — huecos heredados de las Sesiones 2 y 3 del
  Proyecto 1.
- `p_error` sigue sin recuperación de errores sintácticos.

Todos tienen un comentario `LO QUE FALTA AQUÍ` en el código.

---

## Antes de irse

Una sola cosa, y es la que más problemas evita: **comprueben hoy que su
toolchain funciona**. Si `./build.sh 01_hola.s` no imprime nada en su
máquina, resuélvanlo esta semana, no la del 20 de octubre. Todo lo demás
del proyecto se puede empujar; esto no.
