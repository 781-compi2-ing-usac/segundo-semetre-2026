@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    %x_ptr = alloca i32
    store i32 10, ptr %x_ptr
    %t1 = load i32, ptr %x_ptr
    %t2 = icmp slt i32 %t1, 15
    br i1 %t2, label %L1, label %L2
L1:
    %t3 = load i32, ptr %x_ptr
    call i32 (ptr, ...) @printf(ptr @.fmt_int, i32 %t3)
    br label %L3
L2:
    br label %L3
L3:
    ret i32 0
}