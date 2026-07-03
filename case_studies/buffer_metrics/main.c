#include <stdio.h>

int sum_values(const int *arr, int len) {
    int total = 0;
    for (int i = 0; i < len; i++) total += arr[i];
    return total;
}

int max_value(const int *arr, int len) {
    int max = arr[0];
    for (int i = 1; i < len; i++) {
        if (arr[i] > max) max = arr[i];
    }
    return max;
}

void add_offset(int *arr, int len) {
    for (int i = 0; i < len; i++) {
        arr[i] += 2;
    }
}

int main(void) {
    int values[] = {2, 4, 6};
    add_offset(values, 3);
    printf("%d %d\n", sum_values(values, 3), max_value(values, 3));
    return 0;
}
