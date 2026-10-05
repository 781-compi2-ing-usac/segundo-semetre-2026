@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    ; declare int matrix
    %_arr_139994821381264_ptr = alloca i32
    store i32 1, ptr %_arr_139994821381264_ptr
    %_arr_139994815417616_ptr = alloca i32
    store i32 2, ptr %_arr_139994815417616_ptr
    %_arr_139994815418000_ptr = alloca i32
    store i32 3, ptr %_arr_139994815418000_ptr
    %_arr_139994815417680_ptr = alloca i32
    store i32 4, ptr %_arr_139994815417680_ptr
    %_arr_139994814406352_ptr = alloca i32
    store i32 5, ptr %_arr_139994814406352_ptr
    %_arr_139994821701648_ptr = alloca i32
    store i32 6, ptr %_arr_139994821701648_ptr
    ; assign matrix
    ; assign matrix
    ; assign matrix
    ret i32 0
}