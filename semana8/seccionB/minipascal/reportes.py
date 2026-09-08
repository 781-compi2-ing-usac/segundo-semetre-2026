"""
MiniPascal v5 — Reportes en HTML.

No hay nada nuevo de PLY o del patrón Intérprete aquí — esta es la parte
final: tomar lo que el intérprete YA sabe (`ListaErrores`, `TablaSimbolos`,
el texto DOT del AST desde la Sesión 1) y mostrarlo en el formato que pide
el enunciado (sección 3.4), en vez de solo imprimirlo por consola.

Versión condensada a propósito: la sesión de hoy le dio el tiempo real a
structs y slices. Esto es lo mínimo para que ningún reporte quede sin
versión HTML — no tiene estilos, ni pestañas, ni nada de la GUI completa
que pide la sección 3.1.2. Eso lo construyen ustedes.
"""

import html


def reporte_errores_html(errores):
    """Tabla HTML de la sección 3.4.1 del enunciado."""
    if not errores.hay_errores():
        return "<p>Sin errores semánticos.</p>"

    filas = []
    for error in errores.errores:
        filas.append(
            "<tr>"
            f"<td>{html.escape(error['tipo'])}</td>"
            f"<td>{error['linea']}</td>"
            f"<td>{error['columna']}</td>"
            # `html.escape` es obligatorio aquí: la descripción de un
            # error puede citar literalmente el código del usuario
            # (nombres de variable, valores...), y ese texto podría traer
            # `<`, `>` o `&` — sin escaparlo, el HTML generado se rompe o,
            # peor, alguien podría inyectar sus propias etiquetas.
            f"<td>{html.escape(error['descripcion'])}</td>"
            "</tr>"
        )

    return (
        '<table border="1" cellpadding="4">'
        "<tr><th>Tipo</th><th>Línea</th><th>Columna</th><th>Descripción</th></tr>"
        + "".join(filas)
        + "</table>"
    )


def reporte_simbolos_html(tabla):
    """Tabla HTML de la sección 3.4.2 del enunciado."""
    if not tabla.filas:
        return "<p>(tabla de símbolos vacía)</p>"

    filas = []
    for numero, fila in enumerate(tabla.filas, start=1):
        filas.append(
            "<tr>"
            f"<td>{numero}</td>"
            f"<td>{html.escape(fila['nombre'])}</td>"
            f"<td>{html.escape(fila['categoria'])}</td>"
            f"<td>{html.escape(str(fila['tipo']))}</td>"
            f"<td>{html.escape(fila['ambito'])}</td>"
            f"<td>{fila['linea']}</td>"
            f"<td>{html.escape(str(fila['valor']))}</td>"
            "</tr>"
        )

    return (
        '<table border="1" cellpadding="4">'
        "<tr><th>#</th><th>Identificador</th><th>Categoría</th><th>Tipo</th>"
        "<th>Ámbito</th><th>Línea</th><th>Valor</th></tr>"
        + "".join(filas)
        + "</table>"
    )


def reporte_completo_html(errores, tabla, titulo='Reporte MiniPascal'):
    """Junta las dos tablas en una sola página HTML, para verlas en el navegador."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><title>{html.escape(titulo)}</title></head>
<body>
  <h1>{html.escape(titulo)}</h1>

  <h2>Errores</h2>
  {reporte_errores_html(errores)}

  <h2>Tabla de símbolos</h2>
  {reporte_simbolos_html(tabla)}
</body>
</html>
"""


if __name__ == '__main__':
    # Demo rápida, sin PLY: arma una ListaErrores y una TablaSimbolos a
    # mano (las mismas dos clases de la Sesión 2) y genera el HTML.
    from errores import ListaErrores
    from tabla_simbolos import TablaSimbolos

    errores = ListaErrores()
    errores.agregar('Semántico', "La variable 'total' no ha sido declarada.", 3, 15)

    tabla = TablaSimbolos()
    tabla.registrar('contador', 'Variable', 'integer', 'programa', 1, 10)

    salida = 'reporte_demo.html'
    with open(salida, 'w', encoding='utf-8') as archivo:
        archivo.write(reporte_completo_html(errores, tabla, titulo='Demo'))

    print(f"Escrito en: {salida}")
    print("Ábranlo en el navegador para verlo.")

    # -------------------------------------------------------------------
    # Para su proyecto: esto es el 20% que se ve (convertir datos ya
    # calculados a HTML). El 80% real ya lo tienen desde hace semanas:
    # ListaErrores, TablaSimbolos y dot.py. Denle estilos con CSS, tabs,
    # o lo que pida su GUI — la estructura de datos no cambia.
    # -------------------------------------------------------------------
