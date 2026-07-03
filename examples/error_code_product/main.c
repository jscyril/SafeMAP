#include <stdio.h>

int multiply_checked(int a, int b, int *out) {
    if (b == 0) return -2;
    *out = a * b;
    return 0;
}

int main(void) {
    int out = 0;
    int status = multiply_checked(6, 7, &out);
    printf("%d %d\n", status, out);
    return 0;
}
