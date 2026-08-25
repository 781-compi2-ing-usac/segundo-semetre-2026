# Interprete - Documentacion Completa

Este repositorio implementa un interprete con analisis semantico de tipos para un lenguaje de programacion propio. El sistema se divide en tres componentes principales: la gramatica (lexer + parser), el verificador de tipos (typechecker) y el interprete.

---

## 1. La Gramatica

La gramatica define la sintaxis del lenguaje. Se implementa con **PLY** (Python Lex-Yacc) en dos archivos: `mylexer.py` y `myparser.py`.

### 1.1 Lexer (`mylexer.py`)

El lexer convierte el texto fuente en una secuencia de tokens.

#### Palabras reservadas

| Token      | Palabra clave |
|------------|---------------|
| `INT`      | `int`         |
| `FLOAT`    | `float`       |
| `BOOL`     | `bool`        |
| `TRUE`     | `true`        |
| `FALSE`    | `false`       |
| `IF`       | `if`          |
| `WHILE`    | `while`       |
| `PRINT`    | `print`       |
| `FUNCTION` | `fn`          |
| `RETURN`   | `return`      |
| `VOID`     | `void`        |

#### Operadores y simbolos

| Token    | Simbolo | Descripcion          |
|----------|---------|----------------------|
| `PLUS`   | `+`     | Suma                 |
| `MINUS`  | `-`     | Resta                |
| `TIMES`  | `*`     | Multiplicacion       |
| `DIVIDE` | `/`     | Division             |
| `LT`     | `<`     | Menor que            |
| `GT`     | `>`     | Mayor que            |
| `LE`     | `<=`    | Menor o igual que    |
| `GE`     | `>=`    | Mayor o igual que    |
| `EQ`     | `==`    | Igualdad             |
| `EQUALS` | `=`     | Asignacion           |
| `LPAREN` | `(`     | Parentesis izquierdo |
| `RPAREN` | `)`     | Parentesis derecho   |
| `LKEY`   | `{`     | Llave izquierda      |
| `RKEY`   | `}`     | Llave derecha        |
| `COLON`  | `:`     | Dos puntos           |
| `COMMA`  | `,`     | Coma                 |

#### Identificadores y literales

- **Identificadores (`ID`):** `[a-zA-Z_][a-zA-Z0-9_]*`
- **Numeros (`NUM`):** `\d+(\.\d+)?` — soporta enteros (`int`) y decimales (`float`)
- Los literales `true`/`false` se convierten internamente a `True`/`False` de Python

### 1.2 Parser (`myparser.py`)

El parser construye el AST a partir de los tokens. La gramatica formal es:

```
S       : stmts

stmts   : stmt stmts | stmt

stmt    : type ID EQUALS E          (declaracion con inicializacion)
        | ID EQUALS E               (asignacion)
        | PRINT LPAREN E RPAREN     (impresion)
        | IF LPAREN E RPAREN block  (condicional)
        | WHILE LPAREN E RPAREN block (bucle)
        | FUNCTION ID LPAREN params RPAREN COLON type block (declaracion de funcion)
        | ID LPAREN args RPAREN     (llamada a funcion como statement)
        | ret_stmt                  (retorno)

ret_stmt: RETURN E | RETURN

block   : LKEY stmts RKEY

params  : params COMMA param | param | (vacio)
param   : type COLON ID

args    : args COMMA E | E | (vacio)

type    : INT | FLOAT | BOOL | VOID

E       : E PLUS E | E MINUS E | E TIMES E | E DIVIDE E   (aritmetica)
        | E LT E | E GT E | E LE E | E GE E | E EQ E     (comparacion)
        | ID                                              (variable)
        | NUM                                             (literal numerico)
        | TRUE | FALSE                                    (literal booleano)
        | LPAREN E RPAREN                                 (agrupacion)
        | ID LPAREN args RPAREN                           (llamada a funcion como expresion)
```

#### Precedencia de operadores (de menor a mayor)

1. `==` (igualdad)
2. `<`, `>`, `<=`, `>=` (comparacion)
3. `+`, `-` (adicion/sustraccion)
4. `*`, `/` (multiplicacion/division)

Todos los operadores son **asociativos por izquierda**.

---

## 2. El TypeChecker

El typechecker (`AST/Visitor/typechecker.py`) recorre el AST y verifica la consistencia de tipos antes de la ejecucion. Acumula errores en `self.errors` sin detenerse.

### 2.1 Patron Visitor (`AST/Visitor/visitor.py`)

Clase abstracta base que define un metodo `visit_*` por cada tipo de nodo AST. Tanto `TypeChecker` como `Interpreter` heredan de `Visitor` e implementan cada metodo.

### 2.2 Recorrido nodo por nodo (`typechecker.py`)

| Metodo                          | Nodo                       | Verificacion                                                                 |
|---------------------------------|----------------------------|------------------------------------------------------------------------------|
| `visit_type`                    | `TypeNode`                 | Retorna el string del tipo (`'int'`, `'float'`, `'bool'`, `'void'`)          |
| `visit_primitive`               | `PrimitiveNode`            | Retorna el tipo del literal (`node.type`)                                    |
| `visit_variable`                | `VariableNode`             | Busca el tipo en la tabla de simbolos. Error si no existe                    |
| `visit_binary_op`               | `BinaryOpNode`             | Operaciones aritmeticas: ambos operandos deben ser `int`/`float` y del mismo tipo. Comparaciones: mismo requisito, retorna `'bool'` |
| `visit_declaration`             | `DeclarationNode`          | El tipo declarado debe coincidir con el tipo de la expresion inicializadora  |
| `visit_assignment`              | `AssignmentNode`           | La variable debe existir. El tipo de la expresion debe coincidir con el tipo de la variable |
| `visit_block`                   | `BlockNode`                | Crea un nuevo scope. Visita cada statement                                   |
| `visit_print`                   | `PrintNode`                | La expresion debe ser `int`, `float`, `string`, `bool` o `void`              |
| `visit_if`                      | `IfNode`                   | La condicion debe ser de tipo `bool`                                         |
| `visit_while`                   | `WhileNode`                | La condicion debe ser de tipo `bool`                                         |
| `visit_function_declaration`    | `FunctionDeclarationNode`  | Registra `(params_types, return_type)` en la tabla. Verifica que cada `return` coincida con el tipo de retorno declarado |
| `visit_function_call`           | `FunctionCallNode`         | Verifica que la funcion exista, que el numero de argumentos coincida (aridad), y que cada argumento tenga el tipo esperado |
| `visit_param`                   | `ParamNode`                | Registra el parametro en la tabla de simbolos con su tipo                    |
| `visit_return`                  | `ReturnNode`               | Retorna el tipo de la expresion, o `'void'` si no hay expresion              |

### 2.3 Tabla de simbolos (`AST/symtable.py`)

Estructura de scope anidado con apuntadores al padre:

- **`add_symbol(name, value)`** — Agrega un simbolo al scope actual
- **`get_symbol(name)`** — Busca en el scope actual; si no existe, sube recursivamente al scope padre
- **`update_symbol(name, value)`** — Actualiza en el scope donde fue declarado; error si no existe

Cada bloque (`BlockNode`) crea un nuevo `SymTable` con `parent` apuntando al scope anterior.

### 2.4 Nodos AST (`AST/nodes.py`)

| Nodo                      | Atributos                            | Descripcion                                |
|---------------------------|--------------------------------------|--------------------------------------------|
| `Node`                    | `value`                              | Clase base                                   |
| `TypeNode`                | `value` (string del tipo)            | Representa un tipo (`int`, `float`, `bool`, `void`) |
| `PrimitiveNode`           | `value`, `type`                      | Literal numerico o booleano                  |
| `VariableNode`            | `name`                               | Referencia a una variable                    |
| `BinaryOpNode`            | `left`, `op`, `right`                | Operacion binaria (aritmetica o comparacion) |
| `DeclarationNode`         | `var_type`, `var_name`, `expression` | Declaracion con tipo e inicializacion opcional |
| `AssignmentNode`          | `var_name`, `expression`             | Reasignacion de variable                     |
| `BlockNode`               | `statements` (lista)                 | Bloque de sentencias entre `{}`              |
| `PrintNode`               | `expression`                         | Impresion de una expresion                   |
| `IfNode`                  | `condition`, `block`                 | Condicional                                  |
| `WhileNode`               | `condition`, `block`                 | Bucle                                        |
| `FunctionDeclarationNode` | `func_name`, `parameters`, `return_type`, `block` | Declaracion de funcion       |
| `FunctionCallNode`        | `func_name`, `arguments`             | Llamada a funcion                            |
| `ParamNode`               | `param_type`, `param_name`           | Parametro de funcion                         |
| `ReturnNode`              | `expression` (opcional)              | Sentencia return                             |

---

## 3. El Interprete

El interprete (`AST/Visitor/interpreter.py`) ejecuta el AST despues de que el typechecker valida los tipos.

### 3.1 Recorrido nodo por nodo (`interpreter.py`)

| Metodo                          | Nodo                       | Ejecucion                                                                 |
|---------------------------------|----------------------------|---------------------------------------------------------------------------|
| `visit_type`                    | `TypeNode`                 | Retorna el string del tipo                                                |
| `visit_primitive`               | `PrimitiveNode`            | Retorna el valor Python (`int`, `float`, `bool`)                           |
| `visit_variable`                | `VariableNode`             | Busca el valor en la tabla de simbolos                                    |
| `visit_binary_op`               | `BinaryOpNode`             | Evalua `left` y `right`, aplica el operador: `+`, `-`, `*`, `/`, `<`, `>`, `<=`, `>=`, `==` |
| `visit_declaration`             | `DeclarationNode`          | Evalua la expresion y registra el valor en la tabla. Si no hay expresion, registra `None` |
| `visit_assignment`              | `AssignmentNode`           | Evalua la expresion y actualiza el valor en la tabla                      |
| `visit_block`                   | `BlockNode`                | Crea un nuevo scope (`SymTable` hijo). Ejecuta cada statement. Si alguno retorna `FlowControl`, lo propaga hacia arriba |
| `visit_print`                   | `PrintNode`                | Evalua la expresion y llama a `print()` de Python                         |
| `visit_if`                      | `IfNode`                   | Evalua la condicion. Si es verdadera, ejecuta el bloque. Propaga `FlowControl` si existe |
| `visit_while`                   | `WhileNode`                | Mientras la condicion sea verdadera, ejecuta el bloque. Propaga `FlowControl` si existe |
| `visit_function_declaration`    | `FunctionDeclarationNode`  | Crea un objeto `Foreign` con el closure del scope actual y lo registra en la tabla |
| `visit_function_call`           | `FunctionCallNode`         | Busca la funcion en la tabla, verifica que sea `Foreign`, y llama a `invoke()` |
| `visit_param`                   | `ParamNode`                | Retorna el nombre del parametro (solo se usa para construir la lista de params) |
| `visit_return`                  | `ReturnNode`               | Evalua la expresion y retorna un objeto `Return(value)` (senal de control de flujo) |

### 3.2 Control de flujo (`AST/flow.py`)

```
FlowControl        → clase base (senales de control de flujo)
  └── Return       → encapsula el valor retornado por una funcion
```

Cuando un `ReturnNode` se ejecuta, retorna un objeto `Return(value)`. Los metodos `visit_block`, `visit_if` y `visit_while` detectan esta senal con `isinstance(result, FlowControl)` y la propagan hacia arriba, permitiendo que el valor llegue de vuelta a `visit_function_call`.

### 3.3 Estructuras de soporte (`AST/Structures/`)

#### `invokable.py` — Interfaz abstracta

```python
class Invokable(ABC):
    get_arity()    → retorna la cantidad de parametros
    invoke()       → ejecuta la funcion
```

#### `foreign.py` — Funcion definida por el usuario

`Foreign` extiende `Invokable` y representa una funcion declarada en el lenguaje. Al momento de invocarla:

1. Crea un nuevo `SymTable` hijo del closure donde fue definida la funcion
2. Vincula cada parametro con su argumento evaluado
3. Ejecuta el bloque de la funcion
4. Si el resultado es un `Return`, extrae y retorna `result.value`
5. Restaura la tabla de simbolos anterior

Esto implementa **closure**: la funcion captura el scope en el momento de su declaracion.

---

## 4. Ejemplo: `sum`, `fact`, `div`

```
fn sum(int: a, int: b) : int {
    return a + b
}

fn fact(int: n) : int{
    if (n == 0) {
        return 1
    }
    return n*fact(n-1)
}

fn div(int: a,int: b) : int{
    if (a == 0) {
        return 0
    }
    return div(a-b,b) + 1
}

print(sum(2,3))

print(fact(5))

print(div(100,2)) 
```

### Funcion `sum(int: a, int: b) : int`

Suma dos enteros y retorna el resultado. Ejemplo: `sum(2, 3)` retorna `5`.

### Funcion `fact(int: n) : int`

Calcula el **factorial** de `n` mediante recursion:

- **Caso base:** si `n == 0`, retorna `1`
- **Paso recursivo:** retorna `n * fact(n-1)`
- Ejemplo: `fact(5)` = `5 * 4 * 3 * 2 * 1` = `120`

### Funcion `div(int: a, int: b) : int`

Calcula la **division entera** de `a / b` mediante restas sucesivas (sin usar el operador `/`):

- **Caso base:** si `a == 0`, retorna `0`
- **Paso recursivo:** retorna `div(a-b, b) + 1` — resta `b` de `a` y suma 1 al contador
- Ejemplo: `div(100, 2)` = `50` (resta 2 cien veces... no, resta 2 de 100 cincuenta veces hasta llegar a 0)

### Llamadas `print`

```
print(sum(2,3))     → 5
print(fact(5))      → 120
print(div(100,2))   → 50
```

### Flujo de ejecucion

1. El parser genera el AST con 6 nodos: 3 `FunctionDeclarationNode` + 3 `FunctionCallNode` (dentro de `PrintNode`)
2. El **typechecker** verifica que todas las funciones tengan tipos consistentes, que los argumentos coincidan, y que los `return` tengan el tipo correcto
3. El **interprete** registra las 3 funciones como objetos `Foreign` en la tabla de simbolos, luego ejecuta cada `print`, invocando las funciones recursivamente

---

## 5. Interfaz Web (`app.py`)

La aplicacion es un servidor **Flask** que expone una API REST para ejecutar codigo en el lenguaje.

### Endpoint `POST /compile`

Recibe codigo fuente en formato JSON y retorna los resultados.

#### Request

```json
{
    "code": "fn sum(int: a, int: b) : int { return a + b }\nprint(sum(2,3))"
}
```

#### Response (exito)

```json
{
    "errors": [],
    "output": ["5"]
}
```

#### Response (error de tipos)

```json
{
    "errors": ["Type mismatch in binary operation: int and string"],
    "output": []
}
```

### Flujo interno

```
┌─────────────┐
│ POST /compile│
│  (codigo)    │
└──────┬──────┘
       │
       v
┌──────────────┐
│   Parser     │ → parser.parse(code) → AST (lista de nodos)
└──────┬───────┘
       │
       v
┌──────────────┐
│ TypeChecker  │ → recorre cada nodo del AST
│              │ → si hay errores, los retorna y se detiene
└──────┬───────┘
       │ (sin errores)
       v
┌──────────────┐
│ Interpreter  │ → recorre cada nodo del AST
│              │ → captura stdout con redirect_stdout
└──────┬───────┘
       │
       v
┌──────────────┐
│  Response    │ → JSON con {"errors": [], "output": [...]}
└──────────────┘
```

Pasos detallados:

1. **Parseo:** `parser.parse(code)` convierte el texto en una lista de nodos AST
2. **Typechecking:** Se crea un `TypeChecker` y se visita cada nodo. Si `checker.errors` no esta vacio, se retorna inmediatamente con los errores
3. **Interpretacion:** Se crea un `Interpreter`, se captura `stdout` con `StringIO` + `redirect_stdout`, y se visita cada nodo
4. **Respuesta:** La salida capturada se divide por lineas y se retorna como JSON

### Uso desde la interfaz

La aplicacion Flask sirve una pagina HTML en `GET /` (template `templates/index.html`) que contiene un editor de codigo. El usuario escribe codigo en el lenguaje, lo envia al endpoint `/compile`, y la respuesta se muestra en pantalla con los errores y la salida.
