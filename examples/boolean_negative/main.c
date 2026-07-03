#include <stdio.h>

int is_negative(int value) {
    return value < 0;
}

int main(void) {
    printf("%d %d\n", is_negative(-3), is_negative(4));
    return 0;
}
