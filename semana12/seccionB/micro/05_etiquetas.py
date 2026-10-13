"""
MICRO-EJEMPLO 5: etiquetas únicas y la pila de ciclos. Sin PLY.

Un `if` o un `while` se vuelven etiquetas y saltos. Eso plantea dos
preguntas, y este archivo contesta las dos con el árbol más chiquito
posible (tuplas de Python, no nodos de verdad):

    1. ¿Cómo se evita que dos `if` distintos usen el mismo nombre de
       etiqueta?
    2. Cuando aparece un `break`, ¿a qué etiqueta salta? Depende de en
       qué ciclo está, y el generador solo ve un nodo a la vez.

Correr con: python3 05_etiquetas.py
"""


# ===========================================================================
# El programa de juguete
# ===========================================================================
#
#   while A do begin
#       if B then begin break; end;
#       while C do begin
#           if D then begin break; end;
#       end;
#   end;

PROGRAMA = ('while', 'A', [
    ('if', 'B', [('break',)]),
    ('while', 'C', [
        ('if', 'D', [('break',)]),
    ]),
])


# ===========================================================================
# Intento 1 — nombres fijos
# ===========================================================================

def generar_con_nombres_fijos(nodo, salida):
    tipo = nodo[0]
    if tipo == 'while':
        salida.append('while_inicio:')
        for hijo in nodo[2]:
            generar_con_nombres_fijos(hijo, salida)
        salida.append('while_fin:')
    elif tipo == 'if':
        for hijo in nodo[2]:
            generar_con_nombres_fijos(hijo, salida)
        salida.append('if_fin:')


print("--- Intento 1: la misma etiqueta para cada if y cada while ---")
salida = []
generar_con_nombres_fijos(PROGRAMA, salida)
for linea in salida:
    print("   ", linea)

repetidas = sorted({e for e in salida if salida.count(e) > 1})
print(f"\nEtiquetas repetidas: {repetidas}")
print("El ensamblador las rechaza: Error: symbol `.Lfin' is already defined\n")


# ===========================================================================
# Intento 2 — un contador que solo sube
# ===========================================================================
#
# Es lo que hace `nueva_etiqueta` en generador_arm.py. No hace falta nada
# más inteligente: basta con que el número nunca se repita.

class Generador:
    def __init__(self):
        self.contador = 0
        self.salida = []
        self.ciclos = []          # pila: el ciclo más interno va al final

    def nueva_etiqueta(self, prefijo):
        self.contador += 1
        return f'.L{prefijo}_{self.contador}'

    def generar(self, nodo):
        tipo = nodo[0]

        if tipo == 'while':
            inicio = self.nueva_etiqueta('while_inicio')
            fin = self.nueva_etiqueta('while_fin')
            self.ciclos.append({'inicio': inicio, 'fin': fin})   # ABRIR
            self.salida.append(f'{inicio}:')
            for hijo in nodo[2]:
                self.generar(hijo)
            self.salida.append(f'    b {inicio}')
            self.salida.append(f'{fin}:')
            self.ciclos.pop()                                    # CERRAR

        elif tipo == 'if':
            fin = self.nueva_etiqueta('if_fin')
            self.salida.append(f'    (si no se cumple {nodo[1]}) b {fin}')
            for hijo in nodo[2]:
                self.generar(hijo)
            self.salida.append(f'{fin}:')

        elif tipo == 'break':
            # El break no lleva nombre de etiqueta. Mira la pila: el ciclo
            # en el que estamos parados es el último que se abrió y todavía
            # no se ha cerrado.
            destino = self.ciclos[-1]['fin']
            self.salida.append(f'    b {destino}      // break')


print("--- Intento 2: un contador, y una pila de ciclos abiertos ---")
g = Generador()
g.generar(PROGRAMA)
for linea in g.salida:
    print("   ", linea)

print("""
Fíjense en los dos `break`:

  * El de la condición B está en el ciclo de AFUERA y salta a su fin
    (.Lwhile_fin_2).
  * El de la condición D está en el ciclo de ADENTRO y salta al fin de
    ese (.Lwhile_fin_5).

El nodo `break` es idéntico en los dos casos. Lo que cambia es qué había
en la pila de ciclos cuando el generador llegó a él.

Para pensar: si el lenguaje permite `break etiqueta` (salir de un ciclo
que no es el más interno), ¿qué tendría que guardar cada elemento de la
pila además de `inicio` y `fin`?
""")
