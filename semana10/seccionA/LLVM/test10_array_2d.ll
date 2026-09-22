@.fmt_int = private unnamed_addr constant [4 x i8] c"%d\0A\00"
@.fmt_float = private unnamed_addr constant [4 x i8] c"%f\0A\00"
@.fmt_bool = private unnamed_addr constant [4 x i8] c"%d\0A\00"

declare i32 @printf(ptr, ...)

define i32 @main() {
entry:
    %_arr_140549656062160_ptr = alloca i32
    store i32 1, ptr %_arr_140549656062160_ptr
    %_arr_140549656057616_ptr = alloca i32
    store i32 2, ptr %_arr_140549656057616_ptr
    %_arr_140549655967888_ptr = alloca i32
    store i32 3, ptr %_arr_140549655967888_ptr
    %_arr_140549653668304_ptr = alloca i32
    store i32 4, ptr %_arr_140549653668304_ptr
    %_arr_140549653671248_ptr = alloca i32
    store i32 5, ptr %_arr_140549653671248_ptr
    %_arr_140549653669328_ptr = alloca i32
    store i32 6, ptr %_arr_140549653669328_ptr
    ret i32 0
}