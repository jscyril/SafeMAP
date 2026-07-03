#include <stdio.h>

int array_max(const int *arr, int len) {
    int max = arr[0];
    for (int i = 1; i < len; i++) {
        if (arr[i] > max) max = arr[i];
    }
    return max;
}

int main(void) {
    int values[] = {3, 9, 2, 5};
    printf("%d\n", array_max(values, 4));
    return 0;
}
