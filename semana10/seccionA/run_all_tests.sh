#!/bin/bash
# Script para compilar y ejecutar todos los tests

set -e

echo "=========================================="
echo "Compilando y ejecutando tests LLVM IR"
echo "=========================================="

cd LLVM

for test in test1_arithmetic test2_if_simple test3_if_and test4_if_or test5_while_simple test6_while_and test7_bool_materialization test8_complex_condition; do
    echo ""
    echo "--- $test ---"
    if ./build.sh "${test}.ll"; then
        echo "✅ $test LLVM OK"
    else
        echo "❌ $test LLVM FAILED"
    fi
done

cd ..

echo ""
echo "=========================================="
echo "Compilando y ejecutando tests ARM64"
echo "=========================================="

cd ARM

for test in test1_arithmetic test2_if_simple test3_if_and test4_if_or test5_while_simple test6_while_and test7_bool_materialization test8_complex_condition; do
    echo ""
    echo "--- $test ---"
    if ./build.sh "${test}.asm"; then
        echo "✅ $test ARM OK"
    else
        echo "❌ $test ARM FAILED"
    fi
done

cd ..

echo ""
echo "=========================================="
echo "Todos los tests completados"
echo "=========================================="
