#include <stdio.h>

int sum_array(const int *arr, int len) {
    int sum = 0;
    for (int i = 0; i < len; i++) sum += arr[i];
    return sum;
}

int main(void) {
    int values[] = {1, 2, 3, 4};
    printf("%d\n", sum_array(values, 4));
    return 0;
}

