"""
MiniPascal v2 — Entorno (Environment).

Es la misma idea de micro/01_entorno.py (diccionario + puntero al padre),
con dos diferencias para que sirva de verdad dentro del intérprete:

  1. Cada variable guarda, además del valor, si es CONSTANTE. Sin esto no
     se puede detectar "modificación de una variable inmutable"
     (el equivalente de su regla sin `mut`).
  2. `asignar` y `buscar` YA NO validan nada ni reportan errores: asumen
     que quien los llama (un nodo del AST) ya comprobó `existe(nombre)` y
     `es_constante(nombre)` ANTES de llamarlos. La razón es de diseño: solo
     el nodo del AST (`Asignacion`, `Variable`) tiene la línea y columna
     para reportar un buen mensaje de error. `Entorno` no las tiene, así
     que no es quien debe decidir qué decirle al usuario — solo guarda y
     entrega valores.

Por eso el patrón de uso, en un nodo del AST, se ve así:

    if not entorno.existe(nombre):
        errores.agregar('Semántico', f"'{nombre}' no ha sido declarada.",
                         linea, columna)
    elif entorno.es_constante(nombre):
        errores.agregar('Semántico', f"'{nombre}' es inmutable.",
                         linea, columna)
    else:
        entorno.asignar(nombre, valor)

Primero se pregunta, después se actúa. Nunca se actúa "a ciegas" y se
espera la excepción.
"""


class Entorno:

    def __init__(self, padre=None):
        # Cada entrada guarda un pequeño diccionario, no solo el valor,
        # para poder recordar si la variable es constante y (más adelante)
        # su tipo declarado.
        self.variables = {}
        self.padre = padre

    def declarar(self, nombre, valor, tipo=None, constante=False):
        # `declarar` SIEMPRE crea la variable en ESTE entorno, nunca en el
        # padre — igual que en el micro-ejemplo. Así es como funciona el
        # sombreo (shadowing) y el cierre de ámbito al salir de un bloque.
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
        """Cambia el valor de una variable que YA EXISTE y YA SE SABE mutable.

        No repite esas dos comprobaciones (existe / no es constante):
        esa decisión, y el mensaje de error si falla, le toca al nodo del
        AST que sí conoce la línea y columna donde ocurrió.
        """
        if nombre in self.variables:
            self.variables[nombre]['valor'] = valor
            return
        # Si esto revienta, es un bug DE USTEDES (llamaron a asignar sin
        # comprobar existe() antes), no un error del usuario del lenguaje.
        self.padre.asignar(nombre, valor)

    def buscar(self, nombre):
        """Valor de la variable. Asume que ya comprobaron `existe(nombre)`."""
        if nombre in self.variables:
            return self.variables[nombre]['valor']
        return self.padre.buscar(nombre)


if __name__ == '__main__':
    # Mismo escenario del micro-ejemplo, pero ahora usando `existe` y
    # `es_constante` ANTES de actuar, como lo va a hacer el nodo Asignacion.

    def asignar_con_validacion(entorno, nombre, valor):
        """Simula lo que un nodo Asignacion.ejecutar va a hacer."""
        if not entorno.existe(nombre):
            print(f"  [Error Semántico] '{nombre}' no ha sido declarada.")
            return
        if entorno.es_constante(nombre):
            print(f"  [Error Semántico] '{nombre}' es inmutable, no se puede modificar.")
            return
        entorno.asignar(nombre, valor)
        print(f"  OK: {nombre} = {valor}")

    global_ = Entorno()
    global_.declarar('total', 100, tipo='integer', constante=False)
    global_.declarar('PI', 3.14, tipo='real', constante=True)

    print("Intentando modificar una variable mutable:")
    asignar_con_validacion(global_, 'total', 200)

    print("\nIntentando modificar una constante:")
    asignar_con_validacion(global_, 'PI', 3.0)

    print("\nIntentando modificar algo que no existe:")
    asignar_con_validacion(global_, 'fantasma', 1)

    print(f"\nEstado final: total={global_.buscar('total')}, PI={global_.buscar('PI')}")

    # ---------------------------------------------------------------
    # Para su proyecto: el enunciado (sección 3.4.1) trae EXACTAMENTE
    # estos dos mensajes como ejemplo:
    #
    #   [Error Semántico] La variable 'total' no ha sido declarada.
    #   [Error Semántico] No es posible modificar una variable inmutable.
    #
    # Fíjense que aquí ya salen en el orden correcto (primero existe,
    # después es_constante) y sin que el programa se detenga: la
    # ejecución sigue después de cada error, que es justo lo que pide la
    # "Resiliencia durante la ejecución" del enunciado.
    # ---------------------------------------------------------------
