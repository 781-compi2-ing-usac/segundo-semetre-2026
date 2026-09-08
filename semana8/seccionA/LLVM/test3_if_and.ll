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
    %t2 = icmp slt i32 %t1, 15
    br i1 %t2, label %L1, label %L2
L1:
    %t3 = load i32, ptr %y_ptr
    %t4 = icmp sgt i32 %t3, 3
    br i1 %t4, label %L3, label %L4
L3:
    %t5 = load i32, ptr %x_ptr
    %t6 = load i32, ptr %y_ptr
    %t7 = add i32 %t5, %t6
    call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 %t7)
    br label %L5
L2:
    br label %L4
L4:
    br label %L5
L5:
    ret i32 0
}