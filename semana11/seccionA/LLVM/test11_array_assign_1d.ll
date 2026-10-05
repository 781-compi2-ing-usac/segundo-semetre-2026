@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    ; declare int arr
    %_arr_139921167330768_ptr = alloca i32
    store i32 1, ptr %_arr_139921167330768_ptr
    %_arr_139921168928144_ptr = alloca i32
    store i32 2, ptr %_arr_139921168928144_ptr
    %_arr_139921168927824_ptr = alloca i32
    store i32 3, ptr %_arr_139921168927824_ptr
    %_arr_139921169529488_ptr = alloca i32
    store i32 4, ptr %_arr_139921169529488_ptr
    %_arr_139921171903824_ptr = alloca i32
    store i32 5, ptr %_arr_139921171903824_ptr
    ; assign arr
    ; assign arr
    ; assign arr
    ret i32 0
}