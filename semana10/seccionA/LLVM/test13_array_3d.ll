@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    %_arr_140549655689168_ptr = alloca i32
    store i32 1, ptr %_arr_140549655689168_ptr
    %_arr_140549655690960_ptr = alloca i32
    store i32 2, ptr %_arr_140549655690960_ptr
    %_arr_140549653672144_ptr = alloca i32
    store i32 3, ptr %_arr_140549653672144_ptr
    %_arr_140549653667984_ptr = alloca i32
    store i32 4, ptr %_arr_140549653667984_ptr
    %_arr_140549653671504_ptr = alloca i32
    store i32 5, ptr %_arr_140549653671504_ptr
    %_arr_140549653669264_ptr = alloca i32
    store i32 6, ptr %_arr_140549653669264_ptr
    %_arr_140549653671312_ptr = alloca i32
    store i32 7, ptr %_arr_140549653671312_ptr
    %_arr_140549653670736_ptr = alloca i32
    store i32 8, ptr %_arr_140549653670736_ptr
    ret i32 0
}