#include <stdio.h>

void min_max_pair(int a, int b, int *min_out, int *max_out) {
    *min_out = a < b ? a : b;
    *max_out = a > b ? a : b;
}

int main(void) {
    int min_value = 0;
    int max_value = 0;
    min_max_pair(9, 4, &min_value, &max_value);
    printf("%d %d\n", min_value, max_value);
    return 0;
}
