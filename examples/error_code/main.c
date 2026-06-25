#include <stdio.h>

int divide(int a, int b, int *out) {
    if (b == 0) return -1;
    *out = a / b;
    return 0;
}

int main(void) {
    int out = 0;
    int status = divide(12, 3, &out);
    printf("%d %d\n", status, out);
    return 0;
}

