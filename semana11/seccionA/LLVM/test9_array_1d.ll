@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    ; declare int arr
    %_arr_139921171903824_ptr = alloca i32
    store i32 1, ptr %_arr_139921171903824_ptr
    %_arr_139921169530320_ptr = alloca i32
    store i32 2, ptr %_arr_139921169530320_ptr
    %_arr_139921169897744_ptr = alloca i32
    store i32 3, ptr %_arr_139921169897744_ptr
    %_arr_139921171902352_ptr = alloca i32
    store i32 4, ptr %_arr_139921171902352_ptr
    %_arr_139921169807888_ptr = alloca i32
    store i32 5, ptr %_arr_139921169807888_ptr
    ret i32 0
}