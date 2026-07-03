#include <stdio.h>

void decrement(int *value) {
    *value -= 2;
}

int main(void) {
    int value = 7;
    decrement(&value);
    printf("%d\n", value);
    return 0;
}
