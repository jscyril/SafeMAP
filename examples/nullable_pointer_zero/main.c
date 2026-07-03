#include <stddef.h>
#include <stdio.h>

int read_or_zero(const int *p) {
    if (!p) return 0;
    return *p;
}

int main(void) {
    int value = 11;
    printf("%d %d\n", read_or_zero(&value), read_or_zero(NULL));
    return 0;
}
