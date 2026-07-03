#include <stdio.h>

void sum_diff_pair(int a, int b, int *sum_out, int *diff_out) {
    *sum_out = a + b;
    *diff_out = a - b;
}

int main(void) {
    int sum = 0;
    int diff = 0;
    sum_diff_pair(9, 4, &sum, &diff);
    printf("%d %d\n", sum, diff);
    return 0;
}
