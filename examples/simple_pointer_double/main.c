#include <stdio.h>

void double_in_place(int *value) {
    *value *= 2;
}

int main(void) {
    int value = 7;
    double_in_place(&value);
    printf("%d\n", value);
    return 0;
}
