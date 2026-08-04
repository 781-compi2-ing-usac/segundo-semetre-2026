# Sesión 2 — Entornos, tabla de símbolos, tipos y errores

Organización de Lenguajes y Compiladores 2 — Sección B · martes 04/08/2026
Material de apoyo para el Proyecto 1 (**OxigenScript**)


---

## El problema de hoy

La Sesión 1 dejó MiniPascal sin variables: `writeln(2 + 3 * 4);` y nada
más. Esta es la sesión más densa de las cinco porque vamos a ver gran parte
del análisis semántico:

- ¿Dónde vive una variable mientras el programa corre, y qué pasa cuando
  el bloque donde se declaró termina?
- ¿Cómo se sabe que `2 + 'hola'` no tiene sentido, y qué se hace cuando
  pasa — ¿detiene el programa?
- ¿Y si alguien usa una variable que nunca declaró, o intenta modificar
  una constante?

El enunciado (sección 3.4.1) es claro: **ningún error
semántico debe detener la ejecución**. Hay que reportarlo y seguir, para
poder listar varios errores en una sola corrida. Esa sola idea cambia la
forma de todo el código de esta semana.



---

## Qué hay en esta carpeta

```
segundo-semetre-2026/
└── semana3/seccionB/
    ├── requirements.txt
    ├── micro/
    │   ├── 01_entorno.py          cadena de entornos con padre, sin PLY
    │   └── 02_tabla_dominante.py  tabla de tipos resultantes, sin PLY
    └── minipascal/
        ├── lexer.py           + VAR, CONST, TIPO, DOSPUNTOS, ASIGNACION
        ├── entorno.py         NUEVO — Entorno en tiempo de ejecución
        ├── errores.py         NUEVO — ListaErrores, que no detiene nada
        ├── tabla_simbolos.py  NUEVO — TablaSimbolos
        ├── ast_nodes.py       + Variable, Declaracion, Asignacion
        ├── parser.py          + reglas de var/const/asignación
        ├── dot.py             sin cambios de lógica (ignora atributos None)
        ├── main.py            ahora usa Entorno/ListaErrores/TablaSimbolos reales
        └── ejemplos/
            ├── 01_hola.mpas         (Sesión 1, sigue funcionando igual)
            ├── 02_aritmetica.mpas   (Sesión 1)
            ├── 03_errores.mpas      (Sesión 1)
            └── 04_variables.mpas    NUEVO — variables, constantes, 3 errores
```

## Cómo correrlo

```bash
cd semana3/seccionB
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 micro/01_entorno.py
python3 micro/02_tabla_dominante.py

cd minipascal
python3 main.py ejemplos/04_variables.mpas

# cada archivo corre solo, para probar una pieza a la vez:
python3 entorno.py         # Entorno con var/const, sin PLY ni AST
python3 errores.py         # ListaErrores sola
python3 tabla_simbolos.py  # TablaSimbolos sola
python3 parser.py          # lexer + parser + ejecución
```

---

## Las cuatro ideas de hoy

### 1. `Entorno` vs. `TablaSimbolos` — NO son lo mismo

Se pueden llegar a confundir, así que van separadas a propósito en
dos archivos:

| | `Entorno` | `TablaSimbolos` |
|---|---|---|
| Vive en | tiempo de ejecución | todo el programa, de principio a fin |
| Forma | árbol (cada bloque el suyo, con padre) | una lista plana que solo crece |
| Cuándo desaparece | al salir del bloque | nunca — es la bitácora del reporte |
| Para qué sirve | que el programa pueda USAR una variable | que quede constancia de que existió |

`Declaracion.ejecutar` (`ast_nodes.py`) toca las dos, cada una para algo
distinto:

```python
entorno.declarar(self.nombre, valor, tipo=self.tipo, constante=self.constante)
tabla.registrar(nombre=self.nombre, categoria=..., tipo=self.tipo, ...)
```

Si solo tuvieran `Entorno`, no podrían generar el reporte de símbolos al
final: las variables locales de un bloque que ya cerró se pierden apenas
termina ese bloque (nadie más tiene una referencia a su `Entorno`). Por
eso `TablaSimbolos` existe aparte, y por eso nunca se le borra nada.

### 2. Un bloque abre su propio ámbito

El comentario `LO QUE FALTA AQUÍ` de la Sesión 1 decía exactamente esto.
Ya está resuelto:

```python
class Bloque(Instruccion):
    def ejecutar(self, entorno, errores, tabla):
        entorno_local = Entorno(padre=entorno)
        for instruccion in self.instrucciones:
            instruccion.ejecutar(entorno_local, errores, tabla)
```

Ningún nodo especial para `if` o `while` va a necesitar repetir esto: en
la gramática, el cuerpo de CUALQUIER estructura de control es un
`Bloque`. Esta única clase es la que abre ámbito para todos.

Corran `ejemplos/04_variables.mpas` y sigan el rastro de `edad`: se
declara afuera, se modifica desde dentro de un bloque anidado
(`edad := 99;`), y el cambio SÍ se ve afuera cuando el bloque termina —
porque `asignar` sube por la cadena de padres a buscarla, mientras que
`declarar` (la de una variable *nueva*) nunca sale del entorno local.
Esa distinción entre `declarar` y `asignar` es la que hace posible el
shadowing sin romper la modificación de variables externas.

### 3. Nadie actúa a ciegas: primero se pregunta, después se actúa

`Entorno` (`entorno.py`) NO valida nada ni imprime mensajes de error.
Sus métodos `asignar`/`buscar` **asumen** que ya llamaron `existe(...)` y
`es_constante(...)` antes. La razón: solo el nodo del AST tiene la línea
y columna para reportar un buen mensaje; `Entorno` no las tiene.

```python
class Asignacion(Instruccion):
    def ejecutar(self, entorno, errores, tabla):
        valor = self.expresion.evaluar(entorno, errores)
        if valor is None:
            return   # ya se reportó el error al evaluar la expresión

        if not entorno.existe(self.nombre):
            errores.agregar('Semántico', f"La variable '{self.nombre}' no ha sido declarada.", ...)
            return

        if entorno.es_constante(self.nombre):
            errores.agregar('Semántico', f"No es posible modificar la variable '{self.nombre}'...", ...)
            return

        entorno.asignar(self.nombre, valor)
```

Nunca se llama `entorno.asignar(...)` "a ver qué pasa" ni se atrapa una
excepción después. Se pregunta primero, y solo se actúa si las preguntas
salieron bien. Ese patrón — preguntar antes de actuar, y si algo falla
`errores.agregar(...)` + `return None`/`return`, nunca una excepción — es
el que van a repetir en cada validación semántica de su proyecto.

### 4. La tabla de tipos, ahora con errores de verdad

`micro/02_tabla_dominante.py` mostraba la idea con un `print`. En
`Aritmetica.evaluar` (`ast_nodes.py`) es la misma tabla, conectada a
`ListaErrores`:

```python
TIPOS_SUMA = {
    ('integer', 'integer'): 'integer',
    ('integer', 'real'):    'real',
    ('real',    'real'):    'real',
    ('string',  'string'):  'string',
}
```

Solo validamos `+`. Las operaciones con: `-`, `*` y `/` siguen operando "a ciegas" (igual que
en v1) — es lo que no se cubre esta semana, marcado con
`LO QUE FALTA AQUÍ` en el código.

También noten `tipo_de_valor(valor)`: deriva el tipo de MiniPascal
mirando la clase de Python del valor (`isinstance`). Funciona aquí porque
los 4 tipos de MiniPascal coinciden 1 a 1 con tipos de Python. **Su
proyecto no puede hacer lo mismo**: `i32` vs `i64`, o `char` vs
un `String` de un carácter, no tienen un tipo de Python distinto que los
diferencie. El tipo de una variable en OxigenScript debe salir de la
declaración o la inferencia, no de adivinar con `isinstance`.

---

## Detalles del lexer y del parser que vale la pena mirar

### Un solo token para los cuatro tipos

```python
reservadas = {
    ...
    'integer': 'TIPO',
    'real': 'TIPO',
    'boolean': 'TIPO',
    'string': 'TIPO',
}
```

A la gramática no le interesa distinguir `integer` de `real` como
producciones distintas — le basta con "aquí va un nombre de tipo", y el
texto exacto (`p[4]` en la regla) ya viene incluido. Esto evita
escribir cuatro reglas de gramática casi idénticas.

### `:` y `:=` sin que se confundan

```python
t_ASIGNACION = r':='
t_DOSPUNTOS = r':'
```

PLY ordena las reglas simples (las que son un string, no una función) de
la regex más larga a la más corta automáticamente. Por eso `x: integer`
(un solo `:`) y `x := 10` (`:=`) se distinguen solos, sin que ustedes
tengan que decidir el orden a mano.

### Misma primera palabra, dos producciones distintas

```
instruccion : IDENTIFICADOR ASIGNACION expresion PUNTOCOMA   (asignación)
expresion   : IDENTIFICADOR                                   (lectura)
```

`x := 5;` y `x + 1` empiezan los dos con `IDENTIFICADOR`, pero
`instruccion` y `expresion` son no-terminales distintos, y MiniPascal no
tiene "expresiones como instrucción" (a diferencia de C, donde `x;` solo
ya es válido). Por eso el parser nunca se confunde sobre cuál de las dos
está construyendo — no hubo que resolver ningún conflicto a mano.
Confirmen ustedes mismos que no hay conflictos corriendo
`python -c "import parser"` y leyendo la salida.

---

## Ejercicios sugeridos

Sobre `minipascal/`, en orden de dificultad:

1. Repliquen el patrón de `TIPOS_SUMA` para `-`, `*` y `/`: escriban su
   propia tabla y conéctenla en `Aritmetica.evaluar`, exactamente como
   ya está hecho para `+`.
2. Agreguen el operador de asignación compuesta `+=` (o el que usen
   ustedes en su proyecto). Van a necesitar un token nuevo y una regla
   de gramática que, en lugar de reemplazar el valor, lo lea primero con
   `entorno.buscar`, lo sume, y lo vuelva a guardar con `entorno.asignar`.
3. Agreguen shadowing explícito: que declarar dos veces la misma variable
   en el MISMO bloque sea un error semántico (`entorno.declarar` hoy no
   lo impide — revisen `existe` contra el diccionario LOCAL, no toda la
   cadena de padres).
4. Miren `TablaSimbolos.imprimir()` y decidan cómo mostrarían el "Ámbito"
   de forma más útil que el `'programa'` fijo que usamos hoy — pista:
   `Entorno` no sabe su propio nombre todavía.
5. Corran `python3 -c "import parser"` después de cada cambio en la
   gramática. Los conflictos *shift/reduce* de PLY son advertencias
   silenciosas que después se convierten en horas de depuración.

---

## Qué falta para tu proyecto

Lo que **NO** está en este ejemplo y ustedes sí tienen que implementar:

| Falta | Dónde lo pide el enunciado | Cuándo lo vemos |
|---|---|---|
| `if`, `while`, `loop`, `match` | 3.3.8 | Sesión 3 |
| `break`, `continue`, `return`, etiquetas | 3.3.9 | Sesión 3 |
| Funciones, parámetros, `fn main()` | 3.3.13, 3.3.15 | Sesión 4 |
| Arreglos, slices, strings, structs | 3.3.10–3.3.12 | Sesión 4 |
| Funciones embebidas | 3.3.14 | Sesión 4 |
| Reportes en HTML (errores y tabla de símbolos) | 3.4.1, 3.4.2 | Sesión 5 |
| API REST | 6 | Sesión 5 |
| GUI completa (editor, consola, pestañas) | 3.1.2 | **Solo ustedes** |
| Mutabilidad estilo Rust (`mut`), inferencia de tipos | 3.2.3, 3.3.2, 3.3.3 | **Solo ustedes** |

Y hoy mismo, en el código que ya tienen:

- `Aritmetica.evaluar` solo protege `+` con tabla de tipos. `-`, `*` y
  `/` siguen operando "a ciegas": `writeln('hola' - 1);` detiene con un
  error de Python, no con un mensaje decente.
- `p_error` (en `parser.py`) sigue sin recuperación: un error de sintaxis
  detiene el análisis completo, aunque los errores semánticos ya no lo
  hagan. El enunciado pide que también se pueda seguir después de un
  error sintáctico (con el token especial `error` de PLY).
- `entorno.declarar` no impide declarar dos veces la misma variable en el
  mismo bloque — no hay error de "variable ya declarada".
- `TablaSimbolos` guarda el valor de la variable **al momento de
  declararla**, no su valor final. Si reasignan la variable después, esa
  fila de la tabla no se entera (revisen el comentario en
  `tabla_simbolos.py`).
- Ninguno de los dos reportes (errores, símbolos) tiene todavía versión
  HTML — solo se imprimen por consola.

Todos estos tienen un comentario `LO QUE FALTA AQUÍ` (o una nota
explícita) en el código, en el lugar exacto donde va el arreglo.
