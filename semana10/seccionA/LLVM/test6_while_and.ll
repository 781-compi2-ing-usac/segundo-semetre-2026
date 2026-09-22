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
    br label %L1
L1:
    %t1 = load i32, ptr %x_ptr
    %t2 = icmp sgt i32 %t1, 0
    br i1 %t2, label %L2, label %L3
L2:
    %t3 = load i32, ptr %y_ptr
    %t4 = icmp sgt i32 %t3, 0
    br i1 %t4, label %L4, label %L5
L4:
    %t5 = load i32, ptr %x_ptr
    call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 %t5)
    %t6 = load i32, ptr %x_ptr
    %t7 = sub i32 %t6, 1
    store i32 %t7, ptr %x_ptr
    %t8 = load i32, ptr %y_ptr
    %t9 = sub i32 %t8, 1
    store i32 %t9, ptr %y_ptr
    br label %L1
L3:
    br label %L5
L5:
    ret i32 0
}