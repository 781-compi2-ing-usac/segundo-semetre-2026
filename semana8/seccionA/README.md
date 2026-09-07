# Interprete - Documentacion Completa

Este repositorio implementa un interprete con analisis semantico de tipos para un lenguaje de programacion propio. El sistema se divide en cuatro componentes principales: la gramatica (lexer + parser), el verificador de tipos (typechecker), el interprete y el compilador a LLVM IR.

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

| Token       | Simbolo | Descripcion          |
|-------------|---------|----------------------|
| `PLUS`      | `+`     | Suma                 |
| `MINUS`     | `-`     | Resta                |
| `TIMES`     | `*`     | Multiplicacion       |
| `DIVIDE`    | `/`     | Division             |
| `LT`        | `<`     | Menor que            |
| `GT`        | `>`     | Mayor que            |
| `LE`        | `<=`    | Menor o igual que    |
| `GE`        | `>=`    | Mayor o igual que    |
| `EQ`        | `==`    | Igualdad             |
| `AMPERSAND` | `&`     | AND lógico           |
| `PIPE`      | `\|`    | OR lógico            |
| `EQUALS`    | `=`     | Asignacion           |
| `LPAREN`    | `(`     | Parentesis izquierdo |
| `RPAREN`    | `)`     | Parentesis derecho   |
| `LKEY`      | `{`     | Llave izquierda      |
| `RKEY`      | `}`     | Llave derecha        |
| `COLON`     | `:`     | Dos puntos           |
| `COMMA`     | `,`     | Coma                 |

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

E       : E AMPERSAND E | E PIPE E                        (logica)
        | E PLUS E | E MINUS E | E TIMES E | E DIVIDE E   (aritmetica)
        | E LT E | E GT E | E LE E | E GE E | E EQ E     (comparacion)
        | ID                                              (variable)
        | NUM                                             (literal numerico)
        | TRUE | FALSE                                    (literal booleano)
        | LPAREN E RPAREN                                 (agrupacion)
        | ID LPAREN args RPAREN                           (llamada a funcion como expresion)
```

#### Precedencia de operadores (de menor a mayor)

1. `&`, `|` (operadores logicos)
2. `==` (igualdad)
3. `<`, `>`, `<=`, `>=` (comparacion)
4. `+`, `-` (adicion/sustraccion)
5. `*`, `/` (multiplicacion/division)

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
| `visit_arith_op`                | `ArithOpNode`              | Operaciones aritmeticas: ambos operandos deben ser `int`/`float` y del mismo tipo. Retorna el tipo de los operandos |
| `visit_rel_op`                  | `RelOpNode`                | Operaciones relacionales: ambos operandos deben ser `int`/`float` y del mismo tipo. Retorna `'bool'` |
| `visit_logic_op`                | `LogicOpNode`              | Operaciones logicas (`&`, `\|`): ambos operandos deben ser `bool`. Retorna `'bool'` |
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
| `ArithOpNode`             | `left`, `op`, `right`                | Operacion aritmetica (`+`, `-`, `*`, `/`)    |
| `RelOpNode`               | `left`, `op`, `right`                | Operacion relacional (`<`, `>`, `<=`, `>=`, `==`) |
| `LogicOpNode`             | `left`, `op`, `right`                | Operacion logica (`&`, `\|`)                 |
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
| `visit_arith_op`                | `ArithOpNode`              | Evalua `left` y `right`, aplica el operador: `+`, `-`, `*`, `/`           |
| `visit_rel_op`                  | `RelOpNode`                | Evalua `left` y `right`, aplica el operador: `<`, `>`, `<=`, `>=`, `==`. Retorna `bool` |
| `visit_logic_op`                | `LogicOpNode`              | Evalua `left` y `right`, aplica el operador: `&` (and), `\|` (or). Retorna `bool` |
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

---

## 6. Compilador a LLVM IR

El compilador (`AST/Visitor/compiler.py`) genera codigo LLVM IR o ensamblador ARM64 a partir del AST despues de que el typechecker valida los tipos. Utiliza el patron Builder para construir las instrucciones, permitiendo intercambiar el backend de generacion de codigo.

### 6.1 Instalacion de dependencias

**Para LLVM IR (archivo .ll):**
```bash
sudo apt update
sudo apt install -y llvm qemu-user gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu
```

**Para ARM64 (archivo .asm):**
```bash
sudo apt install -y qemu-user binutils-aarch64-linux-gnu
```

### 6.2 Mini tutorial: Compilar y ejecutar

#### Opcion A: LLVM IR

1. **Generar el codigo LLVM IR** desde la interfaz web o API:
   ```bash
   curl -X POST http://localhost:5000/compile \
     -H "Content-Type: application/json" \
     -d '{"code": "int x = 5\nprint(x + 3)"}'
   ```

2. **Guardar la salida** en un archivo `.ll`:
   ```bash
   echo '<codigo LLVM IR>' > programa.ll
   ```

3. **Compilar con el script** `LLVM/build.sh`:
   ```bash
   ./LLVM/build.sh programa.ll
   ```

   El script realiza 4 pasos:
   - `llc`: Convierte LLVM IR a assembly ARM64
   - `as`: Ensambla el codigo a objeto
   - `gcc`: Linkea el objeto a ejecutable
   - `qemu`: Ejecuta el binario con QEMU

#### Opcion B: ARM64 directo

1. **Generar el codigo ensamblador** desde Python:
   ```python
   from myparser import parser
   from AST.Visitor.typechecker import TypeChecker
   from AST.Visitor.compiler import Compiler
   from AST.Builder.arm_builder import ARMBuilder

   code = 'int x = 10\nint y = 5\nprint(x + y)'
   ast = parser.parse(code)
   
   checker = TypeChecker()
   for node in ast:
       checker.dispatch(node)
   
   builder = ARMBuilder()
   compiler = Compiler(builder)
   for node in ast:
       compiler.dispatch(node)
   
   with open('programa.asm', 'w') as f:
       f.write(compiler.get_code())
   ```

2. **Compilar con el script** `ARM/build.sh`:
   ```bash
   ./ARM/build.sh programa.asm
   ```

   El script realiza 3 pasos:
   - `as`: Ensambla el codigo a objeto
   - `ld`: Linkea el objeto a ejecutable
   - `qemu`: Ejecuta el binario con QEMU

### 6.3 Clases del compilador

#### `Compiler` (`AST/Visitor/compiler.py`)

El `Compiler` es un visitor que recorre el AST y utiliza un `TACBuilder` para generar LLVM IR.

| Metodo | Nodo | Accion |
|--------|------|--------|
| `visit_primitive` | `PrimitiveNode` | Retorna el valor literal (ej: `5`, `3.14`) |
| `visit_variable` | `VariableNode` | Genera `load` desde el puntero de la variable |
| `visit_arith_op` | `ArithOpNode` | Genera instruccion aritmetica (`add`, `sub`, `mul`, `sdiv` para int; `fadd`, `fsub`, `fmul`, `fdiv` para float) |
| `visit_rel_op` | `RelOpNode` | Genera comparacion (`icmp`/`fcmp`) y branch condicional. Retorna listas de etiquetas `(ev_labels, ef_labels)` |
| `visit_logic_op` | `LogicOpNode` | Para `&`: escribe EV izquierdo, evalua derecho, concatena EF. Para `\|`: escribe EF izquierdo, evalua derecho, concatena EV |
| `visit_if` | `IfNode` | Escribe etiquetas EV, ejecuta bloque, escribe etiquetas EF con branches al final |
| `visit_while` | `WhileNode` | Escribe etiqueta de inicio, evalua condicion, escribe etiquetas EV, ejecuta bloque, branch al inicio, escribe etiquetas EF |
| `visit_declaration` | `DeclarationNode` | Genera `alloca` para reservar espacio + `store` si hay inicializacion. Si la expresion es RelOp/LogicOp, materializa a variable |
| `visit_assignment` | `AssignmentNode` | Genera `store` para actualizar la variable. Si la expresion es RelOp/LogicOp, materializa a variable |
| `visit_print` | `PrintNode` | Genera llamada a `printf` con el formato apropiado segun el tipo. Si la expresion es RelOp/LogicOp, materializa a print |
| `visit_block` | `BlockNode` | Visita cada statement en secuencia |

#### `TACBuilder` (`AST/Builder/tac_builder.py`)

El `TACBuilder` implementa el patron Builder para generar instrucciones LLVM IR.

| Metodo | Descripcion |
|--------|-------------|
| `new_temp()` | Genera un nuevo temporal (`%t1`, `%t2`, ...) |
| `emit(instruction)` | Agrega una instruccion al codigo |
| `emit_global(declaration)` | Agrega una declaracion global (format strings) |
| `get_type_llvm(type_name)` | Convierte tipos del lenguaje a LLVM (`int` → `i32`, `float` → `double`, `bool` → `i1`) |
| `emit_main_header()` | Genera el header de `main()` con declaraciones de printf y formatos |
| `emit_main_footer()` | Genera el footer con `ret i32 0` |
| `emit_alloca(var_name, type)` | Genera `alloca` para variable y retorna el puntero |
| `build_arithmetic(op, rd, rs1, rs2, type)` | Genera instruccion aritmetica |
| `build_memory_store(rd, base, type)` | Genera `store` |
| `build_memory_load(rd, base, type)` | Genera `load` |
| `build_print(value, type)` | Genera llamada a `printf` segun el tipo |

#### `ARMBuilder` (`AST/Builder/arm_builder.py`)

El `ARMBuilder` implementa el mismo patron Builder pero para generar codigo ensamblador ARM64.

| Metodo | Descripcion |
|--------|-------------|
| `emit_main_header()` | Genera `.global _start`, seccion `.bss` para buffer, y prologo con `stp`/`mov` para frame pointer |
| `emit_main_footer()` | Genera syscall `exit(0)` y la rutina `itoa` para convertir enteros a string |
| `emit_alloca(var_name, type)` | Reserva espacio usando offsets desde el Frame Pointer (x29) |
| `build_arithmetic(op, rd, rs1, rs2, type)` | Genera `add`, `sub`, `mul`, `sdiv` |
| `build_memory_store(rd, base, offset, type)` | Genera `str` con offset desde FP |
| `build_memory_load(rd, base, offset, type)` | Genera `ldr` con offset desde FP |
| `build_print(value, type)` | Usa rutina `itoa` + syscall `write(64)` para imprimir |

**Registros ARM64 utilizados:**

| Registro | Nombre | Uso |
|----------|--------|-----|
| x0-x7 | A0-A7 | Argumentos / temporales |
| x8 | SYS | Numero de syscall |
| x9-x15 | T0-T6 | Temporales |
| x19-x28 | S1-S10 | Saved registers |
| x29 | FP | Frame Pointer |
| x30 | RA | Return Address |
| sp | SP | Stack Pointer |

**Syscalls utilizados:**

| Numero | Syscall | Uso |
|--------|---------|-----|
| 64 | write | Imprimir a stdout |
| 93 | exit | Terminar programa |

**Manejo de variables:**

Las variables se almacenan en el stack usando offsets negativos desde el Frame Pointer:
```asm
// Declaracion: int x = 10
mov x9, #10              // Cargar literal en registro
str x9, [x29, #-8]       // Almacenar en [FP-8]

// Uso: print(x)
ldr x10, [x29, #-8]      // Cargar desde [FP-8]
```

#### Intercambio de Builders

El `Compiler` acepta cualquier `Builder` en su constructor, permitiendo intercambiar el backend de generacion de codigo:

```python
from AST.Visitor.compiler import Compiler
from AST.Builder.tac_builder import TACBuilder
from AST.Builder.arm_builder import ARMBuilder

# Para LLVM IR
builder = TACBuilder()
compiler = Compiler(builder)

# Para ARM64
builder = ARMBuilder()
compiler = Compiler(builder)
```

**Compilar y ejecutar ARM64:**

```bash
# Generar el archivo .asm desde Python
python3 -c "
from myparser import parser
from AST.Visitor.typechecker import TypeChecker
from AST.Visitor.compiler import Compiler
from AST.Builder.arm_builder import ARMBuilder

code = 'int x = 10\nprint(x + 5)'
ast = parser.parse(code)
checker = TypeChecker()
for node in ast:
    checker.dispatch(node)

builder = ARMBuilder()
compiler = Compiler(builder)
for node in ast:
    compiler.dispatch(node)

with open('programa.asm', 'w') as f:
    f.write(compiler.get_code())
"

# Compilar y ejecutar
./ARM/build.sh programa.asm
```

**Requisitos para ARM64:**
```bash
sudo apt install -y qemu-user gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu
```

#### Soporte para Floats en ARM

Actualmente el `ARMBuilder` solo soporta `int`. Para agregar soporte de `float`:

**Dificultad estimada:** Media

**Cambios necesarios:**
1. Usar registros de punto flotante (`d0`-`d31`) en lugar de `x0`-`x30`
2. Instrucciones `fadd`, `fsub`, `fmul`, `fdiv` en lugar de `add`, `sub`, `mul`, `sdiv`
3. Implementar rutina `ftoa` (float to ASCII) mas compleja que `itoa`
4. Manejar precision doble (64 bits) con registros `d` (double)

**Ejemplo de codigo ARM para float:**
```asm
// fadd d0, d1, d2  (suma de doubles)
// fdiv d0, d1, d2  (division de doubles)
```

Por ahora, si se intenta compilar codigo con `float` usando `ARMBuilder`, se lanzara `NotImplementedError`.

### 6.4 Manejo de entornos a bajo nivel

El compilador maneja las variables mediante punteros en memoria:

1. **Declaracion de variable** (`int x = 5`):
   ```llvm
   %x_ptr = alloca i32          ; Reserva 4 bytes en el stack
   store i32 5, ptr %x_ptr      ; Guarda el valor 5
   ```

2. **Uso de variable** (`print(x + 3)`):
   ```llvm
   %t1 = load i32, ptr %x_ptr   ; Carga el valor de x
   %t2 = add i32 %t1, 3         ; Suma 3
   call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 %t2)
   ```

3. **Format strings globales**:
   ```llvm
   @.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
   @.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
   @.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"
   ```

### 6.5 Ejemplo: Operaciones aritméticas

Codigo fuente:
```
int x = 10
int y = 5
print(x + y)
print(x * y)
```

LLVM IR generado:
```llvm
@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    %x_ptr = alloca i32
    store i32 10, ptr %x_ptr
    %y_ptr = alloca i32
    store i32 5, ptr %y_ptr
    %t1 = load i32, ptr %x_ptr
    %t2 = load i32, ptr %y_ptr
    %t3 = add i32 %t1, %t2
    call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 %t3)
    %t4 = load i32, ptr %x_ptr
    %t5 = load i32, ptr %y_ptr
    %t6 = mul i32 %t4, %t5
    call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 %t6)
    ret i32 0
}
```

Salida al ejecutar:
```
15
50
```
