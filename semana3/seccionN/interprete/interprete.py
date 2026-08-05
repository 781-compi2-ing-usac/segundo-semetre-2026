from .visitante import *
from .expresiones import * 

class Interprete(Visitor):
    
    tablaSimbolos = {}

    def visit_expresion_binaria(self, binaria):
        if (binaria.operador == "+"):
            val1 = binaria.exp1.accept(self)
            val2 = binaria.exp2.accept(self)
            val_tipo = 'int'
            if val1.tipo == 'float' or val2.tipo == 'float':
                val_tipo = 'float'
            print("suma", val1, val2)
            return ExpresionValor(val1.val + val2.val, val_tipo)
        elif (binaria.operador == "-"):
            val1 = binaria.exp1.accept(self)
            val2 = binaria.exp2.accept(self)
            val_tipo = 'int'
            if (val1.tipo == 'float' or val2.tipo == 'float'):
                val_tipo = 'float'
            print("suma", val1, val2)
            return ExpresionValor(val1.val - val2.val, val_tipo)
        elif (binaria.operador == "*"):
            val1 = binaria.exp1.accept(self)
            val2 = binaria.exp2.accept(self)
            print("multiplicacion", val1.val, val2.val,val1.tipo, val2.tipo )
            val_tipo = 'int'
            if val1.tipo == 'float' or val2.tipo == 'float':
                val_tipo = 'float'
            print("suma", val1, val2)
            return ExpresionValor(val1.val * val2.val, val_tipo)


    
    def visit_expresion_valor(self, valor):
        print("valor final", valor.val)
        return ExpresionValor(valor.val, valor.tipo)


    def visit_asignacion(self, asignacion):
        valor_resuelto = asignacion.exp.accept(self)
        if asignacion.tipo == valor_resuelto.tipo:
            self.tablaSimbolos[asignacion.identificador] = valor_resuelto
        else:
            print('ERROR DE TIPO',asignacion.tipo, valor_resuelto.tipo)
        print(self.tablaSimbolos)
        
        return self.tablaSimbolos