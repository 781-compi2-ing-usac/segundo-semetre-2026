@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    %x_ptr = alloca i32
    store i32 10, ptr %x_ptr
    %a_ptr = alloca i1
    %t1 = load i32, ptr %x_ptr
    %t2 = icmp slt i32 %t1, 15
    br i1 %t2, label %L1, label %L2
L1:
    store i1 1, ptr %a_ptr
    br label %L3
L2:
    store i1 0, ptr %a_ptr
    br label %L3
L3:
    %b_ptr = alloca i1
    %t3 = load i32, ptr %x_ptr
    %t4 = icmp sgt i32 %t3, 5
    br i1 %t4, label %L4, label %L5
L4:
    %t5 = load i32, ptr %x_ptr
    %t6 = icmp slt i32 %t5, 20
    br i1 %t6, label %L6, label %L7
L6:
    store i1 1, ptr %b_ptr
    br label %L8
L5:
    br label %L7
L7:
    store i1 0, ptr %b_ptr
    br label %L8
L8:
    %t7 = load i1, ptr %a_ptr
    %t8 = zext i1 %t7 to i32
    call i32 (ptr, ...) @printf(ptr @.fmt_bool, i32 %t8)
    %t9 = load i1, ptr %b_ptr
    %t10 = zext i1 %t9 to i32
    call i32 (ptr, ...) @printf(ptr @.fmt_bool, i32 %t10)
    ret i32 0
}