# 05 — Structs y tipos → ARM64 (pendiente de emisión)

```bnf
struct_dcl ::= RESERVEDSTRUCT ID LLAVE_OPEN campos_struct LLAVE_CIERRA PUNTOCOMA
campo ::= ID DOBDOT tipo
init_struct_dcl ::= ID LLAVE_OPEN init_campos_struct LLAVE_CIERRA
init_campo ::= ID IGUAL expresion
tipo ::= TIPOENTERO | FLOAT
```

Hoy solo existe semántica en el intérprete (`visit_struct_dcl` guarda `dict` campo→tipo, `visit_init_struct` guarda `dict` campo→valor). Sin tiling emitido aún.

Diseño propuesto: struct = bloque contiguo en `.data`, un slot de 8 bytes por campo, offset = índice*8 registrado en la tabla de símbolos.

```asm
// struct Punto {x: int, y: int};  → offsets x=0, y=8
// Punto{x=1, y=2}:
<1> → x9 ; ldr x14, =instancia ; str x9, [x14, #0]
<2> → x9 ; ldr x14, =instancia ; str x9, [x14, #8]
// acceso instancia.y:
ldr x14, =instancia
ldr x9, [x14, #8]
```
