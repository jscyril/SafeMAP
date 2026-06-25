#include <stdio.h>

void increment(int *value) {
    *value += 1;
}

int main(void) {
    int value = 4;
    increment(&value);
    printf("%d\n", value);
    return 0;
}

