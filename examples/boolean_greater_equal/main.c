#include <stdio.h>

int is_at_least(int value, int threshold) {
    return value >= threshold;
}

int main(void) {
    printf("%d %d\n", is_at_least(8, 4), is_at_least(3, 7));
    return 0;
}
