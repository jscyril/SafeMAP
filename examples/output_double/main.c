#include <stdio.h>

void double_value(int value, int *out) {
    *out = value * 2;
}

int main(void) {
    int out = 0;
    double_value(7, &out);
    printf("%d\n", out);
    return 0;
}
