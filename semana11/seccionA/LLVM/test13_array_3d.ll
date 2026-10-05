@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    ; declare int cube
    %_arr_139921169530320_ptr = alloca i32
    store i32 1, ptr %_arr_139921169530320_ptr
    %_arr_139921171903824_ptr = alloca i32
    store i32 2, ptr %_arr_139921171903824_ptr
    %_arr_139921168927632_ptr = alloca i32
    store i32 3, ptr %_arr_139921168927632_ptr
    %_arr_139921167913616_ptr = alloca i32
    store i32 4, ptr %_arr_139921167913616_ptr
    %_arr_139921168927824_ptr = alloca i32
    store i32 5, ptr %_arr_139921168927824_ptr
    %_arr_139921168927184_ptr = alloca i32
    store i32 6, ptr %_arr_139921168927184_ptr
    %_arr_139921167916816_ptr = alloca i32
    store i32 7, ptr %_arr_139921167916816_ptr
    %_arr_139921167915600_ptr = alloca i32
    store i32 8, ptr %_arr_139921167915600_ptr
    ret i32 0
}