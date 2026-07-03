#include <stdio.h>

int is_even(int value) {
    return value % 2 == 0;
}

int main(void) {
    printf("%d\n", is_even(8));
    return 0;
}
