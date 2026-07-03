#include <stdio.h>

int is_nonzero(int value) {
    return value != 0;
}

int main(void) {
    printf("%d %d\n", is_nonzero(8), is_nonzero(0));
    return 0;
}
