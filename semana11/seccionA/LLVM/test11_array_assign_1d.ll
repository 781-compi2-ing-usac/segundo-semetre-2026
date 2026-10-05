@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    ; declare int arr
    %_arr_139994816666576_ptr = alloca i32
    store i32 1, ptr %_arr_139994816666576_ptr
    %_arr_139994815417872_ptr = alloca i32
    store i32 2, ptr %_arr_139994815417872_ptr
    %_arr_139994815418064_ptr = alloca i32
    store i32 3, ptr %_arr_139994815418064_ptr
    %_arr_139994816731216_ptr = alloca i32
    store i32 4, ptr %_arr_139994816731216_ptr
    %_arr_139994821381264_ptr = alloca i32
    store i32 5, ptr %_arr_139994821381264_ptr
    ; assign arr
    ; assign arr
    ; assign arr
    ret i32 0
}