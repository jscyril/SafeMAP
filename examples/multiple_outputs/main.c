#include <stdio.h>

void divmod_pair(int value, int divisor, int *quotient, int *remainder) {
    *quotient = value / divisor;
    *remainder = value % divisor;
}

int main(void) {
    int quotient = 0;
    int remainder = 0;
    divmod_pair(17, 5, &quotient, &remainder);
    printf("%d %d\n", quotient, remainder);
    return 0;
}
