; hello.ll

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    ; Reservar espacio para 7 bytes:
    ; H e l l o \n \0
    %str = alloca [7 x i8]

    ; -------------------------
    ; str[0] = 'H'
    ; -------------------------
    %p0 = getelementptr [7 x i8], ptr %str, i32 0, i32 0
    store i8 72, ptr %p0

    ; -------------------------
    ; str[1] = 'e'
    ; -------------------------
    %p1 = getelementptr [7 x i8], ptr %str, i32 0, i32 1
    store i8 101, ptr %p1

    ; -------------------------
    ; str[2] = 'l'
    ; -------------------------
    %p2 = getelementptr [7 x i8], ptr %str, i32 0, i32 2
    store i8 108, ptr %p2

    ; -------------------------
    ; str[3] = 'l'
    ; -------------------------
    %p3 = getelementptr [7 x i8], ptr %str, i32 0, i32 3
    store i8 108, ptr %p3

    ; -------------------------
    ; str[4] = 'o'
    ; -------------------------
    %p4 = getelementptr [7 x i8], ptr %str, i32 0, i32 4
    store i8 111, ptr %p4

    ; -------------------------
    ; str[5] = '\n'
    ; ASCII: 10
    ; -------------------------
    %p5 = getelementptr [7 x i8], ptr %str, i32 0, i32 5
    store i8 10, ptr %p5

    ; -------------------------
    ; str[6] = '\0'
    ; Terminador de la string
    ; -------------------------
    %p6 = getelementptr [7 x i8], ptr %str, i32 0, i32 6
    store i8 0, ptr %p6

    ; Pasar a printf el puntero
    ; al primer carácter.
    call i32 (ptr, ...) @printf(ptr %p0)

    ret i32 0
}