#include <stdio.h>

void square_and_double(int value, int *square_out, int *double_out) {
    *square_out = value * value;
    *double_out = value * 2;
}

int divide_checked(int value, int divisor, int *out) {
    if (divisor == 0) return -1;
    *out = value / divisor;
    return 0;
}

void decrement_in_place(int *value) {
    *value -= 2;
}

int main(void) {
    int square = 0;
    int doubled = 0;
    int divided = 0;
    int value = 9;
    square_and_double(value, &square, &doubled);
    decrement_in_place(&value);
    printf("%d %d %d %d\n", square, doubled, divide_checked(20, 5, &divided), divided);
    return 0;
}
