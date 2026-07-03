#include <stdio.h>

int read_union_as_int(float value) {
    union bits {
        int i;
        float f;
    } data;
    data.f = value;
    return data.i;
}

int main(void) {
    printf("%d\n", read_union_as_int(1.0f));
    return 0;
}
