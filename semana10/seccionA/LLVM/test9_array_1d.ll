@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    %_arr_140549655689168_ptr = alloca i32
    store i32 1, ptr %_arr_140549655689168_ptr
    %_arr_140549655689424_ptr = alloca i32
    store i32 2, ptr %_arr_140549655689424_ptr
    %_arr_140549655967888_ptr = alloca i32
    store i32 3, ptr %_arr_140549655967888_ptr
    %_arr_140549653666960_ptr = alloca i32
    store i32 4, ptr %_arr_140549653666960_ptr
    %_arr_140549653669264_ptr = alloca i32
    store i32 5, ptr %_arr_140549653669264_ptr
    ret i32 0
}