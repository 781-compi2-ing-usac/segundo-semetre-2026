mkdir -p build
aarch64-linux-gnu-as -g -o build/main.o object/main.asm
aarch64-linux-gnu-ld -o build/main build/main.o
qemu-aarch64 build/main                 # ejecución
# qemu-aarch64 -g 1234 build/main         # depuración (stub GDB)