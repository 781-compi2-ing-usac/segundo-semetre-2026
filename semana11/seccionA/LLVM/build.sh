#!/bin/bash

set -e

if [ $# -ne 1 ]; then
    echo "Uso: $0 <archivo.ll>"
    exit 1
fi

INPUT="$1"
NAME=$(basename "$INPUT" .ll)

mkdir -p build

echo "[1/4] LLVM IR → ARM64 Assembly"
llc -mtriple=aarch64-linux-gnu -O0 "$INPUT" -o "build/$NAME.asm"

echo "[2/4] ARM64 Assembly → Object"
aarch64-linux-gnu-as -g -o "build/$NAME.o" "build/$NAME.asm"

echo "[3/4] Object → ARM64 Executable"
aarch64-linux-gnu-gcc -o "build/$NAME" "build/$NAME.o"

echo "[4/4] Ejecutando con QEMU"
qemu-aarch64 -L /usr/aarch64-linux-gnu "build/$NAME"