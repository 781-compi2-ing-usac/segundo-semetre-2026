"""
MiniPascal v4 — Entorno (Environment).

Mismo diccionario + puntero al padre de la Sesión 2. Una novedad esta
semana: `ambito`, el nombre de la función donde vive este entorno (o
'programa' si no hay ninguna). Se hereda del padre automáticamente, así
que un `if` o un `while` anidados DENTRO de una función siguen sabiendo en
qué función están, sin que cada uno tenga que repetirlo. Esto resuelve el
hueco que quedó marcado en el README de la Sesión 3: `TablaSimbolos` ya no
va a registrar todo como 'programa'.

La otra pieza que hace falta para que las funciones funcionen —de dónde
"cuelga" el entorno de activación de una llamada— NO vive aquí. Vive en
`Funcion` (ast_nodes.py): cada función recuerda el entorno donde fue
DECLARADA (`entorno_definicion`), y una llamada cuelga su entorno de
activación de ESE, nunca del entorno de quien llama. Es el mismo mecanismo
que un cierre (closure) en Python o JavaScript. Ver
micro/01_entornos_activacion.py antes de leer `Llamada`.
"""


class Entorno:

    def __init__(self, padre=None, ambito=None):
        self.variables = {}
        self.padre = padre
        # Si no nos dan un ámbito nuevo explícito, heredamos el del padre.
        # Solo una Llamada (al crear el entorno de activación de una
        # función) pasa `ambito` de verdad; Bloque, If, While, etc. dejan
        # que se herede solo.
        if ambito is not None:
            self.ambito = ambito
        elif padre is not None:
            self.ambito = padre.ambito
        else:
            self.ambito = 'programa'

    def declarar(self, nombre, valor, tipo=None, constante=False):
        self.variables[nombre] = {
            'valor': valor,
            'tipo': tipo,
            'constante': constante,
        }

    def existe(self, nombre):
        """¿'nombre' está declarado aquí o en algún entorno padre?"""
        if nombre in self.variables:
            return True
        if self.padre is not None:
            return self.padre.existe(nombre)
        return False

    def es_constante(self, nombre):
        """Asume que ya llamaron `existe(nombre)` y dio True."""
        if nombre in self.variables:
            return self.variables[nombre]['constante']
        return self.padre.es_constante(nombre)

    def tipo_de(self, nombre):
        """Tipo declarado de la variable. Asume que ya comprobaron `existe`."""
        if nombre in self.variables:
            return self.variables[nombre]['tipo']
        return self.padre.tipo_de(nombre)

    def asignar(self, nombre, valor):
        """Cambia el valor de una variable que YA EXISTE y YA SE SABE mutable."""
        if nombre in self.variables:
            self.variables[nombre]['valor'] = valor
            return
        self.padre.asignar(nombre, valor)

    def buscar(self, nombre):
        """Valor de la variable (o de la función, si `nombre` es una función:
        ver `Funcion` en ast_nodes.py — se guarda con el mismo mecanismo)."""
        if nombre in self.variables:
            return self.variables[nombre]['valor']
        return self.padre.buscar(nombre)


if __name__ == '__main__':
    # Mismo demo de la Sesión 2, más una prueba rápida de `ambito`.

    global_ = Entorno()
    global_.declarar('total', 100, tipo='integer', constante=False)
    print(f"Entorno global: ambito={global_.ambito!r}")

    # Un bloque anidado (if/while) hereda el ámbito del padre sin que se lo
    # digamos explícitamente.
    bloque_anidado = Entorno(padre=global_)
    print(f"Entorno de un bloque anidado en 'programa': ambito={bloque_anidado.ambito!r}")

    # Un entorno de activación de función SÍ recibe un ámbito nuevo. De
    # dónde cuelga (`padre=`) es la parte delicada — ver
    # micro/01_entornos_activacion.py y `Funcion`/`Llamada` en
    # ast_nodes.py: NO cuelga de "quien llama", cuelga del entorno donde
    # la función fue DECLARADA.
    activacion = Entorno(padre=global_, ambito='miFuncion')
    print(f"Entorno de activación de 'miFuncion': ambito={activacion.ambito!r}, "
          f"padre es el entorno de definición: {activacion.padre is global_}")

    # ---------------------------------------------------------------
    # Para su proyecto: cada llamada a función necesita colgar su entorno
    # de activación del entorno donde la función fue DECLARADA, no del
    # entorno de quien la está llamando en este momento. Si usan
    # Entorno(padre=entorno_de_quien_llama), van a tener scoping DINÁMICO
    # sin querer, y variables locales de quien llama se van a "colar"
    # dentro de la función llamada. Es un bug silencioso: el programa
    # corre, pero da resultados incorrectos solo en casos específicos de
    # anidamiento — justo el tipo de bug que cuesta horas de depuración.
    # ---------------------------------------------------------------
