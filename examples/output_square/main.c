#include <stdio.h>

void square_value(int value, int *out) {
    *out = value * value;
}

int main(void) {
    int out = 0;
    square_value(7, &out);
    printf("%d\n", out);
    return 0;
}
