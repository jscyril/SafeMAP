#include <stdio.h>

int is_at_most(int value, int threshold) {
    return value <= threshold;
}

int main(void) {
    printf("%d %d\n", is_at_most(3, 7), is_at_most(8, 4));
    return 0;
}
