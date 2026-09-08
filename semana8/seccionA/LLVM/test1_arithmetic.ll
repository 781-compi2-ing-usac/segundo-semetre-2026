@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    %x_ptr = alloca i32
    store i32 10, ptr %x_ptr
    %y_ptr = alloca i32
    store i32 5, ptr %y_ptr
    %t1 = load i32, ptr %x_ptr
    %t2 = load i32, ptr %y_ptr
    %t3 = add i32 %t1, %t2
    call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 %t3)
    %t4 = load i32, ptr %x_ptr
    %t5 = load i32, ptr %y_ptr
    %t6 = sub i32 %t4, %t5
    call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 %t6)
    %t7 = load i32, ptr %x_ptr
    %t8 = load i32, ptr %y_ptr
    %t9 = mul i32 %t7, %t8
    call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 %t9)
    ret i32 0
}