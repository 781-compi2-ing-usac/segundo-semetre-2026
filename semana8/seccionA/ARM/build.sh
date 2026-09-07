#!/bin/bash

set -e

if [ $# -ne 1 ]; then
    echo "Uso: $0 <archivo.asm>"
    exit 1
fi

INPUT="$1"

NAME=$(basename "$INPUT" .asm)

mkdir -p build

echo "[1/3] ARM64 Assembly → Object"

aarch64-linux-gnu-as -g -o "build/$NAME.o" "$INPUT"

echo "[2/3] Object → ARM64 Executable"

aarch64-linux-gnu-ld -o "build/$NAME" "build/$NAME.o"

echo "[3/3] Ejecutando con QEMU"

qemu-aarch64 "build/$NAME"