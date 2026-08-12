

class Registro():
    def __init__(self, identificador, tipo, valor):
        self.identificador = identficador
        self.tipo = tipo
        self.valor = valor


class TablaSimbolo():

    def __init__(self, padre  = None):
        self.padre = padre #Deberia ser  un objeto TablaSimbolo
        self.tabla = {}

    def insertar(self, llave, valor, tipo):
        #Aqui hacemos la validacion de tipo
        self.tabla[llave] = valor

    def buscar(self, llave):
        
        if not (llave in self.tabla):
            if self.padre == None:
                return None
            #print('tablapadre', self.padre.tabla)
            busquedaExtendida = self.padre.buscar(llave)
            if busquedaExtendida == None:
                return None
            return busquedaExtendida
        #print('tabla actual', self.tabla)
        
        return self.tabla[llave]

    def actualizar(self, llave, valor):
        # funcion necesaria para las variables tipo mut
        pass