# Sesión 1 — El patrón Intérprete y el AST

Organización de Lenguajes y Compiladores 2 — Sección B · martes 28/07/2026
Material de apoyo para el Proyecto 1 (**OxigenScript**)


> MiniPascal ↔ OxigenScript.

---

## El problema de hoy

La semana pasada hicimos una calculadora donde el parser calculaba directo:

```python
def p_expression_plus(p):
    'expression : expression PLUS expression'
    p[0] = p[1] + p[3]          # el parser CALCULA
```

Eso funciona para una calculadora y **no funciona para nada más**:

- Un `if` no debe ejecutar sus dos ramas, solo una. El parser no sabe cuál,
  porque la condición todavía no se ha evaluado.
- Un `while` debe ejecutar su cuerpo N veces. El parser lo lee **una** vez.
- Una función se declara una vez y se llama muchas, a veces antes de que el
  parser llegue a su declaración.
- El enunciado pide un **reporte gráfico del AST** y una **tabla de
  símbolos**. Si calcularon directo, no hay árbol que reportar.

La solución es partir el trabajo en dos momentos:

```
texto  →  [lexer]  →  tokens  →  [parser]  →  AST  →  [ejecutar]
                                  construye        ejecuta
```

El parser **solo construye objetos**. Cada objeto sabe ejecutarse a sí mismo
con un método. Eso es el **patrón Intérprete**, y es lo que pide el enunciado.

---

## Qué hay en esta carpeta

```
segundo-semetre-2026/
└── semana2/seccionB/
    ├── requirements.txt
    ├── micro/
    │   ├── 01_interprete_a_mano.py   el patrón sin PLY, árbol armado a mano
    │   └── 02_linea_columna.py       cómo obtener línea y columna de un token
    └── minipascal/
        ├── lexer.py        tokens, palabras reservadas, comentarios, posiciones
        ├── ast_nodes.py    las clases del AST  ← aquí vive la ejecución
        ├── parser.py       la gramática        ← aquí vive la construcción
        ├── dot.py          el AST en formato Graphviz
        ├── main.py         el flujo completo
        └── ejemplos/*.mpas programas de prueba
```

## Cómo correrlo

```bash
cd semana2/seccionB
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python micro/01_interprete_a_mano.py
python micro/02_linea_columna.py

cd minipascal
python main.py ejemplos/01_hola.mpas
python main.py ejemplos/02_aritmetica.mpas
python main.py ejemplos/03_errores.mpas

# cada archivo corre solo, para probar una etapa a la vez:
python lexer.py     # solo tokens
python parser.py    # lexer + parser + ejecución
python dot.py       # imprime el DOT de un árbol de ejemplo y renderiza ast.png
```

---

## Las cuatro ideas de hoy

### 1. Dos jerarquías: expresiones e instrucciones

En `ast_nodes.py`:

```
Nodo                 guarda línea y columna
 ├── Expresion       evaluar(entorno)  →  DEVUELVE un valor
 │    ├── Literal
 │    ├── Aritmetica
 │    └── Negacion
 └── Instruccion     ejecutar(entorno) →  HACE algo
      ├── Writeln
      └── Bloque
```

`2 + 3` es una **expresión**: produce un valor.
`writeln(...)` es una **instrucción**: produce un efecto.

Esa separación se les va a repetir todo el proyecto. Cuando duden de si algo
lleva `evaluar` o `ejecutar`, pregúntense: *¿esto se puede poner a la derecha
de un `=`?* Si sí, es expresión.

El método central es este:

```python
def evaluar(self, entorno):
    izq = self.izquierdo.evaluar(entorno)   # le pido a mis hijos
    der = self.derecho.evaluar(entorno)     # que se calculen
    if self.operador == '+':
        return izq + der
    ...
```

Ningún `if` pregunta "¿qué tipo de nodo eres?". Cada clase sabe lo suyo.
Agregar una operación nueva = agregar una clase, sin tocar las demás.



### 2. La precedencia es la forma del árbol

Corran `python dot.py` y miren el árbol de `2 + 3 * 4`:

```
      Aritmetica +
       /        \
  Literal 2   Aritmetica *
               /       \
          Literal 3  Literal 4
```

La multiplicación quedó **más abajo**, así que se evalúa primero. Por eso
da 14 y no 20. `evaluar()` no sabe nada de precedencia: solo baja recursivo.
Quien resuelve la precedencia es la tabla `precedence` del parser, mientras
construye.

Si su intérprete da resultados aritméticos raros, el problema casi nunca
está en `evaluar()`. Está en la forma del árbol. **Dibújenlo.**

### 3. Línea y columna, desde el primer día

Todo error del enunciado se ve así:

```
[Error Semántico] Línea 6, Columna 5
No es posible modificar una variable inmutable.
```

Para eso, cada nodo del AST tiene que guardar dónde apareció. PLY da dos
cosas y ninguna es la columna:

- `lexer.lineno` — **no se actualiza sola**. Necesitan la regla `t_newline`.
  Si se les olvida, todos sus errores van a decir "Línea 1".
- `lexpos` — posición absoluta en el texto. La columna se calcula así:

```python
def encontrar_columna(entrada, lexpos):
    inicio_de_linea = entrada.rfind('\n', 0, lexpos)
    return lexpos - inicio_de_linea
```

Agréguenlo desde ahora. Meterlo después significa tocar todas las clases del
AST y todas las reglas del parser de un solo golpe.

### 4. El AST se dibuja, y sirve para depurar

`dot.py` genera el archivo `.dot` que pide el enunciado (sección 3.4.3), y
además lo renderiza a `.png` automáticamente. Se los doy al inicio y no al
final porque es la **mejor herramienta de depuración** que van a tener:
cuando algo dé un resultado raro, dibujen el árbol.

```bash
sudo apt install graphviz     # una sola vez
python main.py ejemplos/02_aritmetica.mpas
```

Con eso ya tienen `ast.dot` y `ast.png` en la carpeta. Nada de correr `dot`
a mano.

**Ojo con la trampa:** `pip install graphviz` (ya está en
`requirements.txt`) instala el paquete de Python, que es solo un
**mensajero** — arma el texto DOT y se lo entrega al programa `dot` para que
lo dibuje. El que realmente dibuja es `dot`, y ESE es software del sistema
operativo (C, no Python), así que pip no lo instala. Si no corrieron
`sudo apt install graphviz`, `renderizar_png` en `dot.py` lo detecta y
devuelve `None` en vez de reventar el programa — van a ver un aviso, y el
`.dot` de todas formas queda escrito para pegarlo en
<https://dreampuf.github.io/GraphvizOnline/> mientras tanto.

Esto no es un detalle menor: en su proyecto, el reporte de AST **no puede
tumbar el resto del intérprete** si Graphviz no está en la máquina donde
corre. Fíjense en cómo `main.py` sigue funcionando aunque `renderizar_png`
devuelva `None`.

Además, `dot.py` **no menciona ninguna clase del AST por nombre**: usa
`vars(nodo)` para descubrir los atributos. Por eso va a seguir funcionando
en las próximas semanas sin tocarlo, aunque agreguemos nodos nuevos.

---

## Detalles del lexer que vale la pena mirar

### Palabras reservadas

No escriban `t_BEGIN = r'begin'`. Con eso, el identificador `beginner` se
parte en el token `BEGIN` más el identificador `ner`. Es un bug silencioso y
clásico.

Lo correcto es reconocer todo como identificador y después consultar un
diccionario:

```python
reservadas = {'program': 'PROGRAM', 'begin': 'BEGIN', ...}

def t_IDENTIFICADOR(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reservadas.get(t.value.lower(), 'IDENTIFICADOR')
    return t
```

(El `.lower()` es porque Pascal no distingue mayúsculas en palabras
reservadas. **OxigenScript sí es case sensitive**)

### El orden de las reglas

PLY prueba primero **todas las funciones**, en el orden en que aparecen en el
archivo; después las reglas escritas como string, de la regex más larga a la
más corta.

Por eso `t_REAL` va antes que `t_ENTERO`: si no, `3.14` se leería como
`ENTERO(3) PUNTO ENTERO(14)`.

### Los dos comentarios

```python
def t_comentario_bloque(t):
    r'\(\*(.|\n)*?\*\)'
    t.lexer.lineno += t.value.count('\n')
    # sin `return t`, el token se descarta y nunca llega al parser
```

El `*?` es "no ambicioso": para en el **primer** cierre. Sin él, un archivo
con dos comentarios omitiría todo el código que hay entre ellos.

Estas reglas simples tienen límites reales, y los van a encontrar: un
comentario de llaves no puede contener una llave de cierre, y uno de
paréntesis-asterisco no puede contener su propio cierre. Cuando escribimos
`ejemplos/01_hola.mpas` caímos justo en eso.

El enunciado además les pide reportar como **error léxico**
un comentario de bloque sin cerrar. Piensen qué regla hace falta para eso:
la regex actual simplemente no coincide y los caracteres caen en `t_error`
uno por uno, lo cual no es el mensaje que quieren dar.

---

## Ejercicios sugeridos

Sobre `minipascal/`, en orden de dificultad:

1. Agreguen los operadores `div` y `mod` (división entera y residuo de
   Pascal). Pista: son palabras reservadas, no símbolos, y necesitan entrar
   en la tabla `precedence` al nivel de `*` y `/`.
2. Agreguen una instrucción `write(...)` que imprima **sin** salto de línea.
3. Hagan que `writeln` acepte varias expresiones separadas por coma:
   `writeln('x vale ', 2 + 3);`. Van a necesitar una regla de lista, como
   `instrucciones`.
4. Cambien `Aritmetica.evaluar` para que, antes de operar, revise que los
   tipos sean compatibles, y que imprima un error con línea y columna en vez
   de reventar. Esto es un adelanto de la Sesión 2.
5. Corran `python -c "import parser"` después de cada cambio en la gramática
   y lean los mensajes. Los conflictos *shift/reduce* de PLY son advertencias
   silenciosas que después se convierten en horas de depuración.

---

## Qué falta para tu proyecto

Lo que **NO** está en este ejemplo y ustedes sí tienen que implementar:

| Falta | Dónde lo pide el enunciado | Cuándo lo vemos |
|---|---|---|
| Variables, ámbitos, tabla de símbolos | 3.2.3, 3.3.2, 3.4.2 | Sesión 2 |
| Tipos y tablas de tipos resultantes | 3.2.3, 3.3.5–3.3.7 | Sesión 2 |
| Errores que se acumulan y no detienen la ejecución | 3.4.1 | Sesión 2 |
| Recuperación de errores sintácticos (token `error` de PLY) | 3.4.1 | Sesión 2 |
| `if`, `while`, `loop`, `match` | 3.3.8 | Sesión 3 |
| `break`, `continue`, `return`, etiquetas | 3.3.9 | Sesión 3 |
| Funciones, parámetros, `fn main()` | 3.3.13, 3.3.15 | Sesión 4 |
| Arreglos, slices, strings, structs | 3.3.10–3.3.12 | Sesión 4 |
| Funciones embebidas | 3.3.14 | Sesión 4 |
| Reportes HTML y API REST con Django | 3.4, 6 | Sesión 5 |
| GUI completa (editor, consola, pestañas) | 3.1.2 | **Solo ustedes** |
| Mutabilidad (`mut`), shadowing, inferencia de tipos | 3.2.3, 3.3.2, 3.3.3 | **Solo ustedes** |

Y hoy mismo, en el código que ya tienen:

- `Aritmetica.evaluar` opera sin revisar tipos: `writeln('hola' - 1);`
  revienta con un error de Python, no con un mensaje decente.
- `Bloque.ejecutar` no abre un ámbito nuevo. El parámetro `entorno` ya viaja
  por todo el AST justamente para que ese cambio sea de una línea.
- `p_error` reporta y se rinde. El enunciado pide seguir analizando.
- El intérprete imprime los errores pero no los **guarda**, así que nadie
  puede preguntar después "¿hubo errores?" ni generar el reporte.

Los cuatro tienen un comentario `LO QUE FALTA AQUÍ` en el código, en el
lugar exacto donde va el arreglo.
