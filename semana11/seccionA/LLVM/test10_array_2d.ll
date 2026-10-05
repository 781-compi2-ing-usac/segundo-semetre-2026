@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    ; declare int matrix
    %_arr_139921171903824_ptr = alloca i32
    store i32 1, ptr %_arr_139921171903824_ptr
    %_arr_139921168927568_ptr = alloca i32
    store i32 2, ptr %_arr_139921168927568_ptr
    %_arr_139921171902352_ptr = alloca i32
    store i32 3, ptr %_arr_139921171902352_ptr
    %_arr_139921168927696_ptr = alloca i32
    store i32 4, ptr %_arr_139921168927696_ptr
    %_arr_139921167912848_ptr = alloca i32
    store i32 5, ptr %_arr_139921167912848_ptr
    %_arr_139921168928144_ptr = alloca i32
    store i32 6, ptr %_arr_139921168928144_ptr
    ret i32 0
}