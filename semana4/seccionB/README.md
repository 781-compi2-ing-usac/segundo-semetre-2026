# Sesión 3 — Control de flujo y transferencia

Organización de Lenguajes y Compiladores 2 — Sección B · martes 11/08/2026
Material de apoyo para el Proyecto 1 (**OxigenScript**)

---

## El problema de hoy

Hasta la Sesión 2, MiniPascal ejecutaba instrucciones **en línea recta**:
una tras otra, sin saltos, sin repetición, sin decisiones. Esta semana
agregamos las cuatro cosas que rompen esa línea recta: `if`, `while`,
`repeat...until`, `case`, y las instrucciones que interrumpen un ciclo a
la fuerza (`break`, `continue`).

Dos preguntas nuevas que no existían antes:

- ¿Cómo hace `break` (que puede estar enterrado dentro de varios `if` y
  bloques anidados) para "avisarle" al ciclo correcto que debe parar,
  sin que cada nivel intermedio tenga que enterarse?
- ¿Qué significa `if 5 + 3 then ...`? El enunciado exige que la condición
  sea `boolean` — ¿qué hace el intérprete cuando no lo es?

---

## Qué hay en esta carpeta

```
segundo-semetre-2026/
└── semana4/seccionB/
    ├── requirements.txt
    ├── micro/
    │   ├── 01_senales.py      break/continue/return con excepciones, sin PLY
    │   └── 02_conflictos.py   el "dangling else" y cómo leerlo en PLY
    └── minipascal/
        ├── lexer.py           + IF/THEN/ELSE/WHILE/DO/REPEAT/UNTIL/CASE/OF/
        │                        BREAK/CONTINUE, operadores relacionales
        ├── senales.py         NUEVO — SenalBreak, SenalContinue
        ├── ast_nodes.py       + Comparacion, If, While, Repeat, Case,
        │                        RamaCase, Break, Continue
        ├── parser.py          + gramática de control de flujo
        ├── entorno.py, errores.py, tabla_simbolos.py, dot.py, main.py   (sin cambios)
        └── ejemplos/
            ├── 01_hola.mpas ... 04_variables.mpas   (Sesiones 1-2, siguen igual)
            └── 05_control_flujo.mpas    NUEVO — if/while/repeat/case/break/continue
```

## Cómo correrlo

```bash
cd semana4/seccionB
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python3 micro/01_senales.py
python3 micro/02_conflictos.py

cd minipascal
python3 main.py ejemplos/05_control_flujo.mpas

# cada archivo corre solo, para probar una pieza a la vez:
python3 senales.py    # (no tiene __main__: es solo las dos clases)
python3 parser.py     # lexer + parser + ejecución de un while pequeño
```

---

## Las ideas de hoy

### 1. `break`/`continue` son excepciones, no banderas

`micro/01_senales.py` muestra por qué: con una bandera (`detener = True`),
CADA nivel intermedio entre el `break` y el ciclo que debe detenerse
tendría que revisarla después de cada instrucción. Con una excepción,
Python la hace subir sola por la pila de llamadas hasta el primero que
sepa atraparla — nadie en el medio necesita saber que existe.

```python
class While(Instruccion):
    def ejecutar(self, entorno, errores, tabla):
        while True:
            ...
            try:
                self.cuerpo.ejecutar(entorno, errores, tabla)
            except SenalContinue as señal:
                if señal.etiqueta not in (None, self.etiqueta):
                    raise      # no era para mí — que la siga atrapando otro
                continue
            except SenalBreak as señal:
                if señal.etiqueta not in (None, self.etiqueta):
                    raise
                break
```

`Break.ejecutar` no "hace" nada — solo lanza `SenalBreak`. Quien decide
qué significa esa señal es el `While` (o `Repeat`) que la atrapa, no
`Break` mismo. Y si nadie la atrapa (un `break` fuera de cualquier
ciclo), `Programa.ejecutar` la agarra al final y la convierte en un error
semántico decente en vez de dejar que Python detenga la ejecución — pruébenlo con un `break;` suelto al inicio de un programa.

### 2. El "dangling else" que casi no fue

`micro/02_conflictos.py` construye, a propósito, una gramática AMBIGUA
(`if ID then stmt [else stmt]`, sin exigir llaves) y ustedes ven el
warning de PLY:

```
WARNING: 1 shift/reduce conflict
```

Cuando fuimos a agregar `if`/`else` a la gramática REAL de MiniPascal, se
armó exactamente ese mismo escenario para probarlo con
`python -c "import parser"` — y **no salió ningún warning**. ¿Por qué?

Porque en MiniPascal el cuerpo de un `if` SIEMPRE es un `bloque`
(`begin...end`), nunca una instrucción suelta:

```
instruccion : IF expresion THEN bloque PUNTOCOMA
            | IF expresion THEN bloque ELSE bloque PUNTOCOMA
```

La ambigüedad clásica aparece cuando el lenguaje permite escribir
`if a then if b then c else d;` SIN llaves — ahí el parser no sabe si la
`stmt` completa (`if b then c`) ya se cerró antes de ver el `else`, o si
debe seguir leyendo. Como en MiniPascal todo `if` obliga a escribir
`begin...end`, esa situación **no se puede ni escribir**: el `else`
siempre queda dentro o fuera de un bloque explícito, sin ambigüedad
posible.

Dejamos el `%prec IFX`/`ELSE` en `precedence` de todas formas (revisen
`parser.py`), como red de seguridad explícita en vez de confiar en que
la situación nunca cambie — si algún día alguien agrega una forma de
`if` sin `begin/end` (como el ejercicio 2 de abajo), la precedencia ya
está lista para resolverlo correctamente.

### 3. Preguntar antes de decidir, otra vez

El mismo patrón de la Sesión 2 (`entorno.existe(...)` antes de
`entorno.asignar(...)`) se repite aquí con un helper nuevo:

```python
def verificar_condicion_booleana(valor, errores, linea, columna, de_donde):
    if valor is None:
        return False   # el error ya se reportó al evaluar la condición
    if tipo_de_valor(valor) != 'boolean':
        errores.agregar('Semántico', f"La condición de {de_donde} debe ser...", ...)
        return False
    return True
```

`If`, `While` y `Repeat` lo usan los tres, cada uno con su propio mensaje
(`"un 'if'"`, `"un 'while'"`, `"un 'repeat...until'"`). Prueben
`if 5 + 3 then ...` y `while 'hola' do ...` en
`ejemplos/05_control_flujo.mpas`: los dos se reportan como error
semántico, con línea y columna, y el programa **sigue** ejecutando lo que
viene después — la misma resiliencia de la Sesión 2, aplicada a un caso
nuevo.

### 4. `repeat...until` es la excepción a la regla de `Bloque`

Todo lo demás (`if`, `while`, un bloque suelto) delega la apertura de
ámbito en `Bloque`, porque todos usan `begin...end`. `repeat...until` NO
usa `begin`/`end` — usa sus propios delimitadores — así que no hay
ningún `Bloque` de por medio, y `Repeat.ejecutar` abre su `Entorno`
directamente:

```python
class Repeat(Instruccion):
    def ejecutar(self, entorno, errores, tabla):
        entorno_local = Entorno(padre=entorno)
        while True:
            ...
```

También es la única estructura de esta semana que **no acepta etiqueta**
— simplificación deliberada. Y corre su cuerpo **al menos una vez**,
al revés de `while`: termina cuando la condición se vuelve VERDADERA, no
mientras lo es.

### 5. Otra vez, un solo caso representativo

`Comparacion` (el nodo de `==`, `!=`, `<`, `>`, `<=`, `>=`) solo valida
tipos para `<`:

```python
TIPOS_MENOR = {
    ('integer', 'integer'): 'boolean',
    ('integer', 'real'):    'boolean',
    ('real',    'real'):    'boolean',
    ('string',  'string'):  'boolean',
}
```

Mismo patrón que `TIPOS_SUMA` de la Sesión 2 para `+`. `==`, `!=`, `>`,
`<=`, `>=` operan sin tabla — es el hueco deliberado de esta semana,
marcado con `LO QUE FALTA AQUÍ` en `ast_nodes.py`.

---

## Detalles del lexer y del parser que vale la pena mirar

### Etiquetas: un identificador seguido de `:`

```
externo: while true do begin
  ...
end;
```

Gramaticalmente esto es `IDENTIFICADOR DOSPUNTOS WHILE ...`, un caso más
del mismo truco de la Sesión 2 (`var x: integer` vs. `x := 10`): el
parser distingue por el token que viene DESPUÉS del identificador. Si es
`ASIGNACION`, es una asignación. Si es `DOSPUNTOS` seguido de `WHILE`, es
un ciclo etiquetado. Ningún conflicto — es solo un token más de
diferencia.

### `case` y por qué `RamaCase` es un `Nodo`

```python
class RamaCase(Nodo):
    def __init__(self, valor, bloque, linea, columna):
        ...
```

Cada rama de un `case` (`1: begin ... end;`) podría haberse guardado como
una tupla `(valor, bloque)` suelta. La hicimos una clase `Nodo` en cambio
para que `dot.py` la pueda dibujar **sin que le tengamos que enseñar
nada nuevo** — sigue recorriendo `vars(nodo)` genéricamente, y una tupla
no es algo que sepa recorrer, pero otro `Nodo` sí. Es la misma promesa de
la Sesión 1 ("`dot.py` no menciona ninguna clase por nombre") puesta a
prueba con una estructura nueva, y sigue cumpliéndose sin tocar ese
archivo.

### La rama `else` de `case` también termina en `;`

```
case dia of
  1: begin ... end;
  2: begin ... end;
else
  begin ... end;
end;
```

Al escribir `ejemplos/05_control_flujo.mpas` nos equivocamos primero
poniendo el `else` SIN el `;` después de su bloque, distinto de como
terminan las demás ramas — y el parser lo rechazó, correctamente. Lo
arreglamos exigiendo el mismo `;` en las dos situaciones. Queda como
recordatorio de que una gramática inconsistente entre casos parecidos
no solo es confusa de leer: es fácil de escribir mal incluso para quien
la diseñó.

---

## Ejercicios sugeridos

Sobre `minipascal/`, en orden de dificultad:

1. Repliquen `TIPOS_MENOR` para `>`, `<=` y `>=`. Decidan ustedes si
   `==`/`!=` necesitan tabla o si tiene sentido permitirlos entre
   cualquier par de tipos (piensen: ¿`5 == 'cinco'` debería ser un error,
   o simplemente `false`?).
2. Agreguen los operadores lógicos `&&`, `||` y `!` (sección 3.3.7 del
   enunciado) con **evaluación de corto circuito**: en `a && b`, si `a`
   da `false`, `b` NUNCA debe evaluarse. Pista: no pueden evaluar los dos
   lados primero y decidir después, como hace `Aritmetica` — tienen que
   evaluar el izquierdo, decidir, y solo evaluar el derecho si hace falta.
3. Agreguen etiquetas a `repeat...until` (hoy no las acepta — es la
   simplificación deliberada de esta semana).
4. Hagan que una rama de `case` acepte varios valores separados por coma
   (`1, 2: begin ... end;`), no solo uno. Van a necesitar una lista de
   enteros en la gramática de `rama`, parecida a la de `instrucciones`.
5. Corran `python -c "import parser"` después de cada cambio en la
   gramática y lean la salida completa — sobre todo si tocan `if`/`else`,
   que es justo donde vive la ambigüedad que este archivo evitó por muy
   poco.

---

## Qué falta para tu proyecto

Lo que **NO** está en este ejemplo y ustedes sí tienen que implementar:

| Falta | Dónde lo pide el enunciado | Cuándo lo vemos |
|---|---|---|
| Operadores lógicos (`&&`, `\|\|`, `!`) con corto circuito | 3.3.7 | **Solo ustedes** (o ejercicio 2) |
| Funciones, parámetros, `fn main()` | 3.3.13, 3.3.15 | Sesión 4 |
| `return`, incluido el retorno múltiple | 3.3.9 | Sesión 4 |
| Arreglos, slices, strings, structs | 3.3.10–3.3.12 | Sesión 4 |
| Funciones embebidas | 3.3.14 | Sesión 4 |
| Reportes en HTML (errores y tabla de símbolos) | 3.4.1, 3.4.2 | Sesión 5 |
| API REST con Django | 6 | Sesión 5 |
| GUI completa (editor, consola, pestañas) | 3.1.2 | **Solo ustedes** |
| Mutabilidad estilo Rust (`mut`), inferencia de tipos | 3.2.3, 3.3.2, 3.3.3 | **Solo ustedes** |

Y hoy mismo, en el código que ya tienen:

- `Comparacion` solo protege `<` con tabla de tipos; `==`, `!=`, `>`,
  `<=` y `>=` operan sin validar (mismo hueco que `-`, `*`, `/` en
  `Aritmetica` desde la Sesión 2).
- `Repeat` no acepta etiquetas.
- `Case` solo admite literales enteros, uno por rama (no listas de
  valores, no cadenas, no booleanos).
- `TablaSimbolos` sigue registrando `ambito='programa'` fijo para TODO,
  sin importar cuántos niveles de `if`/`while` anidados tenga la
  declaración — eso va a cambiar recién cuando existan funciones
  (Sesión 4).
- `p_error` (en `parser.py`) sigue sin recuperación: un solo error de
  sintaxis detiene todo el análisis, aunque los errores semánticos ya no
  lo hagan.

Todos estos tienen un comentario `LO QUE FALTA AQUÍ` (o una nota
explícita) en el código, en el lugar exacto donde va el arreglo.
