# Sesión 4 — Funciones, entornos de activación y arreglos

Organización de Lenguajes y Compiladores 2 — Sección B · martes 18/08/2026
Material de apoyo para el Proyecto 1 (**OxigenScript**)

---

## El problema de hoy

Hasta la Sesión 3, todo lo que declaraban vivía en el mismo `Entorno`, uno
colgado del otro: el programa, y adentro sus bloques anidados (`if`,
`while`...). Esta semana aparece algo distinto: una función se **declara**
en un lugar del código, pero se **ejecuta** en otro completamente
distinto, quizás muchas veces, quizás desde adentro de sí misma.

Eso rompe la pregunta que hasta ahora resolvían solo con "sube por la
cadena de padres": cuando el cuerpo de una función se ejecuta, ¿de qué
entorno debe colgar su propio entorno? La respuesta parece obvia hasta que
se piensa dos veces — y si se contesta mal, el intérprete sigue corriendo
igual, solo que da resultados incorrectos en casos específicos de
anidamiento. Ningún error los va a avisar.

La segunda pregunta nueva: `return` necesita el mismo truco de excepción
que `break`/`continue` (Sesión 3), pero además la llamada a función tiene
que comportarse como un límite de pila completo — igual que
`Programa.ejecutar` ya lo era desde la semana pasada.

---

## Qué hay en esta carpeta

```
segundo-semetre-2026/
└── semana5/seccionB/
    ├── requirements.txt
    ├── micro/
    │   ├── 01_entornos_activacion.py   de dónde cuelga el entorno de una llamada
    │   └── 02_limite_de_funcion.py     la llamada como límite de pila (return Y break perdido)
    └── minipascal/
        ├── lexer.py           + FUNCTION/RETURN/ARRAY, COMA, CORCHETEIZQ/CORCHETEDER
        ├── senales.py         + SenalReturn
        ├── entorno.py         + `ambito` (ya no todo es 'programa')
        ├── ast_nodes.py       + Parametro, Funcion, Llamada, Return,
        │                        DeclaracionArreglo, Indexado, AsignacionIndexada
        ├── parser.py          + gramática de funciones, return y arreglos
        ├── errores.py, tabla_simbolos.py, dot.py, main.py   (sin cambios)
        └── ejemplos/
            ├── 01_hola.mpas ... 05_control_flujo.mpas   (Sesiones 1-3, siguen igual)
            ├── 06_funciones.mpas    NUEVO — funciones, recursión, declaración previa
            └── 07_arreglos.mpas     NUEVO — arreglos, índices, paso por valor
```

## Cómo correrlo

```bash
cd semana5/seccionB
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 micro/01_entornos_activacion.py
python3 micro/02_limite_de_funcion.py

cd minipascal
python3 main.py ejemplos/06_funciones.mpas
python3 main.py ejemplos/07_arreglos.mpas

# cada archivo corre solo, para probar una pieza a la vez:
python3 entorno.py
python3 parser.py     # lexer + parser + una función chiquita de ejemplo
```

---

## Las ideas de hoy

### 1. El entorno de activación cuelga de donde la función fue DECLARADA, no de quien la llama

`micro/01_entornos_activacion.py` construye, a propósito, las dos
versiones — la correcta y la que tiene el bug — para que se vea la
diferencia:

```python
def llamar(funcion, argumentos):
    activacion = Entorno(padre=funcion.entorno_definicion)   # CORRECTO
    ...

def llamar_con_el_bug(funcion, argumentos, entorno_de_quien_llama):
    activacion = Entorno(padre=entorno_de_quien_llama)       # BUG
    ...
```

`funcion.entorno_definicion` se guarda una sola vez, en el momento en que
`Funcion.ejecutar` declara la función:

```python
class Funcion(Instruccion):
    def ejecutar(self, entorno, errores, tabla):
        self.entorno_definicion = entorno
        entorno.declarar(self.nombre, self, tipo='function', constante=True)
```

Y `Llamada.evaluar` lo usa así:

```python
entorno_activacion = Entorno(padre=funcion.entorno_definicion, ambito=self.nombre)
```

Esto es, literalmente, lo mismo que un **cierre (closure)** en Python o
JavaScript: la función "se lleva consigo" el entorno donde nació. Es lo
que produce **scoping estático** (el que usa Rust/OxigenScript) en vez de
**scoping dinámico** (el bug). Corran `ejemplos/06_funciones.mpas`,
sección 3 (`quienLlama`/`leerVersion`), y comparen: da `100`, la variable
global, no `999`, la local de quien llamó.

Una nota honesta: la primera versión de este ejemplo intentó resolver
esto con un método `Entorno.raiz()` (subir hasta el entorno sin padre) en
vez de guardar `entorno_definicion`. Se rompía con `factorial` llamándose
a sí misma — porque las declaraciones del bloque principal del programa
viven un nivel POR DEBAJO del entorno raíz real (`Bloque.ejecutar` siempre
abre su propio ámbito, incluso para el bloque más externo), así que
`raiz()` apuntaba a un entorno vacío. Queda como recordatorio de que
"buscar el entorno global subiendo la cadena" y "buscar el entorno donde
algo fue declarado" NO son la misma pregunta, aunque en un lenguaje sin
funciones anidadas casi siempre den la misma respuesta.

### 2. La llamada a función es un límite de pila, igual que `Programa`

`Return` no "hace" nada por sí sola, solo lanza `SenalReturn` — el mismo
patrón exacto de `Break`/`Continue` desde la Sesión 3:

```python
class Return(Instruccion):
    def ejecutar(self, entorno, errores, tabla):
        valor = self.expresion.evaluar(entorno, errores, tabla)
        raise SenalReturn(valor, self.linea, self.columna)
```

`Llamada.evaluar` es quien la atrapa. Pero además tiene que atrapar
`SenalBreak`/`SenalContinue`, por si alguien escribió un `break` DENTRO de
una función sin ningún ciclo que lo contenga — sin eso, la señal se
escapa de la llamada y sigue subiendo hasta el primer `while` que
encuentre, que puede ser el de QUIEN LLAMÓ a la función. `ejemplos/
06_funciones.mpas` (sección 5, `romperMal`) y
`micro/02_limite_de_funcion.py` muestran exactamente ese escape y cómo se
evita:

```python
try:
    funcion.cuerpo.ejecutar(entorno_activacion, errores, tabla)
except SenalReturn as señal:
    return señal.valor
except SenalBreak as señal:
    errores.agregar('Semántico', "'break' usado fuera de un ciclo.", ...)
except SenalContinue as señal:
    errores.agregar('Semántico', "'continue' usado fuera de un ciclo.", ...)
```

Es el mismo `try` que ya tenía `Programa.ejecutar` desde la Sesión 3 —
solo que ahora ocurre una vez POR CADA LLAMADA, no una sola vez al final.

### 3. Declaración previa: casi no es un problema aquí (y por qué sí lo es en otros lenguajes)

`ejemplos/06_funciones.mpas` (sección 4) tiene `esPar` llamando a
`esImpar` ANTES de que `esImpar` aparezca en el texto, y viceversa —
recursión mutua, sin ningún `forward` ni truco especial. Funciona porque
`Funcion.ejecutar` solo GUARDA la función (no ejecuta su cuerpo), y para
cuando alguien realmente LLAMA a `esPar`, las dos declaraciones ya
corrieron y las dos están en el entorno. La resolución de nombres pasa
**al momento de la llamada**, no al momento de declarar.

En un compilador de una sola pasada esto SÍ es un problema real: hay que
conocer la firma de una función antes de poder generar código para
llamarla, así que hace falta una declaración previa explícita (`forward`,
en Pascal de verdad) o una fase separada que recolecte todas las firmas
antes de generar código. Si su proyecto hace algo parecido a resolución
de tipos ANTES de ejecutar, este problema les puede aparecer de verdad,
aunque aquí no lo hizo.

### 4. Arreglos: sin sintaxis literal, siempre con valor por defecto

```python
class DeclaracionArreglo(Instruccion):
    def ejecutar(self, entorno, errores, tabla):
        valor_por_defecto = VALORES_POR_DEFECTO.get(self.tipo_elemento)
        valores = [valor_por_defecto] * self.tamano
        ...
```

`var notas: array[5] of integer;` arranca siempre en `[0, 0, 0, 0, 0]` —
no existe `var notas: array[5] of integer := [1, 2, 3, 4, 5];`. El
tamaño, además, tiene que ser un `ENTERO` literal en el texto (no una
constante ya declarada, no una expresión): son las dos simplificaciones
deliberadas de esta parte. `Indexado` y `AsignacionIndexada` validan el
rango antes de leer o escribir, y reportan error semántico (sin detener
el programa) si el índice se sale — pruébenlo con `ejemplos/
07_arreglos.mpas`, sección 3.

### 5. Todo se pasa por valor, incluidos los arreglos

```python
if isinstance(valor, list):
    valor = list(valor)   # copia, para no compartir el mismo objeto
entorno_activacion.declarar(parametro.nombre, valor, tipo=parametro.tipo)
```

Sin esta copia, una función que modificara un elemento de un arreglo
recibido como parámetro estaría modificando el arreglo ORIGINAL de quien
la llamó (porque las listas de Python son mutables y `entorno.buscar`
devuelve el mismo objeto). `ejemplos/07_arreglos.mpas` (sección 4) lo
demuestra: `duplicarPrimero(notas)` no cambia `notas[0]` afuera.

Esto también reveló una inconsistencia que se corrigió sobre la marcha:
`TablaSimbolos.registrar` recibía la lista original de
`DeclaracionArreglo` (no una copia), así que el "Valor" mostrado en la
tabla terminaba reflejando el estado FINAL del arreglo, no su valor al
declararse — al revés de lo que el README de la Sesión 2 prometía
explícitamente para variables escalares ("no es una foto en vivo").
Se arregló guardando `list(valores)` en vez de `valores`. Queda como
ejemplo de que un tipo de dato mutable nuevo (una lista, en este caso)
puede romper en silencio una promesa de diseño que ya daban por sentada
para los tipos anteriores, todos inmutables.

### 6. El hueco de `ambito` de la Sesión 3 ya se cerró

```python
class Entorno:
    def __init__(self, padre=None, ambito=None):
        ...
        if ambito is not None:
            self.ambito = ambito
        elif padre is not None:
            self.ambito = padre.ambito
        else:
            self.ambito = 'programa'
```

`Declaracion.ejecutar` y `DeclaracionArreglo.ejecutar` ahora registran
`ambito=entorno.ambito` en vez del `'programa'` fijo de antes. Solo
`Llamada.evaluar` pasa un `ambito` nuevo explícito al crear el entorno de
activación; todo lo demás (un `if`, un `while`, un bloque suelto) lo
hereda solo. Corran `ejemplos/06_funciones.mpas` y miren la tabla de
símbolos: la `version` de adentro de `quienLlama` sale con
`ambito=quienLlama`, no `programa`.

### 7. Una función embebida, como siempre, un solo caso representativo

```python
FUNCIONES_EMBEBIDAS = {
    'length': len,
}
```

`length(arreglo)` (o `length(cadena)`) se resuelve ANTES de mirar el
entorno — no ocupa una entrada ahí, así que técnicamente no se puede
"sombrear" declarando una variable `length` propia (no es una regla real
de shadowing, es una simplificación de cómo está resuelto el `if` dentro
de `Llamada.evaluar`).

---

## Detalles del lexer y del parser que vale la pena mirar

### Tres cosas nuevas que empiezan igual: `IDENTIFICADOR`

```
foo := 10;              -> Asignacion       (ASIGNACION después del ID)
foo(1, 2);               -> Llamada (dentro de una expresión, PARIZQ después del ID)
foo[0] := 10;            -> AsignacionIndexada (CORCHETEIZQ, después ASIGNACION)
foo[0]                   -> Indexado         (dentro de una expresión, CORCHETEIZQ)
etiqueta: while ...      -> While etiquetado (DOSPUNTOS después del ID)
```

Ningún conflicto: es el mismo truco que ya usaban desde la Sesión 2 (`var
x: integer` vs. `x := 10`) — LALR(1) decide con un solo token de
anticipación, el que viene inmediatamente después del identificador.

### Parámetros de arreglo reutilizan el formato de texto de `DeclaracionArreglo`

```python
def p_parametro_arreglo(p):
    'parametro : IDENTIFICADOR DOSPUNTOS ARRAY CORCHETEIZQ ENTERO CORCHETEDER OF TIPO'
    tipo = f'array[{p[5]}] of {p[8]}'
    p[0] = Parametro(p[1], tipo, linea, columna)
```

Así, no importa si un arreglo llegó por `var` o por parámetro: su `tipo`
se ve igual en la tabla de símbolos, y `Funcion` no necesita dos formas
distintas de representarlo.

### `Parametro` es un `Nodo`, otra vez por `dot.py`

Mismo truco que `RamaCase` en la Sesión 3: `Parametro` podría haber sido
una tupla `(nombre, tipo)` suelta, pero se hizo una clase `Nodo` para que
`dot.py` la dibuje sin que tengamos que enseñarle nada — sigue sin
conocer ninguna clase del AST por nombre, y ya van dos semanas seguidas
que una decisión de diseño nueva se resuelve solo por seguir esa regla.

### `Expresion.evaluar` gana un tercer parámetro: `tabla`

Antes, ninguna expresión necesitaba la tabla de símbolos — solo las
instrucciones. Eso deja de ser cierto en cuanto una expresión (`Llamada`)
puede ejecutar el CUERPO COMPLETO de una función, y ese cuerpo declara
variables como cualquier otro bloque. Es un cambio mecánico (agregar el
parámetro y pasarlo hacia abajo en cada `evaluar`), pero toca cada nodo
de expresión existente — revisen el diff completo de `ast_nodes.py` si
quieren ver el alcance real de un cambio "mecánico" en la práctica.

---

## Ejercicios sugeridos

Sobre `minipascal/`, en orden de dificultad:

1. Agreguen validación de tipos a los argumentos de una llamada: hoy
   `Llamada.evaluar` solo revisa la CANTIDAD de argumentos, no que cada
   uno calce con el tipo declarado del parámetro correspondiente.
2. Hagan que `Funcion` valide que su cuerpo SIEMPRE termine en un
   `return` en todos los caminos posibles (hoy, si el cuerpo termina sin
   pasar por ninguno, se devuelve el valor por defecto del tipo en
   silencio — pruébenlo comentando el `return` de `cuadrado`).
3. Agreguen una segunda función embebida además de `length` (por ejemplo
   `ord`/`chr`, o `abs`), siguiendo el mismo patrón de
   `FUNCIONES_EMBEBIDAS`.
4. El tamaño de un arreglo hoy tiene que ser un `ENTERO` literal en el
   texto. Permitan que sea también el nombre de una `const` ya declarada
   (van a necesitar resolverla en el momento de ejecutar
   `DeclaracionArreglo`, no en el parser — ¿por qué no en el parser?).
5. Corran `python -c "import parser"` después de cada cambio de
   gramática y lean la salida completa — sobre todo si agregan una nueva
   forma que empiece con `IDENTIFICADOR`, que es justo el patrón que este
   archivo ya explotó tres veces esta semana.

---

## Qué falta para tu proyecto

Lo que **NO** está en este ejemplo y ustedes sí tienen que implementar:

| Falta | Dónde lo pide el enunciado | Cuándo lo vemos |
|---|---|---|
| Registros (`struct`) | 3.3.12 | **Solo ustedes** |
| Slices, `String::from`, raw strings | 3.3.10, 3.3.11 | **Solo ustedes** |
| Retorno múltiple | 3.3.9 | **Solo ustedes** |
| Operadores lógicos (`&&`, `\|\|`, `!`) con corto circuito | 3.3.7 | **Solo ustedes** (Sesión 3, ejercicio 2) |
| Reportes en HTML (errores y tabla de símbolos) | 3.4.1, 3.4.2 | Sesión 5 |
| API REST con Django | 6 | Sesión 5 |
| GUI completa (editor, consola, pestañas) | 3.1.2 | **Solo ustedes** |
| Mutabilidad estilo Rust (`mut`), inferencia de tipos | 3.2.3, 3.3.2, 3.3.3 | **Solo ustedes** |

Y hoy mismo, en el código que ya tienen:

- Ningún operador aritmético salvo `+` (y `<` en comparaciones) tiene
  tabla de tipos — hueco heredado de las Sesiones 2 y 3.
- `Llamada.evaluar` no valida los TIPOS de los argumentos contra los
  parámetros declarados, solo la cantidad.
- Una función puede terminar sin pasar por ningún `return` y no se
  reporta ni error ni advertencia — simplemente devuelve el valor por
  defecto de su tipo de retorno, en silencio.
- Los arreglos no tienen sintaxis literal (`[1, 2, 3]`), su tamaño debe
  ser un entero escrito directamente en el texto, y se pasan siempre por
  VALOR (copiados) a una función — nunca por referencia.
- `Repeat` sigue sin aceptar etiquetas (Sesión 3), y `Case` sigue
  admitiendo solo literales enteros, uno por rama.
- `p_error` (en `parser.py`) sigue sin recuperación de errores
  sintácticos.

Todos estos tienen un comentario `LO QUE FALTA AQUÍ` (o una nota
explícita) en el código, en el lugar exacto donde va el arreglo.
