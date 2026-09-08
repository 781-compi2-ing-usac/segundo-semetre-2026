"""
MiniPascal v6 — Ensamblar, enlazar y ejecutar.

Este archivo es el cuarto componente de la Figura 1 del enunciado: lo que
pasa DESPUÉS de que el compilador escribió el `.s`.

    salida.s  --[ensamblar+enlazar]-->  salida  --[QEMU]-->  texto en pantalla

Son dos programas externos, y ninguno de los dos es Python:

  * `aarch64-linux-gnu-gcc` — el ensamblador y enlazador cruzados. "Cruzado"
    significa que corre en su máquina x86_64 pero produce código para ARM64.
    Lo usamos en vez del `as`+`ld` pelados porque enlaza con la biblioteca
    de C, que es de donde sale `printf`.

  * `qemu-aarch64` — ejecuta un binario ARM64 sobre un procesador que no es
    ARM64, traduciendo las instrucciones al vuelo. Esto es QEMU en modo
    USER: emula un solo programa, no una máquina completa con su sistema
    operativo. Por eso arranca instantáneo.

Si tienen una Mac con chip M1/M2/M3, su procesador YA es ARM64 y no
necesitan QEMU para nada — pueden correr el binario directo. El README
explica las dos rutas.


Por qué `-static`
-----------------
Sin `-static`, el binario sale enlazado dinámicamente y al ejecutarlo QEMU
necesita encontrar las bibliotecas de ARM64 en tiempo de ejecución, lo que
obliga a andar pasándole `-L /usr/aarch64-linux-gnu`. Con `-static`, todo
lo que el programa necesita —printf incluido— queda adentro del ejecutable.
Es un archivo más grande y no nos importa.
"""

import os
import shutil
import subprocess


COMPILADOR = 'aarch64-linux-gnu-gcc'
EMULADOR = 'qemu-aarch64'

FALTA_TOOLCHAIN = """
No encontré: {faltantes}

En Ubuntu / Debian / WSL:
    sudo apt install binutils-aarch64-linux-gnu gcc-aarch64-linux-gnu qemu-user

Ojo: el paquete es `qemu-user`, NO `qemu-user-static` (ese ya no existe en
las versiones recientes de Ubuntu y es el error más común al instalar).

En una Mac con chip M1/M2/M3 ya tienen ARM64 nativo: usen `clang` en vez de
`aarch64-linux-gnu-gcc`, y corran el binario directo, sin QEMU.

El README de esta semana tiene las instrucciones completas, incluyendo una
ruta con Docker que funciona en cualquier sistema.
""".strip()


def herramientas_faltantes():
    """Devuelve la lista de programas del toolchain que no están instalados."""
    return [nombre for nombre in (COMPILADOR, EMULADOR) if shutil.which(nombre) is None]


def ensamblar_y_ejecutar(ruta_asm, ruta_ejecutable=None):
    """Ensambla, enlaza y ejecuta. Devuelve (salida_texto, codigo_retorno).

    Si algo falla, devuelve el mensaje de error como salida — nunca revienta,
    porque un error del ensamblador es información útil, no una catástrofe.
    """
    faltantes = herramientas_faltantes()
    if faltantes:
        return FALTA_TOOLCHAIN.format(faltantes=', '.join(faltantes)), 1

    if ruta_ejecutable is None:
        ruta_ejecutable = os.path.splitext(ruta_asm)[0]

    # --- Ensamblar y enlazar ---------------------------------------------
    compilacion = subprocess.run(
        [COMPILADOR, '-static', ruta_asm, '-o', ruta_ejecutable],
        capture_output=True, text=True,
    )
    if compilacion.returncode != 0:
        # El ensamblador se queja con línea y columna del archivo .s. Si
        # llegan aquí, el error está en el código que GENERARON, no en el
        # programa MiniPascal: abran salida.s y vayan a esa línea.
        return (f"El ensamblador rechazó el código generado:\n\n"
                f"{compilacion.stderr}"), compilacion.returncode

    # --- Ejecutar con QEMU ------------------------------------------------
    ejecucion = subprocess.run(
        [EMULADOR, ruta_ejecutable],
        capture_output=True, text=True,
    )
    return ejecucion.stdout + ejecucion.stderr, ejecucion.returncode
