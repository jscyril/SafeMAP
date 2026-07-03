#include <stddef.h>
#include <stdio.h>

int read_required(const int *value) {
    if (value == NULL) return -1;
    return *value;
}

int read_or_zero(const int *value) {
    if (!value) return 0;
    return *value;
}

int is_enabled(int flag) {
    return flag != 0;
}

int main(void) {
    int value = 9;
    printf("%d %d %d\n", read_required(&value), read_or_zero(NULL), is_enabled(1));
    return 0;
}
