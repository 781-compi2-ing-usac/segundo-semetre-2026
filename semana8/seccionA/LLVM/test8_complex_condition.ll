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
    %t2 = icmp sgt i32 %t1, 5
    br i1 %t2, label %L1, label %L2
L1:
    %t3 = load i32, ptr %y_ptr
    %t4 = icmp slt i32 %t3, 10
    br i1 %t4, label %L3, label %L4
L2:
    br label %L4
L4:
    %t5 = load i32, ptr %x_ptr
    %t6 = icmp eq i32 %t5, 10
    br i1 %t6, label %L5, label %L6
L3:
    br label %L5
L5:
    %t7 = load i32, ptr %x_ptr
    %t8 = load i32, ptr %y_ptr
    %t9 = add i32 %t7, %t8
    call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 %t9)
    br label %L7
L6:
    br label %L7
L7:
    ret i32 0
}