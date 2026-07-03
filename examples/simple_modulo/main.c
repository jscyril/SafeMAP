#include <stdio.h>

int remainder_value(int a, int b) {
    return a % b;
}

int main(void) {
    printf("%d\n", remainder_value(20, 6));
    return 0;
}
