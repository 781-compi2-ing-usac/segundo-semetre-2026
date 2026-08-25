# Sesión 5 — Structs, slices y cierre

Organización de Lenguajes y Compiladores 2 — Sección B · martes 25/08/2026
Material de apoyo para el Proyecto 1 (**OxigenScript**) · **Entrega: viernes 28/08/2026**



---

## El problema de hoy — y un ajuste de última hora

Esta sesión iba a ser reportes HTML + Django + cierre. Cambiamos el
enfoque: la Sesión 4 se quedó sin tiempo para **structs y slices**
(secciones 3.3.10 y 3.3.12 del enunciado), y esas dos piezas del lenguaje
todavía no tenían ningún ejemplo. Así que hoy structs y slices llevan la
mayor parte del tiempo, y reportes/Django quedan en versión condensada —
lo justo para que no les falte nada calificable, sin el desarrollo
completo que hubieran tenido en un escenario ideal.

Dos preguntas nuevas:

- Un registro (`struct`) agrupa varios valores con nombre bajo un mismo
  nombre. ¿Es un concepto nuevo, o es la misma idea de "declarar algo y
  guardarlo" que ya usan para variables, arreglos y funciones?
- Un slice es "una porción de un arreglo". ¿Cuál es la diferencia real
  entre eso y simplemente copiar esa porción a un arreglo más chico?

La segunda pregunta es la que más vale la pena que se detengan a
responder antes de programar: el enunciado es explícito en que un slice
**no copia los datos** — es una vista sobre el arreglo original. Esa
palabra, "vista", es la que hace toda la diferencia.

---

## Qué hay en esta carpeta

```
segundo-semetre-2026/
└── semana6/seccionB/
    ├── requirements.txt        + Django
    ├── micro/
    │   ├── 01_structs.py       records sin PLY: tipo, instancia, campos
    │   └── 02_slices.py        VistaArreglo: una vista, no una copia
    ├── minipascal/
    │   ├── lexer.py             + TYPE/RECORD, RANGO ('..'), AMPERSAND ('&'), IGUALTIPO ('=')
    │   ├── ast_nodes.py         + TipoRegistro, DeclaracionRegistro, AccesoCampo,
    │   │                          AsignacionCampo, VistaArreglo, Slice, DeclaracionInferida
    │   ├── parser.py            + gramática de records y slices
    │   ├── reportes.py          NUEVO — errores y tabla de símbolos en HTML
    │   ├── main.py              ahora también escribe reporte.html
    │   ├── entorno.py, errores.py, tabla_simbolos.py, dot.py, senales.py   (sin cambios)
    │   └── ejemplos/
    │       ├── 01_hola.mpas ... 07_arreglos.mpas   (Sesiones 1-4, siguen igual)
    │       ├── 08_structs.mpas   NUEVO — records, paso por valor, 2 errores
    │       └── 09_slices.mpas    NUEVO — vista, no copia, 1 error
    └── api/                     NUEVO — Django mínimo
        ├── manage.py
        ├── config/              settings.py recortado (sin apps que necesiten BD)
        └── interprete/
            ├── views.py         el endpoint POST
            └── templates/interprete/index.html   textarea + botón, nada más
```

## Cómo correrlo

```bash
cd semana6/seccionB
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python micro/01_structs.py
python micro/02_slices.py

cd minipascal
python main.py ejemplos/08_structs.mpas
python main.py ejemplos/09_slices.mpas
python reportes.py     # genera un reporte HTML de ejemplo, sin PLY

cd ../api
python manage.py runserver
# abran http://127.0.0.1:8000/ en el navegador
```

---

## Las ideas de hoy

### 1. Un registro es "declarar dos veces" — nada más

Primero declaran el TIPO (una vez), después declaran VARIABLES de ese
tipo (tantas como quieran):

```python
class TipoRegistro(Instruccion):
    """type Nombre = record campo1: tipo1; ... end;"""
    def ejecutar(self, entorno, errores, tabla):
        entorno.declarar(self.nombre, self, tipo='record-type', constante=True)

class DeclaracionRegistro(Instruccion):
    """var p: Nombre;"""
    def ejecutar(self, entorno, errores, tabla):
        definicion = entorno.buscar(self.nombre_tipo)
        valores = {c.nombre: VALORES_POR_DEFECTO.get(c.tipo) for c in definicion.campos}
        entorno.declarar(self.nombre, valores, tipo=self.nombre_tipo, constante=False)
```

Es la MISMA idea que ya usaron con `Funcion` ("declarar una función es lo
mismo que declarar una variable — se guarda en el `Entorno`") aplicada
otra vez: declarar un TIPO también es guardar algo bajo un nombre. Y
`DeclaracionRegistro` es la misma idea que `DeclaracionArreglo` de la
Sesión 4 ("crear algo lleno de valores por defecto"), con un `dict`
(campos con nombre) en vez de una `list` (posiciones numeradas).

Un registro en tiempo de ejecución es, literalmente, un diccionario de
Python. `AccesoCampo`/`AsignacionCampo` (`p.nombre`, `p.nombre := ...`)
son casi calcados a `Indexado`/`AsignacionIndexada`, cambiando "índice"
por "nombre de campo". Corran `ejemplos/08_structs.mpas` y noten que
`cumplirAnios(p)` recibe una COPIA del registro (`dict(valor)` en
`Llamada.evaluar`) — la misma regla de paso por valor que ya vieron con
arreglos, aplicada a un tipo de dato nuevo sin tener que inventar nada.

### 2. Un slice es una VISTA — y eso cambia todo lo demás

`micro/02_slices.py` es la idea central de hoy. `VistaArreglo` NO es un
`Nodo` — es un valor en tiempo de ejecución, como una lista:

```python
class VistaArreglo:
    def __init__(self, arreglo_original, inicio, fin):
        self.arreglo_original = arreglo_original   # el MISMO objeto, no una copia
        self.inicio = inicio
        self.fin = fin

    def __getitem__(self, i):
        return self.arreglo_original[self.inicio + i]

    def __setitem__(self, i, valor):
        self.arreglo_original[self.inicio + i] = valor
```

`__len__`/`__getitem__`/`__setitem__` son la parte inteligente: gracias a
esos tres métodos, `len(vista)`, `vista[i]` y `vista[i] := valor`
funcionan con la MISMA sintaxis que una lista de verdad. Por eso
`Indexado`/`AsignacionIndexada`/`length()` casi no necesitaron cambios —
revisen el diff de `ast_nodes.py` y busquen `TIPOS_INDEXABLES`.

Corran `ejemplos/09_slices.mpas` y sigan el rastro de `numeros`/`parte`:
escribir a través del slice cambia el arreglo original, y cambiar el
arreglo original se ve en el slice — porque nunca hubo dos copias de
datos, solo una. Y en la sección 5 del mismo archivo, un slice pasado a
una función **no se copia** (a diferencia de un arreglo completo):
`ponerEnCero(parte)` sí modifica `numeros` afuera. Esa es la diferencia
de fondo entre un arreglo y un slice, y por eso el enunciado insiste
tanto en que "un slice no almacena los datos".

### 3. `var nombre := expresion;` — inferencia de tipos, por una sola razón

Hasta la semana pasada, TODO `var` llevaba `: tipo` explícito. Un slice
rompe eso: no existe una palabra de tipo para "vista sobre un arreglo"
que se pueda escribir de antemano. La solución mínima:

```python
class DeclaracionInferida(Instruccion):
    """var nombre := expresion;   (sin ': tipo')"""
    def ejecutar(self, entorno, errores, tabla):
        valor = self.expresion.evaluar(entorno, errores, tabla)
        tipo = describir_tipo(valor)   # lo deriva DEL VALOR, no de una anotación
        entorno.declarar(self.nombre, valor, tipo=tipo, constante=self.constante)
```

No reemplaza la declaración con tipo explícito (`var x: integer;` sigue
existiendo) — es una forma MÁS, para el único caso que la necesitaba de
verdad. Guárdenlo en la memoria: la inferencia de tipos completa que pide
el enunciado (`let nombre = expr;` sin anotación, para CUALQUIER tipo) es
justo esta misma idea, generalizada — está en la lista de "Solo ustedes".

### 4. Tres bugs reales, encontrados escribiendo los ejemplos

Vale la pena que los vean, porque son el tipo de error que también van a
cometer ustedes:

1. **`__getitem__` sin límite propio.** La primera versión de
   `VistaArreglo` no comprobaba que el índice estuviera dentro de
   `[0, fin - inicio)` — solo delegaba directo al arreglo original. Eso
   significa que `for x in vista` (el protocolo de iteración "viejo" de
   Python) se hubiera salido del slice y seguido leyendo el arreglo
   completo. Se arregló agregando el chequeo dentro de `__getitem__`
   mismo — y de paso, `list(vista)` empezó a funcionar correctamente,
   gratis.
2. **`TablaSimbolos` mostrando un espejo en vivo, otra vez.** El mismo
   bug que ya habían encontrado y arreglado en la Sesión 4 con
   `DeclaracionArreglo` (guardar la lista compartida en vez de una copia)
   volvió a aparecer con `DeclaracionInferida` y una `VistaArreglo`: como
   nunca se tomaba una foto, la tabla mostraba el estado FINAL del
   arreglo, no el que tenía al declarar el slice. Se arregló con
   `list(valor)` en el momento de registrar — la misma solución, aplicada
   a un tipo de dato nuevo.
3. **Parámetros de función que no aceptaban un tipo record.** Al escribir
   `function cumplirAnios(persona: Persona): integer;`, la gramática de
   parámetros solo sabía de tipos primitivos y de arreglos — faltaba la
   producción `parametro : IDENTIFICADOR DOSPUNTOS IDENTIFICADOR`. Un
   caso más del patrón que ya vieron en la Sesión 4: cuando agregan un
   tipo de dato nuevo, hay que revisar TODOS los lugares donde aparece un
   tipo en la gramática (`var`, parámetros, arreglos...), no solo el
   primero que se les ocurra.

Ninguno de los tres se encontró leyendo el código: los tres aparecieron
al escribir y correr los `.mpas` de prueba. Es la razón por la que
insistimos tanto, semana tras semana, en probar con casos reales y no
solo confiar en que "se ve bien".

---

## Reportes en HTML y Django — versión condensada

### `reportes.py`

No hay ningún concepto nuevo de PLY aquí — es tomar lo que YA calculan
(`ListaErrores`, `TablaSimbolos`) y convertirlo a HTML en vez de
imprimirlo por consola:

```python
def reporte_errores_html(errores):
    filas = [... f"<td>{html.escape(error['descripcion'])}</td>" ...]
```

Fíjense en `html.escape`. La descripción de un error casi siempre repite
literalmente un pedazo del código del usuario (un nombre de variable, un
valor). Sin escaparlo, un carácter como `<` rompería el HTML generado —
o, peor, alguien podría inyectar sus propias etiquetas en la página. Esto
no es un detalle de estilo: nunca metan texto sin controlar directo
dentro de HTML.

`main.py` ya escribe `reporte.html` automáticamente en cada corrida —
ábranlo en el navegador después de correr cualquier ejemplo.

### `api/` — el endpoint más pequeño posible

Es un proyecto de Django real (`manage.py runserver` funciona tal cual),
recortado a dos rutas: la página con el `textarea`, y
`POST /api/interpretar`. La `views.py` importa `minipascal/` directo
(está afuera del proyecto de Django, como una carpeta hermana) — no
duplica ni una línea del intérprete.

La advertencia más importante de la sesión está en el propio archivo:

```python
def interpretar(request):
    entorno = Entorno()
    errores = ListaErrores()
    tabla = TablaSimbolos()
    ...
```

Estas tres se crean DENTRO de la función, en cada petición — nunca a
nivel de módulo. Un servidor atiende muchas peticiones; si las crearan
una sola vez arriba del archivo, las variables de un usuario (o de la
petición anterior del mismo usuario) se mezclarían con las de otro.

Y la segunda advertencia, menos obvia: `writeln` llama `print()` por
dentro (`ast_nodes.Writeln`), y eso escribe en la consola del SERVIDOR,
no en algo que le puedan devolver al navegador. La solución es
`contextlib.redirect_stdout`, que intercepta esas llamadas a `print()`
sin tocar una sola línea de `ast_nodes.py`:

```python
buffer_salida = io.StringIO()
with contextlib.redirect_stdout(buffer_salida):
    arbol.ejecutar(entorno, errores, tabla)
```

`settings.py` deja fuera `django.contrib.admin/auth/sessions` a
propósito, para no necesitar una base de datos ni correr
`manage.py migrate` antes de poder arrancar — su proyecto real sí va a
necesitar algunas de esas apps si guardan usuarios o archivos.

---

## Ejercicios sugeridos

Sobre `minipascal/`, en orden de dificultad:

1. Agreguen soporte para que un campo de un `record` sea de tipo
   `array[N] of T` (hoy solo acepta los 4 tipos primitivos).
2. Extiendan `DeclaracionInferida` para que también funcione con `const`
   (`const nombre := expresion;`) — es la misma clase, con `constante=True`.
3. Agreguen validación de tipos a los argumentos de una llamada (sigue
   pendiente desde la Sesión 4): que pasar un `integer` donde se espera
   un `Persona` sea un error semántico, no algo que se acepte en silencio.
4. En el endpoint de Django, agreguen el manejo correcto del token CSRF
   (`@csrf_exempt` está ahí solo para acortar este ejemplo — investiguen
   `{% csrf_token %}` y el header `X-CSRFToken`).
5. Corran `python -c "import parser"` después de cualquier cambio de
   gramática. Ya deberían tenerlo como reflejo a estas alturas.

---

## Qué falta para tu proyecto

Lo que **NO** está en este ejemplo y ustedes sí tienen que implementar:

| Falta | Dónde lo pide el enunciado | Quién lo resuelve |
|---|---|---|
| Registros anidados (un campo que sea otro record) | 3.3.12 | **Solo ustedes** |
| Operadores lógicos (`&&`, `\|\|`, `!`) con corto circuito | 3.3.7 | **Solo ustedes** |
| Retorno múltiple | 3.3.9 | **Solo ustedes** |
| `String::from`, raw strings, métodos de String completos | 3.3.11 | **Solo ustedes** |
| Validación de tipos en argumentos de función | 3.3.13 | **Solo ustedes** (ejercicio 3) |
| Inferencia de tipos general (no solo para slices) | 3.2.3 | **Solo ustedes** |
| GUI completa (editor, consola, pestañas de reportes) | 3.1.2 | **Solo ustedes** |
| Mutabilidad estilo Rust (`mut`), shadowing | 3.2.3, 3.3.2, 3.3.3 | **Solo ustedes** |
| CSRF manejado correctamente en el endpoint | — (buena práctica) | **Solo ustedes** (ejercicio 4) |

Y de sesiones anteriores, siguen sin resolver:

- Solo `+` y `<` tienen tabla de tipos (Sesiones 2-3); el resto de
  operadores opera sin validar.
- `p_error` sigue sin recuperación de errores sintácticos.
- `Repeat` no acepta etiquetas; `Case` solo admite literales enteros, uno
  por rama.
- Una función puede terminar sin pasar por ningún `return`, y no se
  reporta ni error ni advertencia.

Todos estos tienen un comentario `LO QUE FALTA AQUÍ` (o una nota
explícita) en el código.

---

## Checklist antes de entregar

Contra la sección 9 del enunciado ("Requisitos para optar a la
calificación") y el cronograma real (elaboración hasta el 28/08,
calificación 31/08–05/09):

- [ ] **Tecnología**: Python + PLY + Django/React/Angular/etc, en Linux.
      Confirmen que su proyecto corre en una máquina Linux limpia, no
      solo en la suya.
- [ ] **Commits**: todo el historial real está en GitHub — no un solo
      commit gigante al final. Si programaron en varias sesiones, eso
      debería verse en el log.
- [ ] **Manual de usuario**: instalar, crear/editar/ejecutar código, e
      interpretar los tres reportes (errores, tabla de símbolos, AST),
      con capturas de pantalla reales de SU interfaz.
- [ ] **Diagrama de clases y de flujo de procesamiento** (AST, tabla de
      símbolos) — sección 3.6, Documentación Técnica.
- [ ] **Alcance obligatorio (sección 3.5)**: operaciones aritméticas y
      lógicas, declaración de variables con TODOS los tipos, `println!`,
      localizar y ejecutar `fn main()`. Prueben esto específicamente,
      con archivos de entrada nuevos que ustedes no hayan usado antes
      para desarrollar — es la mejor forma de encontrar lo que dan por
      sentado sin darse cuenta.
- [ ] **Reportes**: errores con línea/columna, tabla de símbolos, y AST
      con Graphviz — los tres en el formato que pide su enunciado (HTML
      para los dos primeros, imagen para el AST).
- [ ] **Modificación de código en vivo**: les van a pedir que cambien
      algo de su código durante la calificación. Repasen las partes de
      su intérprete que MENOS entienden — probablemente porque las
      copiaron de algún lado sin pensarlas del todo. Esta sesión, más que
      ninguna otra, fue sobre exactamente eso: entender el mecanismo, no
      memorizar la sintaxis.

Lo que estas cinco sesiones les dieron no fue MiniPascal — fue
practicar, cinco veces seguidas, la misma pregunta: "¿qué necesito
guardar, dónde, y quién lo consulta después?". Esa pregunta no cambia
entre MiniPascal y OxigenScript. Éxitos con la entrega.
