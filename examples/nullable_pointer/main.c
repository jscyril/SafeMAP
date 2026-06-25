#include <stddef.h>
#include <stdio.h>

int read_value(const int *p) {
    if (p == NULL) return -1;
    return *p;
}

int main(void) {
    int value = 7;
    printf("%d %d\n", read_value(&value), read_value(NULL));
    return 0;
}

