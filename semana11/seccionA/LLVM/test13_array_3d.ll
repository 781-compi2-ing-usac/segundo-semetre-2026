@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    ; declare int cube
    %_arr_139994816395152_ptr = alloca i32
    store i32 1, ptr %_arr_139994816395152_ptr
    %_arr_139994815417488_ptr = alloca i32
    store i32 2, ptr %_arr_139994815417488_ptr
    %_arr_139994815417552_ptr = alloca i32
    store i32 3, ptr %_arr_139994815417552_ptr
    %_arr_139994821381264_ptr = alloca i32
    store i32 4, ptr %_arr_139994821381264_ptr
    %_arr_139994815418000_ptr = alloca i32
    store i32 5, ptr %_arr_139994815418000_ptr
    %_arr_139994815416720_ptr = alloca i32
    store i32 6, ptr %_arr_139994815416720_ptr
    %_arr_139994814407056_ptr = alloca i32
    store i32 7, ptr %_arr_139994814407056_ptr
    %_arr_139994814405904_ptr = alloca i32
    store i32 8, ptr %_arr_139994814405904_ptr
    ret i32 0
}