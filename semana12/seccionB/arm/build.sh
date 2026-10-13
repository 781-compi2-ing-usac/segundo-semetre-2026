#!/usr/bin/env bash
#
# build.sh — ensamblar, enlazar y ejecutar un archivo .s de ARM64.
#
#   ./build.sh 01_hola.s
#   ./build.sh 02_aritmetica.s
#
# Detecta solo si el archivo necesita la biblioteca de C (porque usa
# printf) o si le habla al kernel directamente, y elige las herramientas
# que correspondan. Son los dos modos que vemos hoy:
#
#   _start + svc      ->  as + ld           sin libc, syscalls puras
#   main   + printf   ->  gcc -static       con libc
#
set -euo pipefail

ARCHIVO="${1:-}"
if [[ -z "$ARCHIVO" ]]; then
    echo "Uso: ./build.sh <archivo.s>"
    echo "Disponibles:"
    ls -1 ./*.s 2>/dev/null | sed 's|^\./|    |'
    exit 1
fi

if [[ ! -f "$ARCHIVO" ]]; then
    echo "No existe: $ARCHIVO"
    exit 1
fi

BASE="${ARCHIVO%.s}"

# --- ¿Está el toolchain? ---------------------------------------------------
faltan=()
for herramienta in aarch64-linux-gnu-as aarch64-linux-gnu-ld aarch64-linux-gnu-gcc qemu-aarch64; do
    command -v "$herramienta" >/dev/null 2>&1 || faltan+=("$herramienta")
done

if (( ${#faltan[@]} > 0 )); then
    cat <<AYUDA
No encontré: ${faltan[*]}

En Ubuntu / Debian / WSL:

    sudo apt install binutils-aarch64-linux-gnu gcc-aarch64-linux-gnu qemu-user

OJO: el paquete es 'qemu-user', NO 'qemu-user-static'. Ese segundo ya no
existe en las versiones recientes de Ubuntu y es el error más común.

En una Mac con chip M1/M2/M3 su procesador YA es ARM64: no necesitan QEMU.
Usen 'clang' en lugar del compilador cruzado y corran el binario directo.

El README de esta semana tiene las tres rutas completas, incluida una con
Docker que sirve en cualquier sistema.
AYUDA
    exit 1
fi

# --- Ensamblar y enlazar ---------------------------------------------------
if grep -qE '^\s*\.global\s+main\b' "$ARCHIVO"; then
    echo ">>> $ARCHIVO usa printf: enlazando con la biblioteca de C"
    echo "    aarch64-linux-gnu-gcc -static $ARCHIVO -o $BASE"
    aarch64-linux-gnu-gcc -static "$ARCHIVO" -o "$BASE"
else
    echo ">>> $ARCHIVO habla con el kernel directo: sin biblioteca de C"
    echo "    aarch64-linux-gnu-as $ARCHIVO -o $BASE.o"
    aarch64-linux-gnu-as "$ARCHIVO" -o "$BASE.o"
    echo "    aarch64-linux-gnu-ld $BASE.o -o $BASE"
    aarch64-linux-gnu-ld "$BASE.o" -o "$BASE"
fi

# --- Ejecutar --------------------------------------------------------------
echo ""
echo ">>> qemu-aarch64 ./$BASE"
echo "--- salida ------------------------------------------------------------"
set +e
qemu-aarch64 "./$BASE"
codigo=$?
set -e
echo "-----------------------------------------------------------------------"
echo ">>> código de salida: $codigo"
