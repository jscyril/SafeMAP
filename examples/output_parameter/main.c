#include <stdio.h>

int get_max(const int *arr, int len, int *out) {
    if (len <= 0) return -1;
    int max = arr[0];
    for (int i = 1; i < len; i++) if (arr[i] > max) max = arr[i];
    *out = max;
    return 0;
}

int main(void) {
    int values[] = {3, 8, 2};
    int out = 0;
    int status = get_max(values, 3, &out);
    printf("%d %d\n", status, out);
    return 0;
}

